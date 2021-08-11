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
from .tasks import (diff_task,
                    collision_task,
                    annotate_task,
                    lgr_set_annotate_task,
                    cross_script_variants_task,
                    validate_labels_task)
from ..api import LabelInfo
from ..utils import cp_to_slug
from ..views import LGRViewMixin


class LGRToolBaseView(LGRViewMixin, FormView):
    initial_field = 'lgr'
    async_method = None

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.lgr_id = self.kwargs.get('lgr_id')
        self.lgr_info = None
        if self.lgr_id:
            self.lgr_info = self.session.select_lgr(self.lgr_id)
        self.action = None
        self.email_address = request.user.email

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['session_lgrs'] = self.session.list_lgr()
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial[self.initial_field] = self.lgr_id or ''
        return initial

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx.update({
            'lgr_id': self.lgr_id or '',
            'lgr': self.lgr_info.lgr if self.lgr_info else '',
            'is_set': self.lgr_info.is_set if self.lgr_info else '',
            'email': self.email_address,
        })
        return ctx

    def get_async_method(self, lgr_info):
        return self.async_method

    def call_async(self, lgr_info, *args, **kwargs):
        if not self.async_method:
            raise RuntimeError

        method = self.get_async_method(lgr_info)

        method.delay(lgr_info.to_dict(), *args, **kwargs, email_address=self.email_address,
                     storage_path=self.session.get_storage_path())


class LGRToolBaseSetCompatibleView(LGRToolBaseView):

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['session_lgrs'] = self.session.list_lgr()

        # Retrieve complete list of all scripts defined in all sets
        lgr_scripts = set()
        for lgr_dct in self.session.list_lgr():
            if lgr_dct['is_set']:
                lgr_set = [l['name'] for l in lgr_dct['lgr_set_dct']]
                scripts = []
                for lgr_name in lgr_set:
                    lgr_info = self.session.select_lgr(lgr_name, lgr_dct['name'])
                    try:
                        scripts.append((lgr_info.name, lgr_info.lgr.metadata.languages[0]))
                    except (AttributeError, IndexError):
                        pass
                lgr_scripts |= set(scripts)
        kwargs['scripts'] = list(lgr_scripts)
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial[self.initial_field] = self.lgr_id or ''
        return initial


class LGRCompareView(LGRToolBaseView):
    form_class = LGRCompareSelector
    template_name = 'lgr_tools/compare.html'
    initial_field = 'lgr_1'

    def get_success_url(self):
        return reverse('codepoint_list', kwargs={'lgr_id': self.lgr_id})

    def form_valid(self, form):
        lgr_id_1 = form.cleaned_data['lgr_1']
        lgr_id_2 = form.cleaned_data['lgr_2']
        self.action = form.cleaned_data['action']

        lgr_info_1 = self.session.select_lgr(lgr_id_1)
        lgr_info_2 = self.session.select_lgr(lgr_id_2)

        if self.action in ['INTERSECTION', 'UNION']:
            try:
                self.lgr_id = lgr_intersect_union(self.session,
                                                  lgr_info_1, lgr_info_2,
                                                  self.action)
            except LGRCompInvalidException as lgr_xml:
                from io import BytesIO
                from gzip import GzipFile
                from time import strftime

                sio = BytesIO()
                base_filename = '{comp_type}-of-{lgr1}-and-{lgr2}-{date}.xml'.format(
                    comp_type=self.action.lower(),
                    lgr1=lgr_info_1.name,
                    lgr2=lgr_info_2.name,
                    date=strftime('%Y%m%d_%H%M%S'))
                with GzipFile(filename=base_filename, fileobj=sio, mode='w') as gzf:
                    gzf.write(lgr_xml.content)

                filename = self.session.storage_save_file(f'{base_filename}.gz', sio)
                ctx = self.get_context_data()
                ctx.update({
                    'lgr_1': lgr_info_1,
                    'lgr_2': lgr_info_2,
                    'lgr_file_name': filename,
                    'comp_type': self.action.lower(),
                    'error': lgr_xml.error
                })
                return render(self.request, 'lgr_tools/comp_invalid.html',
                              context=ctx)
        else:
            content = lgr_comp_diff(lgr_info_1, lgr_info_2, form.cleaned_data['full_dump'])
            ctx = self.get_context_data()
            ctx.update({
                'content': content,
                'lgr_1': lgr_info_1,
                'lgr_2': lgr_info_2,
            })
            return render(self.request, 'lgr_tools/comp_diff.html', context=ctx)

        return super().form_valid(form)


