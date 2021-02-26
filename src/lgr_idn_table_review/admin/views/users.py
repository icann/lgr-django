# -*- coding: utf-8 -*-
from django import views
from django.contrib import messages
from django.urls import reverse_lazy
from django.utils.translation import ugettext_lazy as _
from lgr_auth.models import LgrUser, LgrRole
from lgr_idn_table_review.admin.forms import UserCreateForm
from lgr_idn_table_review.admin.views.common import BaseListAdminView, BaseAdminView


class LgrUserListView(BaseListAdminView):
    model = LgrUser
    queryset = LgrUser.objects.filter(role=LgrRole.ICANN.value).order_by('email')
    template_name = 'lgr_idn_table_review_admin/user_management.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = LgrUserCreateView.form_class()
        return context


class LgrUserCreateView(BaseAdminView, views.generic.CreateView):
    model = LgrUser
    form_class = UserCreateForm
    template_name = 'lgr_idn_table_review_admin/user_management.html'
    success_url = reverse_lazy('lgr_idn_admin_user_management')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['object_list'] = LgrUserListView.queryset.all()
        return context

    def form_valid(self, form):
        messages.add_message(self.request, messages.SUCCESS, _('New user created'))
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.add_message(self.request, messages.ERROR, _('Failed to create user'))
        return super().form_invalid(form)

class LgrUserView(BaseAdminView, views.View):

    def get(self, request, *args, **kwargs):
        view = LgrUserListView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = LgrUserCreateView.as_view()
        return view(request, *args, **kwargs)


class LgrUserDeleteView(BaseAdminView, views.generic.DeleteView):
    model = LgrUser
    success_url = reverse_lazy('lgr_idn_admin_user_management')
    pk_url_kwarg = 'user_id'
