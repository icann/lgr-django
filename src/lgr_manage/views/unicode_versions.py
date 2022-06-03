from django.urls import reverse_lazy
from django.views.generic import UpdateView, CreateView

from lgr_manage.forms import UnicodeVersionUpdateForm, UnicodeVersionCreateForm
from lgr_manage.views.common import BaseAdminMixin, BaseListAdminView
from lgr_models.models.lgr import UnicodeVersion


class LgrUnicodeVersionsListView(BaseListAdminView):
    template_name = 'lgr_manage/unicode_versions.html'
    queryset = UnicodeVersion.all()
    model = UnicodeVersion

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = UnicodeVersionCreateForm()
        return context


class LgrUnicodeVersionUpdateView(BaseAdminMixin, UpdateView):
    template_name = 'lgr_manage/unicode_versions.html'
    form_class = UnicodeVersionUpdateForm
    model = UnicodeVersion
    success_url = reverse_lazy('lgr_admin_unicode_versions')


class LgrUnicodeVersionCreateView(BaseAdminMixin, CreateView):
    template_name = 'lgr_manage/unicode_versions.html'
    form_class = UnicodeVersionCreateForm
    model = UnicodeVersion
    success_url = reverse_lazy('lgr_admin_unicode_versions')