class LGRDiffView(LGRToolBaseView):
    form_class = LGRDiffSelector
    template_name = 'lgr_tools/diff.html'
    async_method = diff_task

    def form_valid(self, form):
        lgr_id_1 = form.cleaned_data['lgr_1']
        lgr_id_2 = form.cleaned_data['lgr_2']
        labels_file = form.cleaned_data['labels']
        collision = form.cleaned_data['collision']
        full_dump = form.cleaned_data['full_dump']
        with_rules = form.cleaned_data['with_rules']

        lgr_info_1 = self.session.select_lgr(lgr_id_1)
        lgr_info_2 = self.session.select_lgr(lgr_id_2)

        # need to transmit json serializable data
        labels_json = LabelInfo.from_form(labels_file.name,
                                          labels_file.read()).to_dict()
        lgr_2_json = lgr_info_2.to_dict()
        self.call_async(lgr_info_1, lgr_2_json, labels_json, collision, full_dump, with_rules)

        ctx = self.get_context_data()
        ctx.update({
            'lgr_1': lgr_info_1,
            'lgr_2': lgr_info_2,
            'labels_file': labels_file.name,
        })
        return render(self.request, 'lgr_tools/wait_diff.html', context=ctx)


class LGRCollisionView(LGRToolBaseView):
    form_class = LGRCollisionSelector
    template_name = 'lgr_tools/collision.html'
    async_method = collision_task

    def form_valid(self, form):
        lgr_id = form.cleaned_data['lgr']
        labels_file = form.cleaned_data['labels']
        full_dump = form.cleaned_data['full_dump']
        with_rules = form.cleaned_data['with_rules']
        with_tlds = False

        lgr_info = self.session.select_lgr(lgr_id)

        # need to transmit json serializable data
        labels_json = LabelInfo.from_form(labels_file.name, labels_file.read()).to_dict()
        tlds_json = None
        if form.cleaned_data['download_tlds']:
            tlds_json = LabelInfo.from_form('TLDs', download_file(settings.ICANN_TLDS)[1].read().lower()).to_dict()
            with_tlds = True
        self.call_async(lgr_info, labels_json, tlds_json, full_dump, with_rules)

        ctx = self.get_context_data()
        ctx.update({
            'lgr_info': lgr_info,
            'labels_file': labels_file.name,
            'icann_tlds': settings.ICANN_TLDS,
            'with_tlds': with_tlds,
        })
        return render(self.request, 'lgr_tools/wait_coll.html', context=ctx)


