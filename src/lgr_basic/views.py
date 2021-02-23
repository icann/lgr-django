# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import six
from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.translation import ugettext as _
from django.views.generic import FormView

from lgr.exceptions import LGRException
from lgr.tools.utils import download_file, read_labels
from lgr.utils import cp_to_ulabel
from lgr_advanced.api import LGRInfo, LabelInfo, LGRToolSession
from lgr_advanced.lgr_editor.repertoires import get_by_name
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_advanced.lgr_tools.tasks import annotate_task, basic_collision_task
from lgr_advanced.lgr_validator.views import evaluate_label_from_info, NeedAsyncProcess
from lgr_web.views import INTERFACE_SESSION_KEY, Interfaces
from .forms import ValidateLabelSimpleForm


class BasicModeView(FormView):
    form_class = ValidateLabelSimpleForm
    template_name = 'lgr_basic/basic_mode.html'

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        request.session[INTERFACE_SESSION_KEY] = Interfaces.BASIC.name
        self.session = LGRToolSession(request)

    def form_valid(self, form):
        ctx = {}
        results = []

        email_address = form.cleaned_data['email']
        labels_cp = form.cleaned_data['labels']
        labels_file = form.cleaned_data.get('labels_file')
        rz_lgr = form.cleaned_data['rz_lgr']
        ctx['lgr_id'] = rz_lgr  # needed to download results as csv
        collisions = form.cleaned_data['collisions']
        tlds = None
        tld_json = {}
        if collisions:
            tlds = download_file(settings.ICANN_TLDS)[1].read().lower()
            tld_json = LabelInfo.from_form('TLDs', tlds).to_dict()
        lgr_info = LGRInfo(rz_lgr, lgr=get_by_name(rz_lgr, with_unidb=True))
        lgr_info.update_xml()
        lgr_json = lgr_info.to_dict()
        storage_path = self.session.get_storage_path()

        if labels_file:
            labels_json = LabelInfo.from_form(labels_file.name, labels_file.read()).to_dict()
            # data will be sent by email instead of on the ui
            ctx['validation_to'] = email_address
            if collisions:
                basic_collision_task.delay(lgr_json, labels_json, tld_json, email_address, storage_path, True)
                ctx['collision_to'] = email_address
            else:
                annotate_task.delay(lgr_json, labels_json, email_address, storage_path)

        else:
            labels_json = LabelInfo.from_list('labels', [cp_to_ulabel(l) for l in labels_cp]).to_dict()
            check_collisions = None
            if collisions:
                if len(labels_cp) == 1:
                    # if only one label include collisions directly in result
                    data = tlds.decode('utf-8')
                    check_collisions = [l[0] for l in read_labels(six.StringIO(data))]
                else:
                    basic_collision_task.delay(lgr_json, labels_json, tld_json, email_address, storage_path,
                                               False)
                    ctx['collision_to'] = email_address

            for label_cplist in labels_cp:
                try:
                    results.append(evaluate_label_from_info(self.session, lgr_info, label_cplist, None, email_address,
                                                            check_collisions=check_collisions))
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

        return self.render_to_response(self.get_context_data(results=results, **ctx))

    def get_context_data(self, **kwargs):
        ctx = super(BasicModeView, self).get_context_data(**kwargs)
        if 'results' in kwargs:
            ctx['results'] = kwargs.pop('results')
        ctx['storage'] = self.session.list_storage()
        ctx.update(kwargs)
        return ctx
