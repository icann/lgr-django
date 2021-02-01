# -*- coding: utf-8 -*-
from django import views
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic.detail import SingleObjectMixin

from lgr_idn_table_review.admin.forms import RefLgrCreateForm
from lgr_idn_table_review.admin.models import RefLgr
from lgr_idn_table_review.admin.views.common import BaseListAdminView, BaseAdminView


class RefLgrListView(BaseListAdminView):
    model = RefLgr
    template_name = 'lgr_idn_table_review_admin/ref_lgr.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = RefLgrCreateForm()
        return context


class RefLgrCreateView(BaseAdminView, views.generic.CreateView):
    model = RefLgr
    form_class = RefLgrCreateForm
    template_name = 'lgr_idn_table_review_admin/ref_lgr.html'
    success_url = reverse_lazy('lgr_idn_admin_ref_lgr')


class RefLgrView(BaseAdminView, views.View):

    def get(self, request, *args, **kwargs):
        view = RefLgrListView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = RefLgrCreateView.as_view()
        return view(request, *args, **kwargs)


class RefLgrDeleteView(BaseAdminView, views.generic.DeleteView):
    model = RefLgr
    success_url = reverse_lazy('lgr_idn_admin_ref_lgr')
    pk_url_kwarg = 'lgr_id'


class DisplayRefLgrView(SingleObjectMixin, views.View):
    pk_url_kwarg = 'lgr_id'
    model = RefLgr

    def get(self, request, *args, **kwargs):
        lgr = self.get_object()
        return HttpResponse(lgr.file.read(), content_type='text/xml', charset='UTF-8')
