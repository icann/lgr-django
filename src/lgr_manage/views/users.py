# -*- coding: utf-8 -*-
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponseBadRequest
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from django.views.generic import View, RedirectView, CreateView, DeleteView
from django.views.generic.detail import SingleObjectMixin

from lgr_auth.forms import UserForm
from lgr_auth.models import LgrUser, LgrRole
from lgr_auth.views import LgrUserUpdateView
from lgr_manage.views.common import BaseListAdminView, BaseAdminMixin


class LgrUserListView(BaseListAdminView):
    model = LgrUser
    queryset = LgrUser.objects.all()
    template_name = 'lgr_manage/user_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = LgrUserCreateView.form_class(can_edit_role=True)
        context['can_manage'] = settings.AUTH_METHOD != 'ICANN'
        return context


class LgrUserCreateView(BaseAdminMixin, CreateView):
    model = LgrUser
    form_class = UserForm
    template_name = 'lgr_manage/user_management.html'
    success_url = reverse_lazy('lgr_admin_user_management')

    def post(self, request, *args, **kwargs):
        if settings.AUTH_METHOD == 'ICANN':
            return HttpResponseBadRequest(_('Cannot create users when auth is performed with ICANN'))

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['can_edit_role'] = True
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = LgrUserListView.queryset.all()
        context['can_manage'] = settings.AUTH_METHOD != 'ICANN'
        return context

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, _('New user created'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, _('Failed to create user'))
        return super().form_invalid(form)


class LgrUserView(BaseAdminMixin, View):

    def get(self, request, *args, **kwargs):
        view = LgrUserListView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = LgrUserCreateView.as_view()
        return view(request, *args, **kwargs)


class LgrUserAdminUpdateView(BaseAdminMixin, LgrUserUpdateView):
    template_name = 'lgr_manage/user_update.html'
    success_url_name = 'lgr_admin_update_user'

    def get_queryset(self):
        return LgrUser.objects.exclude(role__exact=LgrRole.ADMIN)


class LgrUserChangeStatusView(BaseAdminMixin, SingleObjectMixin, RedirectView):
    model = LgrUser
    url = reverse_lazy('lgr_admin_user_management')
    pk_url_kwarg = 'user_pk'
    enable = None

    def get_redirect_url(self, *args, **kwargs):
        return self.request.GET.get('next', super(LgrUserChangeStatusView, self).get_redirect_url(*args, **kwargs))

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        user.enable(not user.enabled())
        return super(LgrUserChangeStatusView, self).post(request, *args, **kwargs)


class LgrUserDeleteView(BaseAdminMixin, DeleteView):
    model = LgrUser
    success_url = reverse_lazy('lgr_admin_user_management')
    pk_url_kwarg = 'user_pk'
