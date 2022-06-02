from django.db.models import Value, IntegerField
from django.db.models.functions import Replace, Cast
from django.urls import reverse_lazy
from django.views.generic import UpdateView, CreateView

from lgr_manage.forms import UnicodeVersionUpdateForm, UnicodeVersionCreateForm
from lgr_manage.views.common import BaseAdminMixin, BaseListAdminView
from lgr_models.models.unicode import UnicodeVersion


class LgrUnicodeVersionsListView(BaseListAdminView):
    template_name = 'lgr_manage/unicode_versions.html'
    # 10.0.0, 14.0.0, 9.0.0 -> 1400, 1000, 900 (to properly sort versions)
    queryset = UnicodeVersion.all().order_by(
      Cast(Replace('version', Value('.'), Value('')), output_field=IntegerField())
    ).reverse()
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
