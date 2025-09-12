from django.test import TestCase
from lgr.core import LGR

from lgr_models.models.lgr import RzLgr


class TestRZLGR(TestCase):
    def test_converts_model_instance_to_core_lgr_instance(self):
        rz_lgr: RzLgr = RzLgr.objects.first()

        lgr = rz_lgr.to_lgr()

        self.assertEqual(lgr.name, 'RZ-LGR 1')
        self.assertIsInstance(lgr, LGR)
