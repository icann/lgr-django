# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import FormView

from lgr.tools.utils import download_file
from lgr_advanced.lgr_tools.api import lgr_intersect_union, lgr_comp_diff, lgr_harmonization, LGRCompInvalidException
from lgr_advanced.lgr_tools.forms import (LGRCompareSelector,
                                          LGRDiffSelector,
                                          LGRCollisionSelector,
                                          LGRAnnotateSelector,
                                          LGRCrossScriptVariantsSelector,
                                          LGRHarmonizeSelector,
                                          LGRComputeVariantsSelector)
from lgr_models.models.lgr import LgrBaseModel, RzLgr
from .tasks import (diff_task,
                    collision_task,
                    annotate_task,
                    lgr_set_annotate_task,
                    cross_script_variants_task,
                    validate_labels_task)
from ..api import LabelInfo
from ..models import LgrModel, SetLgrModel
from lgr_utils.cp import cp_to_slug
from ..views import LGRViewMixin


class LGRToolBaseView(LGRViewMixin, FormView):
    initial_field = 'lgr'
    async_method = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.lgr_pk = self.kwargs.get('lgr_pk')
        self.email_address = request.user.email

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial[self.initial_field] = self.lgr_pk or ''
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'email': self.email_address,
        })
        return ctx

    def get_async_method(self, lgr_object: LgrBaseModel):
        return self.async_method

    def call_async(self, selected_lgr_object: LgrBaseModel, *args, **kwargs):
        method = self.get_async_method(selected_lgr_object)
        if not method:
            raise RuntimeError

        method.delay(self.request.user.pk, selected_lgr_object.pk, *args, **kwargs)


class LGRCompareView(LGRToolBaseView):
    form_class = LGRCompareSelector
    template_name = 'lgr_tools/compare.html'
    initial_field = 'lgr_1'

    def get_success_url(self):
        return reverse('codepoint_list', kwargs={'lgr_pk': self.lgr_pk})

    def form_valid(self, form):
        lgr_pk_1, lgr_pk_2 = (form.cleaned_data[lgr_id] for lgr_id in ('lgr_1', 'lgr_2'))
        action = form.cleaned_data['action']

        lgr_object_1, lgr_object_2 = (LgrModel.objects.get(owner=self.request.user, pk=pk)
                                      for pk in (lgr_pk_1, lgr_pk_2))

        if action in ['INTERSECTION', 'UNION']:
            try:
                lgr_object = lgr_intersect_union(self.request.user,
                                                 lgr_object_1.to_lgr(),
                                                 lgr_object_2.to_lgr(),
                                                 action)
                self.lgr_pk = lgr_object.pk
            except LGRCompInvalidException as lgr_xml:
                from io import BytesIO
                from gzip import GzipFile
                from time import strftime

                sio = BytesIO()
                base_filename = '{comp_type}-of-{lgr1}-and-{lgr2}-{date}.xml'.format(
                    comp_type=action.lower(),
                    lgr1=lgr_object_1.name,
                    lgr2=lgr_object_2.name,
                    date=strftime('%Y%m%d_%H%M%S'))
                with GzipFile(filename=base_filename, fileobj=sio, mode='w') as gzf:
                    gzf.write(lgr_xml.content)

                report = self.storage.storage_save_report_file(f'{base_filename}.gz', sio)
                ctx = self.get_context_data()
                ctx.update({
                    'lgr_object_1': lgr_object_1,
                    'lgr_object_2': lgr_object_2,
                    'report': report,
                    'comp_type': action.lower(),
                    'error': lgr_xml.error
                })
                return render(self.request, 'lgr_tools/comp_invalid.html',
                              context=ctx)
        else:
            content = lgr_comp_diff(lgr_object_1, lgr_object_2, form.cleaned_data['full_dump'])
            ctx = self.get_context_data()
            ctx.update({
                'content': content,
                'lgr_object_1': lgr_object_1,
                'lgr_object_2': lgr_object_2,
            })
            return render(self.request, 'lgr_tools/comp_diff.html', context=ctx)

        return super().form_valid(form)


