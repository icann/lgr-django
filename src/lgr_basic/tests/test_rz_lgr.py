from django.test import TestCase

from lgr_models.models import RzLgr


class TestRzLgr(TestCase):

    def test_to_lgr_info(self):
        rz_lgr: RzLgr = RzLgr.objects.first()
        lgr_info = rz_lgr.to_lgr_info()
        self.assertTrue('Label Generation Rules for the Root Zone' in lgr_info.xml)
