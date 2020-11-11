# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import json
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils.translation import ugettext as _

from lgr.exceptions import LGRException
from lgr_editor.api import LabelInfo, session_get_storage
from lgr_editor.lgr_exceptions import lgr_exception_to_text
from lgr_tools.tasks import validate_label_task, lgr_set_validate_label_task
from .api import validation_results_to_csv, lgr_set_evaluate_label, evaluate_label
from .forms import ValidateLabelForm

select_lgr = getattr(__import__(settings.LGR_SELECTOR_FUNC.rpartition('.')[0],
                                fromlist=[settings.LGR_SELECTOR_FUNC.rpartition('.')[0]]),
                     settings.LGR_SELECTOR_FUNC.rpartition('.')[2])

get_unidb = getattr(__import__(settings.UNIDB_LOADER_FUNC.rpartition('.')[0],
                               fromlist=[settings.UNIDB_LOADER_FUNC.rpartition('.')[0]]),
                    settings.UNIDB_LOADER_FUNC.rpartition('.')[2])


class NeedAsyncProcess(Exception):
    """Exception used to notify that we need an async process"""
    pass


def evaluate_label_from_info(request,
                             lgr_info, label_cplist, script_lgr_name,
                             email,
                             threshold_include_vars=settings.LGR_VALIDATOR_MAX_VARS_DISPLAY_INLINE,
                             check_collisions=None):
    """
    Evaluate a label in an LGR.

    This function is responsible to determine whether or not the evaluation process should be blocking/synchronous,
    or launched as a celery task.

    :param lgr_info: The LGR Info object
    :param label_cplist: The label to test, as an array of codepoints.
    :param script_lgr_name: Name of the LGR to use as the script LGR.
    :param email: Required to launch processing in task queue.
    :param threshold_include_vars: Include variants in results if the number of variant labels is less or equal to this.
                                   Set to negative to always return variants.
    :param check_collisions: Check for collisions with the provided list of labels
    :return: a dict containing results of the evaluation, empty if process is asynchronous.
    """
    ctx = {}
    need_async = lgr_info.lgr.estimate_variant_number(label_cplist) > settings.LGR_VALIDATION_MAX_VARS_SYNCHRONOUS
    if need_async and not email:
        raise NeedAsyncProcess

    udata = get_unidb(lgr_info.lgr.metadata.unicode_version)
    if lgr_info.is_set:
        script_lgr_info = None
        for set_lgr_info in lgr_info.lgr_set:
            if script_lgr_name == set_lgr_info.name:
                script_lgr_info = set_lgr_info
                break
        if not need_async:
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
            storage_path = session_get_storage(request)
            lgr_set_validate_label_task.delay(lgr_info.to_dict(), script_lgr_info.to_dict(), label_cplist, email,
                                              storage_path)
            ctx['launched_as_task'] = True
    else:
        if not need_async:
            ctx = evaluate_label(lgr_info.lgr, label_cplist,
                                 threshold_include_vars=threshold_include_vars,
                                 idna_encoder=udata.idna_encode_label,
                                 check_collisions=check_collisions)
        else:
            storage_path = session_get_storage(request)
            validate_label_task.delay(lgr_info.to_dict(), label_cplist, email, storage_path)
            ctx['launched_as_task'] = True

    return ctx


def validate_label(request, lgr_id, lgr_set_id=None,
                   threshold_include_vars=settings.LGR_VALIDATOR_MAX_VARS_DISPLAY_INLINE,
                   output_func=None, noframe=False):
    lgr_info = select_lgr(request, lgr_id, lgr_set_id)
    udata = get_unidb(lgr_info.lgr.metadata.unicode_version)
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
                             idna_decoder=udata.idna_decode_label,
                             scripts=scripts)
    ctx = {}
    if form.is_bound and form.is_valid():
        label_cplist = form.cleaned_data['label']
        script_lgr_name = form.cleaned_data.get('script', None)
        email = form.cleaned_data['email']
        if lgr_info.is_set:
            set_labels_file = form.cleaned_data['set_labels']
            if set_labels_file is not None:
                if lgr_info.set_labels_info is None or lgr_info.set_labels_info.name != set_labels_file.name:
                    lgr_info.set_labels_info = LabelInfo.from_form(set_labels_file.name,
                                                                   set_labels_file.read())
        try:
            ctx['result'] = evaluate_label_from_info(request, lgr_info, label_cplist, script_lgr_name, email,
                                                     threshold_include_vars=threshold_include_vars)
        except UnicodeError as ex:
            if output_func:
                return _redirect_on_error(request, lgr_id, lgr_set_id, ex, noframe)

            messages.add_message(request, messages.ERROR,
                                 lgr_exception_to_text(ex))
        except NeedAsyncProcess:
            messages.add_message(request, messages.INFO,
                                 _('Input label generates too many variants to compute them all quickly. '
                                   'You need to enter your email address and will receive a notification once process is done'))
            ctx['email_required'] = True
        except LGRException as ex:
            return _redirect_on_error(request, lgr_id, lgr_set_id, ex, noframe)

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


def _redirect_on_error(request, lgr_id, lgr_set_id, exception, noframe):
    messages.add_message(request, messages.ERROR,
                         lgr_exception_to_text(exception))
    kwargs = {'lgr_id': lgr_id}
    if lgr_set_id is not None:
        kwargs['lgr_set_id'] = lgr_set_id
    # redirect to myself to refresh display
    if noframe:
        return redirect('lgr_validate_label_noframe', **kwargs)
    else:
        return redirect('lgr_validate_label', **kwargs)


def validate_label_noframe(request, lgr_id, lgr_set_id=None):
    return validate_label(request, lgr_id, lgr_set_id, noframe=True)


def validate_label_json(request, lgr_id, lgr_set_id=None):
    return validate_label(request, lgr_id,  lgr_set_id=lgr_set_id,
                          threshold_include_vars=-1,
                          output_func=lambda ctx: HttpResponse(json.dumps(ctx.get('result', 'Error')),
                                                               content_type='application/json'),
                          noframe=True)


def validate_label_csv(request, lgr_id, lgr_set_id=None,):
    return validate_label(request, lgr_id, lgr_set_id=lgr_set_id,
                          threshold_include_vars=-1,
                          output_func=_prepare_csv_response, noframe=True)


def _prepare_csv_response(ctx):
    response = HttpResponse(content_type='text/csv', charset='utf-8')
    cd = 'attachment; filename="lgr-val-{0}.csv"'.format(ctx.get('result', {}).get('a_label', 'Error'))
    response['Content-Disposition'] = cd

    validation_results_to_csv(ctx['result'], response)

    return response
