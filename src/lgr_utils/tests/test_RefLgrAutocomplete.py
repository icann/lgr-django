from unittest.mock import patch

from lgr_utils.views import RefLgrAutocomplete
from django.test import SimpleTestCase
from lgr_utils.tests.ModelMocks import RefLgrMemberMock, RzLgrMock, RefLgrMock, MockListExpected


class test_RefLgrAutocomplete_building(SimpleTestCase):

    # TODO : Improve the tests with fixtures
    # https://docs.djangoproject.com/en/dev/topics/testing/tools/#fixture-loading
    # https://docs.djangoproject.com/en/dev/topics/testing/tools/#provided-test-case-classes
    # https://docs.djangoproject.com/en/dev/internals/contributing/writing-code/unit-tests/#tips-for-writing-tests

    @patch("lgr_models.models.lgr.RefLgr.objects", RefLgrMock())
    @patch("lgr_models.models.lgr.RefLgrMember.objects", RefLgrMemberMock())
    @patch("lgr_models.models.lgr.RzLgr.objects", RzLgrMock())
    def test_normalRefLgrAutocomplete(self):
        response = RefLgrAutocomplete.get_list();
        self.assertEqual(response, MockListExpected)
