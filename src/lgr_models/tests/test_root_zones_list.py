from lgr_models.models.lgr import RzLgr
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestRootZoneList(LgrWebClientTestBase):

    def test_default_root_zones_list(self):
        rz_lgrs = list(RzLgr.objects.all().values_list('name', flat=True))
        self.assertListEqual(rz_lgrs, self.default_root_zones)
