from django.urls import reverse_lazy
from django.views.generic import ListView, UpdateView, CreateView

from lgr_manage.forms import UnicodeVersionUpdateForm, UnicodeVersionCreateForm
from lgr_manage.views.common import BaseAdminView
from lgr_models.models.lgr import UnicodeVersion


class LgrUnicodeVersionsListView(BaseAdminView, ListView):
    template_name = 'lgr_manage/unicode_versions.html'
    queryset = UnicodeVersion.all()
    model = UnicodeVersion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UnicodeVersionCreateForm()
        return context


class LgrUnicodeVersionUpdateView(BaseAdminView, UpdateView):
    template_name = 'lgr_manage/unicode_versions.html'
    form_class = UnicodeVersionUpdateForm
    model = UnicodeVersion
    success_url = reverse_lazy('lgr_idn_admin_unicode_versions')


class LgrUnicodeVersionCreateView(BaseAdminView, CreateView):
    template_name = 'lgr_manage/unicode_versions.html'
    form_class = UnicodeVersionCreateForm
    model = UnicodeVersion
    success_url = reverse_lazy('lgr_idn_admin_unicode_versions')
