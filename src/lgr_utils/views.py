from dal_select2.views import Select2GroupListView
from django.contrib.auth.mixins import LoginRequiredMixin

from lgr_idn_table_review.idn_tool.api import RFC_CORE_REQUIREMENT
from lgr_models.models.lgr import RzLgr, RzLgrMember, RefLgr, RefLgrMember


class RefLgrAutocomplete(LoginRequiredMixin, Select2GroupListView):

    @staticmethod
    def get_list():
        lgr_choices = RefLgrAutocomplete.build_choices(RzLgr, RzLgrMember, 'rz_lgr')
        lgr_choices += RefLgrAutocomplete.build_choices(RefLgr, RefLgrMember, 'ref_lgr')
        return lgr_choices

    @staticmethod
    def build_choices(lgr_model, member_model, common_field):
        lgr_choices = []
        for lgr_obj in lgr_model.objects.filter(active=True):
            lgr_member_choices = ((str(lgr_obj.to_tuple()), lgr_obj.filename),) + tuple(
                (str(lgr_member.to_tuple()), lgr_member.name) for lgr_member in member_model.objects.filter
                (**{common_field : lgr_obj}))
            lgr_choices += [((lgr_obj.name, lgr_obj.name), lgr_member_choices)]
        return lgr_choices


class RefLgrAutocompleteWithCore(RefLgrAutocomplete):

    @staticmethod
    def get_list():
        lgr_choices = super(RefLgrAutocompleteWithCore, RefLgrAutocompleteWithCore).get_list()
        lgr_choices += [(('RFC Core Requirements', 'RFC Core Requirements'),
                         ((RFC_CORE_REQUIREMENT, 'RFC Core Requirements'),))]

        return lgr_choices