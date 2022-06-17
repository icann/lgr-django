from lgr_basic.forms import ValidateLabelSimpleForm
from lgr_models.models.lgr import RzLgr
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestValidateLabelsAgainstDropDown(LgrWebClientTestBase):
    test_label = 'مكتب'  # arab character valid since the beginning (rz lgr version 1)
    dropdown_label = 'RZ-LGR 4'
    dropdown_lgr_keys = LgrWebClientTestBase.default_root_zones + ['Ref. LGR']

    def test_validate_labels_against_full(self):
        self.login_admin()

        # given
        response = self.client.get('/b/')
        dropdown = response.context['widget']
        form = response.context['form']
        values = form.fields['rz_lgr'].choices
        dropdown_dict = {v[0][0]:v[1][0][0] for v in values}

        # when
        response = self.client.post('/b/',
                                    {'rz_lgr': dropdown_dict[self.dropdown_label], 'collisions': False,
                                     'labels': self.test_label})

        # then
        self.assertEquals('rz_lgr', dropdown['name'])
        self.assertListEqual(list(dropdown_dict.keys()), self.dropdown_lgr_keys)
        self.assertNotContains(response, 'INVALID', status_code=200)

    def test_validate_labels_against(self):
        dropdown = ValidateLabelSimpleForm()
        values = [v[0][0] for v in dropdown.fields['rz_lgr'].choices]
        self.assertListEqual(values, self.dropdown_lgr_keys)
