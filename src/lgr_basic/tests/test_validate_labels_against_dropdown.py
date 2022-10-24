from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestValidateLabelsAgainstDropDown(LgrWebClientTestBase):
    test_label = 'مكتب'  # arab character valid since the beginning (rz lgr version 1)
    dropdown_label = 'RZ-LGR 5'
    dropdown_lgr_keys = LgrWebClientTestBase.active_root_zones + ['Reference LGR']

    def test_validate_labels_against_full(self):
        self.login_admin()

        # given
        response = self.client.get('/b/')
        dropdown = response.context['widget']
        form = response.context['form']
        values = form.fields['lgr'].choices
        dropdown_dict = {v[0][0]: v[1][0][0] for v in values}

        # when
        response = self.client.post('/b/',
                                    {'lgr': dropdown_dict[self.dropdown_label], 'collisions': False,
                                     'labels': self.test_label})

        # then
        self.assertEquals('lgr', dropdown['name'])
        self.assertListEqual(list(dropdown_dict.keys()), self.dropdown_lgr_keys)
        self.assertNotContains(response, 'INVALID', status_code=200)
