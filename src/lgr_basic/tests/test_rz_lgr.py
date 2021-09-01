from django.test import TestCase

from lgr_models.models.lgr import RzLgr


class TestRzLgr(TestCase):

    def test_to_lgr_info(self):
        rz_lgr: RzLgr = RzLgr.objects.first()
        lgr = rz_lgr.to_lgr()
        self.assertEqual('RZ-LGR 1', lgr.name)
