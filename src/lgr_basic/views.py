# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.generic import FormView

from lgr.exceptions import LGRException
from lgr.tools.utils import download_file, read_labels
from lgr.utils import cp_to_ulabel
from lgr_editor.api import LabelInfo, session_get_storage, LGRInfo, session_list_storage
from lgr_editor.lgr_exceptions import lgr_exception_to_text
from lgr_editor.repertoires import get_by_name
from lgr_tools.tasks import collision_task
from lgr_validator.views import evaluate_label_from_info, NeedAsyncProcess
from lgr_web.views import ADVANCED_INTERFACE_SESSION_KEY
from .forms import ValidateLabelSimpleForm


class BasicModeView(FormView):
    form_class = ValidateLabelSimpleForm
    template_name = 'basic_mode.html'

    def get(self, request, *args, **kwargs):
        # we want to stay in basic mode
        request.session[ADVANCED_INTERFACE_SESSION_KEY] = False
        return super(BasicModeView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        ctx = {}
        labels_cp = form.cleaned_data['labels']
        labels_file = form.cleaned_data.get('labels_file')
        if labels_file:
            labels_json = LabelInfo.from_form(
                labels_file.name,
                labels_file.read())
            labels_cp = []
            for label, valid, error in read_labels(labels_json.labels, as_cp=True):
                labels_cp.append(label)
        else:
            labels_json = LabelInfo.from_list('labels', [cp_to_ulabel(l) for l in labels_cp])

        email_address = form.cleaned_data['email']
        rz_lgr = form.cleaned_data['rz_lgr']
        collisions = form.cleaned_data['collisions']
        lgr_info = LGRInfo(rz_lgr, lgr=get_by_name(rz_lgr))
        lgr_info.update_xml()
        results = []
        for label_cplist in [l for l in labels_cp]:
            try:
                results.append(evaluate_label_from_info(self.request, lgr_info, label_cplist, None, email_address))
            except UnicodeError as ex:
                messages.add_message(self.request, messages.ERROR, lgr_exception_to_text(ex))
            except NeedAsyncProcess:
                messages.add_message(self.request, messages.INFO,
                                     _('Input label generates too many variants to compute them all quickly. '
                                       'You need to enter your email address and will receive a notification once '
                                       'process is done'))
                ctx['email_required'] = True
            except LGRException as ex:
                messages.add_message(self.request, messages.ERROR, lgr_exception_to_text(ex))
                # redirect to myself to refresh display
                return redirect('lgr_basic_mode')

        if collisions:
            tld_json = LabelInfo.from_form('TLDs', download_file(settings.ICANN_TLDS)[1].read().lower()).to_dict()
            lgr_json = lgr_info.to_dict()
            collision_task.delay(lgr_json, labels_json.to_dict(), tld_json, email_address,
                                 False, False, session_get_storage(self.request))

        return self.render_to_response(self.get_context_data(results=results))

    def get_context_data(self, **kwargs):
        ctx = super(BasicModeView, self).get_context_data(**kwargs)
        if 'results' in kwargs:
            ctx['results'] = kwargs['results']
        ctx['storage'] = session_list_storage(self.request)
        return ctx