import logging

from django.http import JsonResponse
from django.utils.translation import gettext_lazy as _

from lgr_manage.views.common import BaseAdminMixin


class AjaxFormViewMixin(BaseAdminMixin):
    model = None

    def form_valid(self, form):
        active_pk = form.cleaned_data['active'].pk
        msg = ''

        old_active = None
        try:
            old_active_entity = self.model.objects.filter(active=True)
            if old_active_entity.exists():
                old_active = old_active_entity.first().pk
                old_active_entity.update(active=False)

            new_active = self.model.objects.get(pk=active_pk)
            new_active.active = True
            new_active.save(update_fields=['active'])
        except:
            msg = _("Error processing active indicator")
            form.add_error('active', msg)
            logging.exception(msg)
            return self.form_invalid(self, form)

        data = {
            'old_active': old_active,
            'msg': msg
        }
        return JsonResponse(data)

    def form_invalid(self, form):
        response = super(AjaxFormViewMixin, self).form_invalid(form)
        if self._is_ajax(self.request):
            return JsonResponse(form.errors, status=400)
        else:
            return response

    def _is_ajax(self, request):
        return request.META.get('HTTP_X_REQUESTED_WITH', '') == 'XMLHttpRequest'
