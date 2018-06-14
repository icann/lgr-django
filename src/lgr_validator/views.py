# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from django.http import HttpResponse
from django.contrib import messages
from django.conf import settings
from django.shortcuts import render, redirect

from lgr_editor.api import LabelInfo
from lgr_editor.lgr_exceptions import lgr_exception_to_text

from lgr.exceptions import LGRException

from .forms import ValidateLabelForm
from .api import validation_results_to_csv, lgr_set_evaluate_label, evaluate_label

select_lgr = getattr(__import__(settings.LGR_SELECTOR_FUNC.rpartition('.')[0],
                                fromlist=[settings.LGR_SELECTOR_FUNC.rpartition('.')[0]]),
                     settings.LGR_SELECTOR_FUNC.rpartition('.')[2])

get_unidb = getattr(__import__(settings.UNIDB_LOADER_FUNC.rpartition('.')[0],
                               fromlist=[settings.UNIDB_LOADER_FUNC.rpartition('.')[0]]),
                    settings.UNIDB_LOADER_FUNC.rpartition('.')[2])


def evaluate_label_from_info(lgr_info, label_cplist, script_lgr_name,
                             udata, threshold_include_vars=settings.LGR_VALIDATOR_MAX_VARS_DISPLAY_INLINE):
    if lgr_info.is_set:
        script_lgr_info = None
        for set_lgr_info in lgr_info.lgr_set:
            if script_lgr_name == set_lgr_info.name:
                script_lgr_info = set_lgr_info
                break
        if lgr_info.set_labels_info is None:
            set_labels = []
        else:
            set_labels = lgr_info.set_labels_info.labels
        # TODO if script_lgr_info is None
        ctx = lgr_set_evaluate_label(lgr_info.lgr, script_lgr_info.lgr, label_cplist,
                                     set_labels,
                                     threshold_include_vars=threshold_include_vars,
                                     idna_encoder=udata.idna_encode_label)
    else:
        ctx = evaluate_label(lgr_info.lgr, label_cplist,
                             threshold_include_vars=threshold_include_vars,
                             idna_encoder=udata.idna_encode_label)

    return ctx


def validate_label(request, lgr_id, lgr_set_id=None,
                   threshold_include_vars=settings.LGR_VALIDATOR_MAX_VARS_DISPLAY_INLINE,
                   output_func=None, noframe=False):
    lgr_info = select_lgr(request, lgr_id, lgr_set_id)
    udata = get_unidb(lgr_info.lgr.metadata.unicode_version)
    max_label_len = lgr_info.lgr.max_label_length()
    scripts = None
    if lgr_info.is_set:
        scripts = []
        for lgr_set_info in lgr_info.lgr_set:
            try:
                scripts.append((lgr_set_info.name, lgr_set_info.lgr.metadata.languages[0]))
            except (AttributeError, IndexError):
                pass
    form = ValidateLabelForm(request.POST or request.GET or None,
                             files=request.FILES or None,
                             lgr_info=lgr_info,
                             max_label_len=max_label_len,
                             idna_decoder=udata.idna_decode_label,
                             scripts=scripts)
    ctx = {}
    if form.is_bound and form.is_valid():
        label_cplist = form.cleaned_data['label']
        script_lgr_name = form.cleaned_data.get('script', None)
        if lgr_info.is_set:
            set_labels_file = form.cleaned_data['set_labels']
            if set_labels_file is not None:
                if lgr_info.set_labels_info is None or lgr_info.set_labels_info.name != set_labels_file.name:
                    lgr_info.set_labels_info = LabelInfo.from_form(set_labels_file.name,
                                                                   set_labels_file.read())
        try:
            ctx = evaluate_label_from_info(lgr_info, label_cplist, script_lgr_name, udata,
                                           threshold_include_vars=threshold_include_vars)
        except UnicodeError as ex:
            messages.add_message(request, messages.ERROR,
                                 lgr_exception_to_text(ex))
        except LGRException as ex:
            messages.add_message(request, messages.ERROR,
                                 lgr_exception_to_text(ex))
            kwargs = {'lgr_id': lgr_id}
            if lgr_set_id is not None:
                kwargs['lgr_set_id'] = lgr_set_id
            # redirect to myself to refresh display
            if noframe:
                return redirect('lgr_validate_label_noframe', **kwargs)
            else:
                return redirect('lgr_validate_label', **kwargs)

    ctx['form'] = form
    ctx['lgr_id'] = lgr_id
    ctx['is_set'] = lgr_info.is_set or lgr_set_id is not None

    if lgr_set_id:
        lgr_set_info = select_lgr(request, lgr_set_id)
        ctx['lgr_set'] = lgr_set_info.lgr
        ctx['lgr_set_id'] = lgr_set_id

    if noframe:
        ctx['base_template'] = '_base_noframe.html'

    if output_func:
        return output_func(ctx)
    else:
        return render(request, 'lgr_validator/validator.html', context=ctx)


def validate_label_noframe(request, lgr_id, lgr_set_id=None):
    return validate_label(request, lgr_id, lgr_set_id, noframe=True)


def validate_label_json(request, lgr_id, lgr_set_id=None):
    return validate_label(request, lgr_id,  lgr_set_id=lgr_set_id,
                          threshold_include_vars=-1,
                          output_func=lambda ctx: HttpResponse(json.dumps(ctx), content_type='application/json'))


def validate_label_csv(request, lgr_id, lgr_set_id=None,):
    return validate_label(request, lgr_id, lgr_set_id=lgr_set_id,
                          threshold_include_vars=-1,
                          output_func=_prepare_csv_response)


def _prepare_csv_response(ctx):
    response = HttpResponse(content_type='text/csv', charset='utf-8')
    cd = 'attachment; filename="lgr-val-{0}.csv"'.format(ctx['a_label'])
    response['Content-Disposition'] = cd

    validation_results_to_csv(ctx, response)

    return response
