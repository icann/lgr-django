from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestImportLGRView(LgrWebClientTestBase):
    def test_validating_repertoire_import_full(self):
        self.login_admin()

        response = self.client.get('/a/editor/import/')
        dropdown = response.context['form'].fields['validating_repertoire']
        values = [v[1] for v in dropdown.choices]
        self.assertListEqual(
            values, [''] + sorted(self.active_root_zones + self.active_idna_repertoire + self.active_msr))

        with open('src/lgr_web/resources/idn_ref/root-zone/lgr-4-common-05nov20-en.xml', 'rb') as fp:
            response = self.client.post('/a/editor/import/',
                                        {'validating_repertoire': values[1],
                                         'encoding': 'utf-8',
                                         'file': fp}, follow=True)
        self.assertNotContains(response, 'Cannot import LGR file(s)', status_code=200)

    def test_validating_repertoire_create_full(self):
        self.login_admin()

        response = self.client.get('/a/editor/new/')
        dropdown = response.context['form'].fields['validating_repertoire']
        values = [v[1] for v in dropdown.choices]
        self.assertListEqual(
            values, [''] + sorted(self.active_root_zones + self.active_idna_repertoire + self.active_msr))

        response = self.client.post('/a/editor/new/',
                                    {'validating_repertoire': values[1],
                                     'unicode_version': '6.3.0',
                                     'name': 'test'}, follow=True)
        self.assertNotContains(response, 'Cannot import LGR file(s)', status_code=200)
