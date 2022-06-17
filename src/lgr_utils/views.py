from dal_select2.views import Select2GroupListView
from django.contrib.auth.mixins import LoginRequiredMixin

from lgr_models.models.lgr import RzLgr, RzLgrMember, RefLgr


class RefLgrAutocomplete(LoginRequiredMixin, Select2GroupListView):

    @staticmethod
    def get_list():
        lgr_choices = []
        for rz in RzLgr.objects.filter(active=True):
            rz_member_choices = ((str(rz.to_tuple()), rz.name),) + tuple(
                (str(rz_member.to_tuple()), rz_member.name) for rz_member in RzLgrMember.objects.filter(rz_lgr=rz))
            lgr_choices += [((rz.name, rz.name), rz_member_choices)]
        lgr_choices += [(('Ref. LGR', 'Ref. LGR'), tuple(
            ((str(ref_lgr.to_tuple()), ref_lgr.name) for ref_lgr in RefLgr.objects.all())))]
        return lgr_choices
