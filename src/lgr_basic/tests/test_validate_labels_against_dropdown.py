from lgr_basic.forms import ValidateLabelSimpleForm
from tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestValidateLabelsAgainstDropDown(LgrWebClientTestBase):
    test_label = 'ب'  # arab character valid since the beginning (rz lgr version 1)
    dropdown_label = 'RZ-LGR 4'
    dropdown_labels = ['RZ-LGR 4']

    def test_validate_labels_against_full(self):
        self.login()

        response = self.client.get('/b/')
        dropdown = response.context['widget']
        self.assertEquals('rz_lgr', dropdown['name'])
        dropdown_dict = {v[1][0]['label']: v[1][0]['value'] for v in dropdown['optgroups']}
        self.assertListEqual(list(dropdown_dict.keys()), self.dropdown_labels)

        response = self.client.post('/b/',
                                    {'rz_lgr': dropdown_dict[self.dropdown_label], 'collisions': False,
                                     'labels': self.test_label})
        self.assertNotContains(response, 'INVALID', status_code=200)

    def test_validate_labels_against(self):
        dropdown = ValidateLabelSimpleForm()
        values = [v[1] for v in dropdown.fields['rz_lgr'].choices]
        self.assertListEqual(values, self.dropdown_labels)
