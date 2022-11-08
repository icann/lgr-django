# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from io import StringIO

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.cache import cache
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext as _
from django.views.generic import FormView

from lgr.exceptions import LGRException
from lgr.tools.utils import download_file, read_labels
from lgr.utils import cp_to_ulabel
from lgr_advanced.api import LabelInfo, LGRToolStorage
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_advanced.lgr_tools.tasks import annotate_task, basic_collision_task
from lgr_advanced.lgr_validator.views import NeedAsyncProcess, evaluate_label_from_view
from lgr_models.models.lgr import RzLgr, LgrBaseModel
from lgr_tasks.models import LgrTaskModel
from lgr_tasks.tasks import _index_cache_key
from lgr_utils.views import RefLgrAutocomplete
from .forms import ValidateLabelSimpleForm


class BasicModeView(LoginRequiredMixin, FormView):
    form_class = ValidateLabelSimpleForm
    template_name = 'lgr_basic/basic_mode.html'

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['reflgr'] = RefLgrAutocomplete.get_list()
        return kwargs

    def get_initial(self):
        init = super().get_initial()
        rz = RzLgr.objects.filter(active=True).first()
        init['lgr'] = str(rz.to_tuple())
        init['labels'] = self.request.GET.get('label')
        return init

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.storage = LGRToolStorage(request.user)

    def form_valid(self, form):
        ctx = {}
        results = []

        labels_cp = form.cleaned_data['labels']
        labels_file = form.cleaned_data.get('labels_file')
        lgr: LgrBaseModel = form.cleaned_data['lgr']
        ctx['lgr_object'] = lgr  # needed to download results as csv
        collisions = form.cleaned_data['collisions']
        hide_mixed_script_variants = not form.cleaned_data['include_mixed_script_variants']

        if labels_file:
            labels_json = LabelInfo.from_form(labels_file.name, labels_file.read()).to_dict()
            ctx['validation_task'] = True
            task_name = _('Annotate labels on LGR %s') % lgr.pk
            if collisions:
                task_name = _('Compute collisions and annotate labels on %s') % lgr.name
            task = LgrTaskModel.objects.create(app=self.request.resolver_match.app_name,
                                               name=task_name,
                                               user=self.request.user)
            if collisions:
                basic_collision_task.apply_async((self.request.user.pk, lgr.pk, labels_json,
                                                  True, lgr._meta.label), task_id=task.pk)
                ctx['collision_task'] = True
            else:
                annotate_task.apply_async((self.request.user.pk, lgr.pk, labels_json, lgr._meta.label),
                                          task_id=task.pk)
        else:
            result = {}
            is_collision_index = False
            check_collisions = None
            if collisions:
                def launch_collision_task():
                    labels_json = LabelInfo.from_list('labels', [cp_to_ulabel(l) for l in labels_cp]).to_dict()
                    task = LgrTaskModel.objects.create(app=self.request.resolver_match.app_name,
                                                       name=_('Compute collisions on %s') % lgr.name,
                                                       user=self.request.user)
                    basic_collision_task.apply_async((self.request.user.pk, lgr.pk, labels_json,
                                                      False, lgr._meta.label), task_id=task.pk)
                    ctx['collision_task'] = True

                if len(labels_cp) == 1:
                    # if only one label include collisions directly in result
                    tld_indexes = cache.get(_index_cache_key(lgr))
                    result['collision_with_tlds'] = True
                    if not tld_indexes:
                        tlds = download_file(settings.ICANN_TLDS)[1].read().lower()
                        data = tlds.decode('utf-8')
                        check_collisions = [l[0] for l in read_labels(StringIO(data))]
                    else:
                        is_collision_index = True
                        check_collisions = tld_indexes
                else:
                    launch_collision_task()

            for label_cplist in labels_cp:
                try:
                    res = result.copy()
                    res.update(evaluate_label_from_view(self.request,
                                                        lgr,
                                                        label_cplist,
                                                        ignore_thresholds=False,
                                                        check_collisions=check_collisions,
                                                        is_collision_index=is_collision_index,
                                                        hide_mixed_script_variants=hide_mixed_script_variants))
                    if res.get('launched_as_task') and collisions and len(labels_cp) == 1:
                        # task has not been launched as there is only one label,
                        # but it should finally be computed in background
                        launch_collision_task()
                    results.append(res)
                except UnicodeError as ex:
                    messages.add_message(self.request, messages.ERROR, lgr_exception_to_text(ex))
                except NeedAsyncProcess:
                    messages.add_message(self.request, messages.INFO,
                                         mark_safe(_('Input label generates too many variants to compute them all '
                                                     'quickly. You can follow your task progression on the %s.') % (
                                             f"<a href='{reverse('list_process')}'>{_('task status page')}</a>")))
                except LGRException as ex:
                    messages.add_message(self.request, messages.ERROR, lgr_exception_to_text(ex))
                    return self.render_to_response(self.get_context_data(results=results, **ctx))

        return self.render_to_response(self.get_context_data(results=results, **ctx))

    def get_context_data(self, **kwargs):
        ctx = super(BasicModeView, self).get_context_data(**kwargs)
        ctx.update({
            'reports': self.storage.list_storage(),
            'home_url_name': 'lgr_basic_mode'
        })
        ctx.update(kwargs)
        return ctx
