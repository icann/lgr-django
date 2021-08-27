from lgr_models.tests.test_unicode_version import TestUnicodeVersion


class TestLabelFormsView(TestUnicodeVersion):

    def test_unicode_versions(self):
        self.login()

        self.a_unicode_version.activated = True
        self.a_unicode_version.save()
        response = self.client.get('/a/label_forms/')
        self.assertEqual(response.context['option']['value'], self.a_unicode_version.version)
