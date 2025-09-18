from lgr_advanced.lgr_editor.forms import MetadataForm
from lgr_models.models.lgr import RzLgr
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestMetadataView(LgrWebClientTestBase):
    def setUp(self):
        self.instance = RzLgr.objects.first()
        self.instance_metadata = self.instance.to_lgr().metadata
        self.login_admin()

    def test_renders_model_instance_metadata(self):
        response = self.client.get('/a/editor/{}/{}/metadata/'.format('rzlgr', self.instance.pk))
        form_initial_data = response.context_data['form'].initial

        self.assertTemplateUsed(response, 'lgr_editor/metadata.html')
        self.assertIsInstance(response.context_data['form'], MetadataForm)
        self.assertEqual(response.context_data['home_url_name'], 'lgr_advanced_mode')
        self.assertEqual(response.context_data['lgr_pk'], self.instance.pk)
        self.assertEqual(response.context_data['lgr_object'], self.instance)
        self.assertEqual(form_initial_data['version'], self.instance_metadata.version.value)
        self.assertEqual(form_initial_data['version_comment'], self.instance_metadata.version.comment)
        self.assertEqual(form_initial_data['date'], self.instance_metadata.date)
        self.assertEqual(form_initial_data['language'], self.instance_metadata.languages[0])
        self.assertEqual(form_initial_data['scope'], self.instance_metadata.scopes[0].value)
        self.assertEqual(form_initial_data['scope_type'], self.instance_metadata.scopes[0].scope_type)
        self.assertEqual(form_initial_data['unicode_version'], self.instance_metadata.unicode_version)
        self.assertEqual(form_initial_data['validity_start'], self.instance_metadata.validity_start)
        self.assertEqual(form_initial_data['validity_end'], self.instance_metadata.validity_end)
        self.assertEqual(form_initial_data['description'], self.instance_metadata.description.value)
        self.assertEqual(form_initial_data['description_type'], self.instance_metadata.description.description_type)
        self.assertEqual(form_initial_data['validating_repertoire'], [('', '')])
