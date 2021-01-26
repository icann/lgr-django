# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render

from lgr.tools.idn_review.review import review_lgr
from lgr_advanced.api import session_list_lgr, session_select_lgr
from lgr_idn_table_review.forms import LGRIdnTableReviewSelector


def lgr_idn_table_review(request, lgr_id):
    form = LGRIdnTableReviewSelector(request.POST or None,
                                     session_lgrs=[lgr['name'] for lgr in session_list_lgr(request) if
                                                   not lgr['is_set']],
                                     lgr_id=lgr_id)

    if form.is_valid():
        idn_table_id, ref_lgr_id = form.cleaned_data['idn_table'], form.cleaned_data['ref_lgr']
        idn_table_info, ref_lgr_info = (session_select_lgr(request, l) for l in (idn_table_id, ref_lgr_id))
        context = review_lgr(idn_table_info.lgr, ref_lgr_info.lgr)
        return render(request, 'review.html', context=context)

    ctx = {
        'form': form,
        'lgr_id': lgr_id if lgr_id is not None else ''
    }

    return render(request, 'review_form.html', context=ctx)
