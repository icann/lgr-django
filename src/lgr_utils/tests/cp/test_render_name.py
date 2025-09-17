from django.test import SimpleTestCase
from lgr.char import Char, RangeChar
from lgr.core import LGR

from lgr_utils.cp import render_name
from lgr_utils.unidb import get_db_by_version


class TestRenderName(SimpleTestCase):
    # TODO: Handle case when provided value is invalid
    def setUp(self):
        self.udata = get_db_by_version(LGR().metadata.unicode_version)

    def test_renders_char_in_html(self):
        char = Char(0x002A)

        result = render_name(char, self.udata)

        self.assertEqual(result, 'ASTERISK')

    def test_renders_range_char_in_html(self):
        char = RangeChar(0x002A, 0x002A, 0x002B)

        result = render_name(char, self.udata)

        self.assertEqual(result, 'ASTERISK &hellip; PLUS SIGN')
