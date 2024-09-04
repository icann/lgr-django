#! /bin/env python
# -*- coding: utf-8 -*-
"""
tag - 
"""
import logging
from itertools import islice

from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import TemplateView

from lgr.exceptions import LGRException
from lgr_advanced.lgr_editor.utils import render_cp_or_sequence
from lgr_advanced.lgr_editor.views.mixins import LGRHandlingBaseMixin, LGREditMixin
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_utils.cp import cp_to_slug

logger = logging.getLogger(__name__)

TRUNCATE_AFTER_N_CP_TAGS = 10


class ListTagView(LGRHandlingBaseMixin, TemplateView):
    """
    List/edit tags of an LGR.
    """
    template_name = 'lgr_editor/tags.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        tag_classes = self.lgr.get_tag_classes()

        tags = [{
            'name': tag,
            'nb_cp': len(clz.codepoints),
            'view_more': len(clz.codepoints) > TRUNCATE_AFTER_N_CP_TAGS,
            'codepoints': [{
                'cp_disp': render_cp_or_sequence(c),
                'cp_id': cp_to_slug((c,)),
            } for c in islice(clz.codepoints, TRUNCATE_AFTER_N_CP_TAGS)]
        } for tag, clz in tag_classes.items()]

        ctx.update({
            'tags': tags,
        })

        return ctx


class ListTagJsonView(LGRHandlingBaseMixin, View):
    """
    Return the full list of code points associated with a tag in JSON.
    """

    def get(self, request, *args, **kwargs):
        tag_id = self.kwargs['tag_id']
        tag_classes = self.lgr.get_tag_classes()
        if tag_id not in tag_classes:
            # Error
            return

        clz = tag_classes[tag_id]

        data = []
        cp_list = []
        for c in clz.codepoints:
            cp_slug = cp_to_slug((c,))
            kwargs = {'lgr_pk': self.lgr_pk, 'codepoint_id': cp_slug, 'model': self.lgr_object.model_name}
            cp_view_url = reverse('codepoint_view', kwargs=kwargs)
            obj = {'cp_disp': render_cp_or_sequence(c), 'cp_view': cp_view_url}
            cp_list.append(obj)
            if len(cp_list) == 10:
                data.append(cp_list)
                cp_list = []
        # Do not forget to add the remaining code points, if any
        if cp_list:
            data.append(cp_list)

        response = {'data': data}
        return JsonResponse(response)


class DeleteTagView(LGREditMixin, View):
    """
    Delete a tag from an LGR.
    """

    def post(self, request, *args, **kwargs):
        tag_id = self.kwargs['tag_id']
        logger.debug("Delete tag %s'", tag_id)

        try:
            self.lgr.del_tag(tag_id)
            self.update_lgr()
        except LGRException as ex:
            messages.add_message(request, messages.ERROR, lgr_exception_to_text(ex))
        else:
            messages.add_message(request, messages.INFO,
                                 _("References to tag %(tag)s have been removed from the repertoire. "
                                   "Do not forget to update any WLE that might reference it.") % {'tag': tag_id})

        return redirect('tags', lgr_pk=self.lgr_pk, model=self.lgr_object.model_name)
