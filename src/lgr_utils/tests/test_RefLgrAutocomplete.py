from unittest.mock import patch

from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_utils.views import RefLgrAutocomplete
from lgr_utils.tests.ModelMocks import RefLgrMemberMock, RzLgrMock, RefLgrMock, MockListExpected


class MyTestCase(LgrWebClientTestBase):

    @patch("lgr_models.models.lgr.RefLgr.objects", RefLgrMock())
    @patch("lgr_models.models.lgr.RefLgrMember.objects", RefLgrMemberMock())
    @patch("lgr_models.models.lgr.RzLgr.objects", RzLgrMock())
    def test_normalRefLgrAutocomplete(self):

        response = RefLgrAutocomplete.get_list();
        self.assertEqual(response, MockListExpected)
