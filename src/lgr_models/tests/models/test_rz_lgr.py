from lgr.core import LGR

from lgr_models.models.lgr import RzLgr
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestRZLGR(LgrWebClientTestBase):
    def test_converts_model_instance_to_core_lgr_instance(self):
        rz_lgr: RzLgr = RzLgr.objects.first()

        lgr = rz_lgr.to_lgr()

        self.assertEqual(lgr.name, 'RZ-LGR 1')
        self.assertIsInstance(lgr, LGR)

    def test_default_root_zones_list(self):
        rz_lgrs = list(RzLgr.objects.all().values_list('name', flat=True))

        active_rz_lgrs = list(RzLgr.objects.filter(active=True).values_list('name', flat=True))

        self.assertListEqual(rz_lgrs, self.default_root_zones)
        self.assertListEqual(active_rz_lgrs, self.active_root_zones)