class LGRDiffView(LGRToolBaseView):
    form_class = LGRDiffSelector
    template_name = 'lgr_tools/diff.html'
    async_method = diff_task

    def form_valid(self, form):
        lgr_pk_1, lgr_pk_2 = (form.cleaned_data[lgr_id] for lgr_id in ('lgr_1', 'lgr_2'))
        labels_file = form.cleaned_data['labels']
        collision = form.cleaned_data['collision']
        full_dump = form.cleaned_data['full_dump']
        with_rules = form.cleaned_data['with_rules']

        lgr_object_1, lgr_object_2 = (LgrModel.objects.get(owner=self.request.user, pk=pk)
                                      for pk in (lgr_pk_1, lgr_pk_2))

        # need to transmit json serializable data
        labels_json = LabelInfo.from_form(labels_file.name,
                                          labels_file.read()).to_dict()
        self.call_async(lgr_object_1, lgr_object_2.pk, labels_json, collision, full_dump, with_rules)

        ctx = self.get_context_data()
        ctx.update({
            'lgr_object_1': lgr_object_1,
            'lgr_object_2': lgr_object_2,
            'labels_file': labels_file.name,
        })
        return render(self.request, 'lgr_tools/wait_diff.html', context=ctx)


class LGRCollisionView(LGRToolBaseView):
    form_class = LGRCollisionSelector
    template_name = 'lgr_tools/collision.html'
    async_method = collision_task

    def form_valid(self, form):
        lgr_pk = form.cleaned_data['lgr']
        labels_file = form.cleaned_data['labels']
        full_dump = form.cleaned_data['full_dump']
        with_rules = form.cleaned_data['with_rules']
        with_tlds = False

        lgr_object = LgrModel.objects.get(owner=self.request.user, pk=lgr_pk)

        # need to transmit json serializable data
        labels_json = LabelInfo.from_form(labels_file.name, labels_file.read()).to_dict()
        tlds_json = None
        if form.cleaned_data['download_tlds']:
            tlds_json = LabelInfo.from_form('TLDs', download_file(settings.ICANN_TLDS)[1].read().lower()).to_dict()
            with_tlds = True
        self.call_async(lgr_object, labels_json, tlds_json, full_dump, with_rules)

        ctx = self.get_context_data()
        ctx.update({
            'lgr_object': lgr_object,
            'labels_file': labels_file.name,
            'icann_tlds': settings.ICANN_TLDS,
            'with_tlds': with_tlds,
        })
        return render(self.request, 'lgr_tools/wait_coll.html', context=ctx)


class LGRAnnotateView(LGRToolBaseView):
    form_class = LGRAnnotateSelector
    template_name = 'lgr_tools/annotate.html'

    def get_async_method(self, lgr_object: LgrModel):
        if lgr_object.is_set():
            return lgr_set_annotate_task
        return annotate_task

    def form_valid(self, form):
        ctx = self.get_context_data()
        lgr_pk = form.cleaned_data['lgr']
        labels_file = form.cleaned_data['labels']

        lgr_object = LgrModel.objects.get(owner=self.request.user, pk=lgr_pk)

        # need to transmit json serializable data
        labels_json = LabelInfo.from_form(labels_file.name,
                                          labels_file.read()).to_dict()
        async_kwargs = {'labels_json': labels_json}

        if lgr_object.is_set():
            set_labels_file = form.cleaned_data['set_labels']
            if not set_labels_file:
                set_labels_info = LabelInfo(name='None', labels=[])
            else:
                # Handle label set
                set_labels_info = LabelInfo.from_form(set_labels_file.name,
                                                      set_labels_file.read())
            async_kwargs['set_labels_json'] = set_labels_info.to_dict()

        if lgr_object.is_set():
            script_lgr_pk = form.cleaned_data['script']
            ctx['script_lgr_pk'] = script_lgr_pk
            async_kwargs['script_lgr_pk'] = script_lgr_pk

        self.call_async(lgr_object, **async_kwargs)

        ctx.update({
            'lgr_object': lgr_object,
            'labels_file': labels_file.name,
        })
        return render(self.request, 'lgr_tools/wait_annotate.html', context=ctx)


