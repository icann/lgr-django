# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.generic import FormView

from lgr.exceptions import LGRException
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_advanced.lgr_tools.tasks import validate_label_task, lgr_set_validate_label_task
from lgr_advanced.unidb import get_db_by_version
from .api import validation_results_to_csv, lgr_set_evaluate_label, evaluate_label
from .forms import ValidateLabelForm
from ..api import LabelInfo
from ..lgr_editor.views.mixins import LGRHandlingBaseMixin


class NeedAsyncProcess(Exception):
    """Exception used to notify that we need an async process"""
    pass


def evaluate_label_from_info(session,
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

    udata = get_db_by_version(lgr_info.lgr.metadata.unicode_version)
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
            storage_path = session.get_storage_path()
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
            storage_path = session.get_storage_path()
            validate_label_task.delay(lgr_info.to_dict(), label_cplist, email, storage_path)
            ctx['launched_as_task'] = True

    return ctx


class ValidateLabelView(LGRHandlingBaseMixin, FormView):
    form_class = ValidateLabelForm
    template_name = 'lgr_validator/validator.html'
    threshold_include_vars = settings.LGR_VALIDATOR_MAX_VARS_DISPLAY_INLINE
    output_func: str = None
    noframe = False

    def __init__(self):
        super().__init__()
        self.result = {}
        self.email_required = False

    def get_initial(self):
        initial = super().get_initial()
        if self.lgr_info is not None and self.lgr_info.set_labels_info is not None:
            initial['set_labels'].initial = self.lgr_info.set_labels_info.name
        return initial

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        udata = get_db_by_version(self.lgr_info.lgr.metadata.unicode_version)
        scripts = None
        if self.lgr_info.is_set:
            scripts = []
            for lgr_set_info in self.lgr_info.lgr_set:
                try:
                    scripts.append((lgr_set_info.name, lgr_set_info.lgr.metadata.languages[0]))
                except (AttributeError, IndexError):
                    pass
        kwargs.update({
            'idna_decoder': udata.idna_decode_label,
            'scripts': scripts
        })

        if self.request.GET:
            kwargs['data'] = self.request.GET
        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['result'] = self.result
        ctx['lgr_id'] = self.lgr_id
        ctx['is_set'] = self.lgr_info.is_set or self.lgr_set_id is not None
        ctx['email_required'] = self.email_required

        if self.lgr_set_id:
            lgr_set_info = self.session.select_lgr(self.lgr_set_id)
            ctx['lgr_set'] = lgr_set_info.lgr
            ctx['lgr_set_id'] = self.lgr_set_id

        if self.noframe:
            ctx['base_template'] = 'lgr_advanced/_base_noframe.html'

        return ctx

    def form_valid(self, form):
        label_cplist = form.cleaned_data['label']
        script_lgr_name = form.cleaned_data.get('script', None)
        email = form.cleaned_data['email']
        if self.lgr_info.is_set:
            set_labels_file = form.cleaned_data['set_labels']
            if set_labels_file is not None:
                if self.lgr_info.set_labels_info is None or self.lgr_info.set_labels_info.name != set_labels_file.name:
                    self.lgr_info.set_labels_info = LabelInfo.from_form(set_labels_file.name,
                                                                        set_labels_file.read())
        try:
            self.result = evaluate_label_from_info(self.session, self.lgr_info, label_cplist, script_lgr_name, email,
                                                   threshold_include_vars=self.threshold_include_vars)
        except UnicodeError as ex:
            if self.output_func:
                return self._redirect_on_error(ex)

            messages.add_message(self.request, messages.ERROR, lgr_exception_to_text(ex))
        except NeedAsyncProcess:
            messages.add_message(self.request, messages.INFO,
                                 _('Input label generates too many variants to compute them all quickly. '
                                   'You need to enter your email address and will receive a notification once process is done'))
            self.email_required = True
        except LGRException as ex:
            return self._redirect_on_error(ex)

        return self.render_to_response(self.get_context_data(form=form))

    def render_to_response(self, context, **response_kwargs):
        if self.output_func:
            return getattr(self, self.output_func)(context)
        return super().render_to_response(context, **response_kwargs)

    def _redirect_on_error(self, exception):
        messages.add_message(self.request, messages.ERROR, lgr_exception_to_text(exception))
        # redirect to myself to refresh display
        if self.noframe:
            return redirect('lgr_validate_label_noframe', **self.kwargs)
        else:
            return redirect('lgr_validate_label', **self.kwargs)


class ValidateLabelNoFrameView(ValidateLabelView):
    noframe = True


class ValidateLabelJsonView(ValidateLabelView):
    threshold_include_vars = -1
    output_func = '_prepare_json_response'
    noframe = True

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    @staticmethod
    def _prepare_json_response(ctx):
        return JsonResponse(ctx.get('result', 'Error'))


class ValidateLabelCSVView(ValidateLabelView):
    threshold_include_vars = -1
    output_func = '_prepare_csv_response'
    noframe = True

    def get(self, request, *args, **kwargs):
        return self.post(request, *args, **kwargs)

    @staticmethod
    def _prepare_csv_response(ctx):
        response = HttpResponse(content_type='text/csv', charset='utf-8')
        cd = 'attachment; filename="lgr-val-{0}.csv"'.format(ctx.get('result', {}).get('a_label', 'Error'))
        response['Content-Disposition'] = cd

        validation_results_to_csv(ctx['result'], response)

        return response
