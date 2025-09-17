from lgr_advanced.lgr_editor.forms import ImportLGRForm
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestImportLGRForm(LgrWebClientTestBase):
    def test_renders_validating_repertoire_in_dropdown(self):
        form = ImportLGRForm()
        dropdown = form.fields['validating_repertoire']
        values = [v[1] for v in dropdown.choices]
        self.assertListEqual(
            values, [''] + sorted(self.active_root_zones + self.active_idna_repertoire + self.active_msr))