class LGRCrossScriptVariantsView(LGRToolBaseView):
    form_class = LGRCrossScriptVariantsSelector
    template_name = 'lgr_tools/cross_script_variants.html'
    async_method = cross_script_variants_task

    def form_valid(self, form):
        ctx = self.get_context_data()
        lgr_pk = form.cleaned_data['lgr']
        labels_file = form.cleaned_data['labels']
        in_set = False

        lgr_object = LgrModel.objects.get(owner=self.request.user, pk=lgr_pk)

        # need to transmit json serializable data
        labels_json = LabelInfo.from_form(labels_file.name,
                                          labels_file.read()).to_dict()

        if lgr_object.is_set():
            in_set = True
            script_lgr_pk = form.cleaned_data['script']
            script_lgr_object = SetLgrModel.objects.get(owner=self.request.user,
                                                        pk=script_lgr_pk)
            lgr_object = script_lgr_object

        self.call_async(lgr_object, in_set, labels_json)

        ctx.update({
            'lgr_object': lgr_object,
            'in_set': in_set,
            'labels_file': labels_file.name,
        })
        return render(self.request, 'lgr_tools/wait_cross_scripts.html', context=ctx)


class LGRHarmonizeView(LGRToolBaseView):
    form_class = LGRHarmonizeSelector
    template_name = 'lgr_tools/harmonize.html'
    initial_field = 'lgr_1'

    def get_initial(self):
        initial = super().get_initial()
        initial['rz_lgr'] = ''
        return initial

    def form_valid(self, form):
        ctx = self.get_context_data()
        lgr_pk_1, lgr_pk_2, rz_lgr_pk = (form.cleaned_data[lgr_id] for lgr_id in ('lgr_1', 'lgr_2', 'rz_lgr'))

        lgr_object_1, lgr_object_2 = (LgrModel.objects.get(owner=self.request.user, pk=pk)
                                      for pk in (lgr_pk_1, lgr_pk_2))
        rz_lgr_object = RzLgr.objects.get(pk=rz_lgr_pk) if rz_lgr_pk else None

        h_lgr_1_object, h_lgr_2_object, cp_review = lgr_harmonization(self.request.user,
                                                                      lgr_object_1,
                                                                      lgr_object_2,
                                                                      rz_lgr_object)

        ctx.update({
            'lgr_object_1': lgr_object_1,
            'lgr_object_2': lgr_object_2,
            'h_lgr_object_1': h_lgr_1_object,
            'h_lgr_object_2': h_lgr_2_object,
            # TODO remove cp_review as not used anymore: from here and harmonization method
            'cp_review': ((h_lgr_1_object.pk, ((c, cp_to_slug(c)) for c in cp_review[0])),
                          (h_lgr_2_object.pk, ((c, cp_to_slug(c)) for c in cp_review[1]))),
            'has_cp_review': bool(cp_review[0]) or bool(cp_review[1])
        })
        return render(self.request, 'lgr_tools/harmonization_result.html', context=ctx)


class LGRComputeVariants(LGRToolBaseView):
    form_class = LGRComputeVariantsSelector
    template_name = 'lgr_tools/variants.html'
    async_method = validate_labels_task

    def form_valid(self, form):
        lgr_pk = form.cleaned_data['lgr']
        labels_file = form.cleaned_data['labels']

        lgr_object = LgrModel.objects.get(owner=self.request.user, pk=lgr_pk)

        # need to transmit json serializable data
        labels_json = LabelInfo.from_form(labels_file.name, labels_file.read()).to_dict()
        self.call_async(lgr_object, labels_json)

        ctx = self.get_context_data()
        ctx.update({
            'lgr_object': lgr_object,
            'labels_file': labels_file.name,
        })
        return render(self.request, 'lgr_tools/wait_variants.html', context=ctx)
