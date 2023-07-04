from pathlib import Path

from dal_select2.views import Select2GroupListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils.http import url_has_allowed_host_and_scheme

from lgr_models.models.lgr import RzLgr, RzLgrMember, RefLgr, RefLgrMember

RFC_CORE_REQUIREMENT = 'core'


class RefLgrAutocomplete(LoginRequiredMixin, Select2GroupListView):

    @staticmethod
    def get_list():
        lgr_choices = RefLgrAutocomplete.build_choices(RzLgr, RzLgrMember)
        lgr_choices += RefLgrAutocomplete.build_choices(RefLgr, RefLgrMember)
        return lgr_choices

    @staticmethod
    def build_choices(lgr_model, member_model):
        lgr_choices = []
        for lgr_obj in lgr_model.objects.filter(active=True):
            lgr_member_choices = ((str(lgr_obj.to_tuple()), Path(lgr_obj.filename).stem),) + tuple(
                (str(lgr_member.to_tuple()), lgr_member.name) for lgr_member in
                member_model.objects.filter(common=lgr_obj))
            lgr_choices += [((lgr_obj.name, lgr_obj.name), lgr_member_choices)]
        return lgr_choices


class RefLgrAutocompleteWithCore(RefLgrAutocomplete):

    @staticmethod
    def get_list():
        lgr_choices = super(RefLgrAutocompleteWithCore, RefLgrAutocompleteWithCore).get_list()
        lgr_choices += [(('RFC Core Requirements', 'RFC Core Requirements'),
                         ((RFC_CORE_REQUIREMENT, 'RFC Core Requirements'),))]

        return lgr_choices


def safe_next_redirect_url(request, default):
    redirect_to = request.GET.get('next')
    url_is_safe = False
    if redirect_to:
        url_is_safe = url_has_allowed_host_and_scheme(
            url=redirect_to,
            allowed_hosts=set(request.get_host()),
            require_https=request.is_secure(),
        )
    return redirect_to if url_is_safe else default
