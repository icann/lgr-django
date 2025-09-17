from unittest import TestCase

from lgr_models.models.lgr import RzLgr
from lgr_models.utils import get_model_from_name


class TestGetModelFromName(TestCase):
    # TODO: Handle when name does not match a model
    # TODO: Handle when providing anything but a string or a Model
    def test_returns_model_class_when_string_is_provided(self):
        model_name = 'lgr_models.RzLgr'

        result = get_model_from_name(model_name)

        self.assertEqual(result, RzLgr)

    def test_returns_self_when_class_is_provided(self):
        model = RzLgr

        result = get_model_from_name(model)

        self.assertEqual(result, RzLgr)
