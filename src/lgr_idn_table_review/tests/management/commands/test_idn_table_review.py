import os

from lgr_idn_table_review.management.commands.idn_table_review import idn_table_review
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestIDNTableReview(LgrWebClientTestBase):
    # TODO: Handle case when xml file is invalid
    # TODO: review_lgr() from lgr-core has no unit tests to cover
    #       the content of the output
    def setUp(self):
        self.output_file = './test_result.html'

    def tearDown(self):
        if os.path.exists(self.output_file):
            os.remove(self.output_file)

    def test_returns_review_results_in_html_file(self):
        # TODO: Use better files for the tests
        idn_table = 'src/lgr_web/resources/idn_ref/root-zone/lgr-5-common-26may22-en.xml'
        reference_lgr = 'src/lgr_web/resources/idn_ref/root-zone/lgr-5-common-26may22-en.xml'

        idn_table_review(idn_table, reference_lgr=reference_lgr, output=self.output_file)

        self.assertTrue(os.path.exists(self.output_file))
