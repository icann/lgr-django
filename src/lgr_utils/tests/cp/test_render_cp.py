from django.test import SimpleTestCase
from lgr.char import Char, RangeChar

from lgr_utils.cp import render_cp


class TestRenderCP(SimpleTestCase):
    # TODO: Handle case when provided value is invalid
    def test_renders_codepoint_for_char(self):
        char = Char(0x002A)

        result = render_cp(char)

        self.assertEqual(result, 'U+002A')

    def test_renders_codepoints_for_range_char(self):
        char = RangeChar(0x002A, 0x002A, 0x002B)

        result = render_cp(char)

        self.assertEqual(result, 'U+002A &hellip; U+002B')
