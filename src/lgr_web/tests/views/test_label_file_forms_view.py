from django.core.files.uploadedfile import SimpleUploadedFile

from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_web.forms import LabelFileFormsForm, LabelFormsForm


class TestLabelFileForms(LgrWebClientTestBase):
    def setUp(self):
        self.login_user()

    def test_renders_view_with_form(self):
        response = self.client.get('/label_file_forms/')

        self.assertTemplateUsed(response, 'label_forms.html')
        self.assertIsInstance(response.context_data['form'], LabelFormsForm)
        self.assertIsInstance(response.context_data['file_form'], LabelFileFormsForm)

    def test_generates_csv_file_from_list_of_label(self):
        test_label = 'مكتب'
        labels_file = SimpleUploadedFile(
            'labels.txt', f'{test_label}\nété'.encode('utf-8'), content_type='text/plain')

        response = self.client.post('/label_file_forms/', {'labels-form-labels': labels_file})

        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(
            response.content.decode('utf-8-sig'),
            'Input,Code point sequence,U-label,A-label,Note\r\n'
            'مكتب,U+0645 U+0643 U+062A U+0628,مكتب,xn--ngbd8eh,-\r\n'
            'été,U+00E9 U+0074 U+00E9,été,xn--t-9fab,-\r\n')

    def test_generates_csv_file_with_validation_error_in_notes_of_invalid_label(self):
        labels_file = SimpleUploadedFile(
            'labels.txt', f'-invalid\nxn--abcd\nét é'.encode('utf-8'),
            content_type='text/plain')

        response = self.client.post('/label_file_forms/', {'labels-form-labels': labels_file})

        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(
            response.content.decode('utf-8-sig'),
            'Input,Code point sequence,U-label,A-label,Note\r\n'
            '-invalid,U+002D U+0069 U+006E U+0076 U+0061 U+006C U+0069 U+0064,-,-,-invalid is invalid due to hyphen restrictions in the RFC5891 as it starts with a hyphen-minus.\r\n'
            'xn--abcd,U+0078 U+006E U+002D U+002D U+0061 U+0062 U+0063 U+0064,-,-,xn--abcd is invalid due to invalid Punycode.\r\n'
            'ét é,U+00E9 U+0074 U+0020 U+00E9,-,-,ét é is invalid as it contains disallowed characters.\r\n')
