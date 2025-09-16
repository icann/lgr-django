from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestBasicModeView(LgrWebClientTestBase):
    #TODO: Add coverage when providing `labels_file` and `collisions`
    def setUp(self):
        self.test_label = 'مكتب'  # Arab character valid since the beginning (rz lgr version 1)
        self.dropdown_label = 'RZ-LGR 5'
        self.dropdown_lgr_keys = LgrWebClientTestBase.active_root_zones + ['Reference LGR']
        self.login_admin()

    def test_validates_labels_against_dropdown(self):
        response = self.client.get('/b/')
        dropdown = response.context['widget']
        form = response.context['form']
        values = form.fields['lgr'].choices
        dropdown_dict = {v[0][0]: v[1][0][0] for v in values}

        response = self.client.post(
            '/b/',
            {'lgr': dropdown_dict[self.dropdown_label], 'collisions': False, 'labels': self.test_label})

        self.assertEquals('lgr', dropdown['name'])
        self.assertListEqual(list(dropdown_dict.keys()), self.dropdown_lgr_keys)
        self.assertNotContains(response, 'INVALID', status_code=200)
