from unittest import TestCase

from django.http import Http404

from lgr_models.models.lgr import RzLgr
from lgr_models.utils import get_model_from_url_name


class TestGetModelFromName(TestCase):
    # TODO: Handle when name does not match a model
    # TODO: Handle when providing anything but a string
    def test_returns_model_class_when_string_is_provided(self):
        model_name = 'RzLgr'

        result = get_model_from_url_name(model_name)

        self.assertEqual(result, RzLgr)

    def test_raise_http_404_when_no_model_match_name(self):
        model_name = 'Invalid'

        with self.assertRaises(Http404):
            get_model_from_url_name(model_name)
