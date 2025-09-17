from django.test import SimpleTestCase

from lgr_utils.cp import cp_to_slug


class TestCPtoSlug(SimpleTestCase):
    def test_returns_codepoint_in_string_format(self):
        codepoint = (1568, 1569)

        result = cp_to_slug(codepoint)

        self.assertEqual(result, '1568-1569')
