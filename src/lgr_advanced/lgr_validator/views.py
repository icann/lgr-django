# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect
from django.views.generic import FormView

from lgr.exceptions import LGRException
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_advanced.lgr_tools.tasks import validate_label_task, lgr_set_validate_label_task
from lgr_advanced.unidb import get_db_by_version
from lgr_auth.models import LgrUser
from lgr_models.models.lgr import LgrBaseModel, RzLgr
from .api import validation_results_to_csv, lgr_set_evaluate_label, evaluate_label
from .forms import ValidateLabelForm
from ..api import LabelInfo
from ..lgr_editor.repertoires import get_by_name
from ..lgr_editor.views.mixins import LGRHandlingBaseMixin
from ..models import LgrModel


class NeedAsyncProcess(Exception):
    """Exception used to notify that we need an async process"""
    pass


def evaluate_label_from_view(user: LgrUser,
                             lgr_object: LgrBaseModel,
                             label_cplist,
                             script_lgr_pk=None,
                             set_labels_info: LabelInfo = None,
                             threshold_include_vars=settings.LGR_VALIDATOR_MAX_VARS_DISPLAY_INLINE,
                             check_collisions=None):
    """
    Evaluate a label in an LGR.

    This function is responsible to determine whether or not the evaluation process should be blocking/synchronous,
    or launched as a celery task.

    :param user: The current logged in user
    :param lgr_object: The LGR object
    :param label_cplist: The label to test, as an array of codepoints.
    :param script_lgr_pk: Primary key of the LGR to use as the script LGR.
    :param set_labels_info: The LabelInfo allocated in set
    :param threshold_include_vars: Include variants in results if the number of variant labels is less or equal to this.
                                   Set to negative to always return variants.
    :param check_collisions: Check for collisions with the provided list of labels
    :return: a dict containing results of the evaluation, empty if process is asynchronous.
    """
    ctx = {}
    lgr = lgr_object.to_lgr()
    need_async = lgr.estimate_variant_number(label_cplist) > settings.LGR_VALIDATION_MAX_VARS_SYNCHRONOUS
    udata = get_db_by_version(lgr.metadata.unicode_version)
    if lgr_object.is_set():
        lgr_object: LgrModel
        script_lgr_object = lgr_object.set_info.lgr_set.get(owner=user, pk=script_lgr_pk)
        if not need_async:
            set_labels = [] if not set_labels_info else set_labels_info.labels
            ctx = lgr_set_evaluate_label(lgr,
                                         script_lgr_object.to_lgr(),
                                         label_cplist,
                                         set_labels,
                                         threshold_include_vars=threshold_include_vars,
                                         idna_encoder=udata.idna_encode_label)
        else:
            if set_labels_info:
                set_labels_json = set_labels_info.to_dict()
            else:
                set_labels_json = LabelInfo(name='None', labels=[])

            lgr_set_validate_label_task.delay(user.pk, lgr_object.pk, script_lgr_object.pk,
                                              label_cplist, set_labels_json)
            ctx['launched_as_task'] = True
    else:
        if not need_async:
            ctx = evaluate_label(lgr,
                                 label_cplist,
                                 threshold_include_vars=threshold_include_vars,
                                 idna_encoder=udata.idna_encode_label,
                                 check_collisions=check_collisions)
        else:
            validate_label_task.delay(user.pk, lgr_object.pk, label_cplist)
            ctx['launched_as_task'] = True

    return ctx


# TODO remove once rz for basic will be loaded from db
def evaluate_label_from_info(user, lgr_name, label_cplist,
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
    lgr = get_by_name(lgr_name, with_unidb=True)
    need_async = lgr.estimate_variant_number(label_cplist) > settings.LGR_VALIDATION_MAX_VARS_SYNCHRONOUS
    udata = get_db_by_version(lgr.metadata.unicode_version)
    if not need_async:
        ctx = evaluate_label(lgr, label_cplist,
                             threshold_include_vars=threshold_include_vars,
                             idna_encoder=udata.idna_encode_label,
                             check_collisions=check_collisions)
    else:
        validate_label_task.delay(user.pk, lgr.name, label_cplist, lgr_model=RzLgr)
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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        udata = get_db_by_version(self.lgr.metadata.unicode_version)
        scripts = None
        if self.lgr_object.is_set():
            scripts = []
            for lgr_in_set_obj in self.lgr_object.embedded_lgrs():
                lgr_in_set = lgr_in_set_obj.to_lgr()
                try:
                    scripts.append((lgr_in_set_obj.pk, lgr_in_set.metadata.languages[0]))
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

        if self.noframe:
            ctx['base_template'] = 'lgr_advanced/_base_noframe.html'

        return ctx

    def form_valid(self, form):
        label_cplist = form.cleaned_data['label']
        script_lgr_pk = form.cleaned_data.get('script', None)
        set_labels_info = None
        if self.lgr_object.is_set():
            set_labels_file = form.cleaned_data['set_labels']
            if set_labels_file is not None:
                set_labels_info = LabelInfo.from_form(set_labels_file.name,
                                                      set_labels_file.read())
        try:
            self.result = evaluate_label_from_view(self.request.user,
                                                   self.lgr_object,
                                                   label_cplist,
                                                   script_lgr_pk=script_lgr_pk,
                                                   set_labels_info=set_labels_info,
                                                   threshold_include_vars=self.threshold_include_vars)
        except UnicodeError as ex:
            if self.output_func:
                return self._redirect_on_error(ex)

            messages.add_message(self.request, messages.ERROR, lgr_exception_to_text(ex))
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
