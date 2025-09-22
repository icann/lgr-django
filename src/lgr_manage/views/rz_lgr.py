from django import views
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _

from lgr_manage.forms import RzLgrCreateForm, RzLgrIsActiveForm
from lgr_manage.views.ajax_mixin import AjaxFormViewMixin
from lgr_manage.views.common import (
    BaseAdminMixin,
    BaseCreateInitActiveMixin,
    BaseDeleteModelInitActiveMixin,
    BaseListAdminView,
    initial_active)
from lgr_models.models.lgr import RzLgr


class RzLgrListView(BaseListAdminView):
    model = RzLgr
    template_name = 'lgr_manage/rz_lgr.html'
    active_form = RzLgrIsActiveForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = RzLgrCreateForm()
        return context


class RzLgrCreateView(BaseCreateInitActiveMixin, views.generic.CreateView):
    model = RzLgr
    form_class = RzLgrCreateForm
    template_name = 'lgr_manage/rz_lgr.html'
    success_url = reverse_lazy('lgr_admin_rz_lgr')
    active_form = RzLgrIsActiveForm

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, _('New RZ LGR created'))
        response = super().form_valid(form)
        initial_active(RzLgr, set_active=True)
        return response

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, _('Failed to create RZ LGR'))
        return super().form_invalid(form)


class RzLgrView(BaseAdminMixin, views.View):

    def get(self, request, *args, **kwargs):
        view = RzLgrListView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = RzLgrCreateView.as_view()
        return view(request, *args, **kwargs)


class RzLgrDeleteView(BaseDeleteModelInitActiveMixin):
    model = RzLgr
    success_url = reverse_lazy('lgr_admin_rz_lgr')
    pk_url_kwarg = 'lgr_pk'


class RzLgrIsActiveView(AjaxFormViewMixin, views.generic.edit.FormView):
    model = RzLgr
    form_class = RzLgrIsActiveForm
    template_name = 'lgr_manage/rz_lgr.html'
    success_url = reverse_lazy('lgr_admin_rz_lgr')
