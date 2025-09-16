from lgr_models.models.lgr import RzLgr
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_renderer.api import generate_context


class TestGenerateContext(LgrWebClientTestBase):
    def test_returns_lgr_context(self):
        # TODO: We should do more assertions on the outputs by using a
        #       smaller LGR made for testing
        lgr = RzLgr.objects.first().to_lgr()

        result = generate_context(lgr)

        self.assertEqual(result['name'], 'RZ-LGR 1')
        self.assertIn('stats', result)
        self.assertEqual(result['main_language'], 'und-Zyyy')
        self.assertIn('metadata', result)
        self.assertEqual(result['description'], lgr.metadata.description.value)
        self.assertEqual(result['description_type'], 'text/html')
        self.assertIn('repertoire', result)
        self.assertIn('variant_sets', result)
        self.assertIn('classes', result)
        self.assertIn('actions', result)
        self.assertIn('rules', result)
        self.assertIn('references', result)
