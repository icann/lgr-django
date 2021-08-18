from lgr_advanced.lgr_editor.forms import ImportLGRForm
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestValidatingRepertoire(LgrWebClientTestBase):
    test_label = 'ب'  # arab character valid since the beginning (rz lgr version 1)
    dropdown_label = 'RZ-LGR 4'
    dropdown_labels = ['RZ-LGR 4']

    def test_validating_repertoire(self):
        dropdown = ImportLGRForm()
        values = [v[1] for v in dropdown.fields['validating_repertoire'].choices]
        self.assertListEqual(values, self.dropdown_labels)

    def test_validating_repertoire_full(self):
        self.login()

        response = self.client.get('/a/editor/import/')
        dropdown = response.context['form'].fields['validating_repertoire']
        values = [v[1] for v in dropdown.choices if v[1]]
        self.assertListEqual(values, self.dropdown_labels)
        with open('src/lgr_web/resources/repertoires/lgr-4-common-05nov20-en.xml', 'rb') as fp:
            response = self.client.post('/a/editor/import/',
                                        {'validating_repertoire': values[0],
                                         'encoding': 'utf-8',
                                         'file': fp}, follow=True)
        self.assertNotContains(response, 'Cannot import LGR file(s)', status_code=200)
