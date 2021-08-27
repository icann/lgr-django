from django import views
from django.urls import reverse
from django.views.generic import ListView, UpdateView

from lgr_business.unicode_versions import UnicodeVersions
from lgr_manage.forms import UnicodeVersionForm
from lgr_manage.views.common import BaseAdminView
from lgr_models.models import UnicodeVersion


class LgrUnicodeVersionsView(BaseAdminView, views.View):
    def get(self, request, *args, **kwargs):
        view = LgrUnicodeVersionsListView.as_view()
        return view(request, *args, **kwargs)

    def post(self, request, *args, **kwargs):
        view = LgrUnicodeVersionUpdateView.as_view()
        return view(request, *args, **kwargs)


class LgrUnicodeVersionsListView(BaseAdminView, ListView):
    template_name = 'lgr_idn_table_review_admin/unicode_versions.html'
    unicode_versions = UnicodeVersions()

    def get_queryset(self):
        return self.unicode_versions.get()


class LgrUnicodeVersionUpdateView(BaseAdminView, UpdateView):
    template_name = 'lgr_idn_table_review_admin/unicode_versions.html'
    form_class = UnicodeVersionForm
    model = UnicodeVersion

    def get_success_url(self):
        return reverse('lgr_idn_admin_unicode_versions')
