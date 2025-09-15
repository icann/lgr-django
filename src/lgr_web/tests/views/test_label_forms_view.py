from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_web.forms import LabelFileFormsForm, LabelFormsForm


class TestLabelForms(LgrWebClientTestBase):
    def setUp(self):
        self.login_user()

    def test_renders_view_with_form(self):
        response = self.client.get('/label_file_forms/')

        self.assertTemplateUsed(response, 'label_forms.html')
        self.assertIsInstance(response.context_data['form'], LabelFormsForm)
        self.assertIsInstance(response.context_data['file_form'], LabelFileFormsForm)

    def test_returns_labels_and_codepoint_sequence(self):
        test_label = 'مكتب'

        response = self.client.post('/label_forms/', {'label': test_label})

        self.assertIn('form', response.context_data)
        self.assertIn('file_form', response.context_data)
        self.assertIn('cp_list', response.context_data)
        self.assertIn('u_label', response.context_data)
        self.assertIn('a_label', response.context_data)
        self.assertEqual(response.context_data['cp_list'], 'U+0645 U+0643 U+062A U+0628')
        self.assertEqual(response.context_data['u_label'], 'مكتب')
        self.assertEqual(response.context_data['a_label'], 'xn--ngbd8eh')

    def test_returns_error_message_for_invalid_punycode(self):
        test_label = 'xn--abcd'

        response = self.client.post('/label_forms/', {'label': test_label})

        self.assertIn('form', response.context_data)
        self.assertIn('file_form', response.context_data)
        self.assertIn('cp_list', response.context_data)
        self.assertIn('u_label', response.context_data)
        self.assertIn('a_label', response.context_data)
        self.assertEqual(response.context_data['cp_list'], 'U+0078 U+006E U+002D U+002D U+0061 U+0062 U+0063 U+0064')
        self.assertEqual(response.context_data['u_label'], '-')
        self.assertEqual(response.context_data['a_label'], '-')
        self.assertContains(response, f'{test_label} is invalid due to invalid Punycode.')

    def test_returns_error_message_for_invalid_label(self):
        test_label = '-invalid'

        response = self.client.post('/label_forms/', {'label': test_label})

        self.assertIn('form', response.context_data)
        self.assertIn('file_form', response.context_data)
        self.assertIn('cp_list', response.context_data)
        self.assertIn('u_label', response.context_data)
        self.assertIn('a_label', response.context_data)
        self.assertEqual(response.context_data['cp_list'], 'U+002D U+0069 U+006E U+0076 U+0061 U+006C U+0069 U+0064')
        self.assertEqual(response.context_data['u_label'], '-')
        self.assertEqual(response.context_data['a_label'], '-')
        self.assertContains(
            response,
            f'{test_label} is invalid due to hyphen restrictions in the RFC5891 as it starts with a hyphen-minus.')

    def test_returns_error_message_for_invalid_input(self):
        test_label = 'ét é'

        response = self.client.post('/label_forms/', {'label': test_label})

        self.assertIn('form', response.context_data)
        self.assertIn('file_form', response.context_data)
        self.assertIn('cp_list', response.context_data)
        self.assertIn('u_label', response.context_data)
        self.assertIn('a_label', response.context_data)
        self.assertEqual(response.context_data['cp_list'], 'U+00E9 U+0074 U+0020 U+00E9')
        self.assertEqual(response.context_data['u_label'], '-')
        self.assertEqual(response.context_data['a_label'], '-')
        self.assertContains(response, f'{test_label} is invalid as it contains disallowed characters.')
