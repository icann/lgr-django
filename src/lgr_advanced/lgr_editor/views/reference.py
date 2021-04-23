#! /bin/env python
# -*- coding: utf-8 -*-
"""
reference - 
"""
import logging

from django.contrib import messages
from django.http import Http404, HttpResponseBadRequest, JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import TemplateView, FormView

from lgr.exceptions import LGRException
from lgr_advanced.lgr_editor.forms import ReferenceForm, ReferenceFormSet
from lgr_advanced.lgr_editor.views.mixins import LGRHandlingBaseMixin, LGREditMixin
from lgr_advanced.lgr_exceptions import lgr_exception_to_text

logger = logging.getLogger('reference')


class ReferenceViewMixin:

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        references = [{
            'ref_id': ref_id,
            'description': ref.get('value', ''),
            'comment': ref.get('comment', '')
        } for (ref_id, ref) in self.lgr_info.lgr.reference_manager.items()]

        add_reference_form = None
        references_form = None
        form = ctx.get('form')
        if form:
            if isinstance(form, ReferenceForm):
                add_reference_form = form
            if isinstance(form, ReferenceFormSet):
                references_form = form
        add_reference_form = add_reference_form or ReferenceForm(prefix='add_reference', ro_id=False)
        references_form = references_form or ReferenceFormSet(initial=references,
                                                              prefix='references',
                                                              disabled=self.lgr_info.is_set or self.lgr_set_id is not None)
        ctx.update({
            'add_reference_form': add_reference_form,
            'references_form': references_form,
            'lgr': self.lgr_info.lgr,
            'lgr_id': self.lgr_id,
            'is_set': self.lgr_info.is_set or self.lgr_set_id is not None
        })
        if self.lgr_set_id:
            lgr_set_info = self.session.select_lgr(self.lgr_set_id)
            ctx['lgr_set'] = lgr_set_info.lgr
            ctx['lgr_set_id'] = self.lgr_set_id
        return ctx


class ReferenceView(LGRHandlingBaseMixin, ReferenceViewMixin, TemplateView):
    """
    List/edit references of an LGR.
    """
    template_name = 'lgr_editor/references.html'

    def post(self, request, *args, **kwargs):
        if 'add_reference' in request.POST:
            view = AddReferenceView.as_view()
        elif 'edit_references' in request.POST:
            view = EditReferenceView.as_view()
        else:
            raise Http404

        return view(request, *args, **kwargs)


class AddReferenceView(LGREditMixin, ReferenceViewMixin, FormView):
    form_class = ReferenceForm
    template_name = 'lgr_editor/references.html'

    def get_prefix(self):
        return 'add_reference'

    def get_success_url(self):
        return reverse('references', kwargs={'lgr_id': self.lgr_id})

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['ro_id'] = False
        return kwargs

    def form_valid(self, form):
        logger.debug('Add reference')
        if form.is_valid():
            # form was submitted, we parse the value from the form field
            ref_id = form.cleaned_data['ref_id']
            description = form.cleaned_data['description']
            url = form.cleaned_data['comment']
            try:
                self.lgr_info.lgr.reference_manager.add_reference(description, url, ref_id=ref_id or None)
                self.session.save_lgr(self.lgr_info)
                messages.success(self.request, _('New reference created'))
            except LGRException as ex:
                messages.add_message(self.request, messages.ERROR, lgr_exception_to_text(ex))
                # do nothing to redirect to myself (success url) to refresh display
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.error('Add reference: form is not valid')
        logger.error(form.errors)
        return super().form_invalid(form)


class EditReferenceView(LGREditMixin, ReferenceViewMixin, FormView):
    form_class = ReferenceFormSet
    template_name = 'lgr_editor/references.html'

    def get_prefix(self):
        return 'references'

    def get_success_url(self):
        return reverse('references', kwargs={'lgr_id': self.lgr_id})

    def form_valid(self, form):
        logger.debug('Edit reference')
        reference_manager = self.lgr_info.lgr.reference_manager
        for ref_form in form:
            ref_id = ref_form.cleaned_data['ref_id']
            description = ref_form.cleaned_data['description']
            comment = ref_form.cleaned_data['comment']
            try:
                reference_manager.update_reference(ref_id,
                                                   value=description,
                                                   comment=comment)
                self.session.save_lgr(self.lgr_info)
            except LGRException as ex:
                messages.add_message(self.request, messages.ERROR, lgr_exception_to_text(ex))
                # do nothing to redirect to myself (success url) to refresh display
        return super().form_valid(form)

    def form_invalid(self, form):
        logger.error('Edit reference: form is not valid')
        logger.error(form.errors)
        return super().form_invalid(form)


class ListReferenceJsonView(LGRHandlingBaseMixin, View):
    """
    Return the list of defined references as JSON.
    """

    def get(self, request, *args, **kwargs):
        references = [{
            'ref_id': ref_id,
            'description': ref.get('value', ''),
            'comment': ref.get('comment', '')
        } for (ref_id, ref) in self.lgr_info.lgr.reference_manager.items()]

        return JsonResponse(references, charset='UTF-8', safe=False)


class AddReferenceAjaxView(LGREditMixin, FormView):
    """
    AJAX interface to create a new reference.
    """
    form_class = ReferenceForm

    def form_valid(self, form):
        ref_id = form.cleaned_data['ref_id'] or None
        description = form.cleaned_data['description']
        url = form.cleaned_data['comment']
        try:
            self.lgr_info.lgr.reference_manager.add_reference(description, url, ref_id=ref_id)
            self.session.save_lgr(self.lgr_info)
            references = [{
                'ref_id': ref_id,
                'description': ref.get('value', ''),
                'comment': ref.get('comment', '')
            } for (ref_id, ref) in self.lgr_info.lgr.reference_manager.items()]
            rv = {'ok': True, 'data': references}
        except LGRException as ex:
            rv = {'ok': False, 'error': lgr_exception_to_text(ex)}

        return JsonResponse(rv, charset='UTF-8')

    def form_invalid(self, form):
        return HttpResponseBadRequest(form.errors)


class DeleteReferenceView(LGREditMixin, View):
    """
    Delete a reference from an LGR.
    """

    def get(self, request, *args, **kwargs):
        ref_id = self.kwargs['ref_id']
        logger.debug("Delete reference %s'", ref_id)
        lgr_info = self.session.select_lgr(self.lgr_id)
        if lgr_info.is_set:
            return HttpResponseBadRequest('Cannot edit LGR set')

        try:
            lgr_info.lgr.del_reference(ref_id)
            self.session.save_lgr(lgr_info)
        except LGRException as ex:
            messages.add_message(request, messages.ERROR,
                                 lgr_exception_to_text(ex))

        return redirect('references', lgr_id=self.lgr_id)