class LGRAnnotateView(LGRToolBaseSetCompatibleView):
    form_class = LGRAnnotateSelector
    template_name = 'lgr_tools/annotate.html'

    def get_initial(self):
        initial = super().get_initial()
        if self.lgr_info and self.lgr_info.set_labels_info:
            initial['set_labels'] = self.lgr_info.set_labels_info
        return initial
    
    def get_async_method(self, lgr_info):
        if lgr_info.is_set:
            return lgr_set_annotate_task
        return annotate_task

    def form_valid(self, form):
        ctx = self.get_context_data()
        lgr_id = form.cleaned_data['lgr']
        labels_file = form.cleaned_data['labels']

        lgr_info = self.session.select_lgr(lgr_id)

        # need to transmit json serializable data
        labels_json = LabelInfo.from_form(labels_file.name,
                                          labels_file.read()).to_dict()
        if lgr_info.is_set:
            set_labels_file = form.cleaned_data['set_labels']
            if set_labels_file is not None:
                # Handle label set
                if lgr_info.set_labels_info is None or lgr_info.set_labels_info.name != set_labels_file.name:
                    lgr_info.set_labels_info = LabelInfo.from_form(set_labels_file.name,
                                                                   set_labels_file.read())

        async_kwargs = {}
        if lgr_info.is_set:
            script_lgr_id = form.cleaned_data['script']
            script_lgr_info = self.session.select_lgr(script_lgr_id, lgr_set_id=lgr_id)

            script_lgr_json = script_lgr_info.to_dict()
            ctx['script'] = script_lgr_id
            async_kwargs = {'script_lgr_json': script_lgr_json}

        self.call_async(lgr_info, labels_json, **async_kwargs)

        ctx.update({
            'lgr_info': lgr_info,
            'labels_file': labels_file.name,
        })
        return render(self.request, 'lgr_tools/wait_annotate.html', context=ctx)


class LGRCrossScriptVariantsView(LGRToolBaseSetCompatibleView):
    form_class = LGRCrossScriptVariantsSelector
    template_name = 'lgr_tools/cross_script_variants.html'
    async_method = cross_script_variants_task

    def form_valid(self, form):
        ctx = self.get_context_data()
        lgr_id = form.cleaned_data['lgr']
        labels_file = form.cleaned_data['labels']

        lgr_info = self.session.select_lgr(lgr_id)

        # need to transmit json serializable data
        labels_json = LabelInfo.from_form(labels_file.name,
                                          labels_file.read()).to_dict()

        if lgr_info.is_set:
            script_lgr_id = form.cleaned_data['script']
            script_lgr = self.session.select_lgr(script_lgr_id, lgr_set_id=lgr_id)
            lgr_info = script_lgr

        cross_script_variants_task.delay(lgr_info.to_dict(), labels_json)

        ctx.update({
            'lgr_info': lgr_info,
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
        lgr_1_id, lgr_2_id = form.cleaned_data['lgr_1'], form.cleaned_data['lgr_2']
        rz_lgr_id = form.cleaned_data['rz_lgr'] or None

        lgr_1_info, lgr_2_info = (self.session.select_lgr(l) for l in (lgr_1_id, lgr_2_id))
        rz_lgr = self.session.select_lgr(rz_lgr_id).lgr if rz_lgr_id is not None else None

        h_lgr_1_id, h_lgr_2_id, cp_review = lgr_harmonization(self.session, lgr_1_info.lgr, lgr_2_info.lgr, rz_lgr)

        ctx.update({
            'lgr_1': lgr_1_info,
            'lgr_2': lgr_2_info,
            'h_lgr_1_id': h_lgr_1_id,
            'h_lgr_2_id': h_lgr_2_id,
            'cp_review': ((h_lgr_1_id, ((c, cp_to_slug(c)) for c in cp_review[0])),
                          (h_lgr_2_id, ((c, cp_to_slug(c)) for c in cp_review[1]))),
            'has_cp_review': bool(cp_review[0]) or bool(cp_review[1])
        })
        return render(self.request, 'lgr_tools/harmonization_result.html', context=ctx)


class LGRComputeVariants(LGRToolBaseView):
    form_class = LGRComputeVariantsSelector
    template_name = 'lgr_tools/variants.html'
    async_method = validate_labels_task

    def form_valid(self, form):
        lgr_id = form.cleaned_data['lgr']
        labels_file = form.cleaned_data['labels']

        lgr_info = self.session.select_lgr(lgr_id)

        # need to transmit json serializable data
        labels_json = LabelInfo.from_form(labels_file.name, labels_file.read()).to_dict()
        lgr_json = lgr_info.to_dict()
        self.call_async(lgr_json, labels_json)

        ctx = self.get_context_data()
        ctx.update({
            'lgr_info': lgr_info,
            'labels_file': labels_file.name,
        })
        return render(self.request, 'lgr_tools/wait_variants.html', context=ctx)
