from django.urls import reverse
from django.views.generic import ListView, UpdateView

from lgr_manage.forms import UnicodeVersionForm
from lgr_manage.views.common import BaseAdminView
from lgr_models.models import UnicodeVersion


class LgrUnicodeVersionsView(BaseAdminView, ListView):
    template_name = 'lgr_idn_table_review_admin/unicode_versions.html'
    model = UnicodeVersion


class LgrUnicodeVersionView(BaseAdminView, UpdateView):
    template_name = 'lgr_idn_table_review_admin/unicode_version_detail.html'
    form_class = UnicodeVersionForm
    model = UnicodeVersion

    def get_success_url(self):
        return reverse('lgr_idn_admin_unicode_versions')
