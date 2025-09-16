import os

from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_renderer.api import render_html


class TestRenderHTML(LgrWebClientTestBase):
    # TODO: Handle case when xml file is invalid
    def setUp(self):
        self.output_file = './test_result.html'

    def tearDown(self):
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def test_returns_lgr_context_in_html_file(self):
        xml_file = 'src/lgr_web/resources/idn_ref/root-zone/lgr-5-common-26may22-en.xml'
        output_file = './test_result.html'

        render_html(xml_file, validate=False, output=output_file)

        self.assertTrue(os.path.exists(self.output_file))
