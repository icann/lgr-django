from django.test import SimpleTestCase
from lgr.char import Char, RangeChar

from lgr_renderer.utils import render_glyph


class TestRenderGlyph(SimpleTestCase):
    # TODO: Handle case when provided value is invalid
    def test_renders_char(self):
        char = Char(0x002A)

        result = render_glyph(char)

        self.assertEqual(result, '<bdi>&#x00002A;</bdi>')

    def test_renders_range_char(self):
        char = RangeChar(0x002A, 0x002A, 0x002B)

        result = render_glyph(char)

        self.assertEqual(result, '<bdi>&#x00002A;</bdi> &hellip; <bdi>&#x00002B;</bdi>')
