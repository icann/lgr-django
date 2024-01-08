from django.contrib.messages import get_messages
from django.contrib.messages.storage import default_storage
from django.contrib.messages.storage.fallback import FallbackStorage
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import RequestFactory
from django.urls import reverse

from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_web.views import LabelFormsView


class TestLabelForms(LgrWebClientTestBase):
    test_label = 'مكتب'

    def test_label_forms(self):
        self.login_user()

        url = reverse('lgr_label_forms')
        response = self.client.post(url, {'label': self.test_label})

        self.assertIn('form', response.context_data)
        self.assertIn('file_form', response.context_data)
        self.assertIn('cp_list', response.context_data)
        self.assertIn('u_label', response.context_data)
        self.assertIn('a_label', response.context_data)
        self.assertEqual(response.context_data['cp_list'], 'U+0645 U+0643 U+062A U+0628')
        self.assertEqual(response.context_data['u_label'], 'مكتب')
        self.assertEqual(response.context_data['a_label'], 'xn--ngbd8eh')

    def test_label_file_forms(self):
        self.login_user()

        labels_file = SimpleUploadedFile('labels.txt', f'{self.test_label}\nété'.encode('utf-8'),
                                         content_type='text/plain')

        url = reverse('lgr_label_file_forms')
        response = self.client.post(url, {'labels-form-labels': labels_file})

        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(response.content.decode('utf-8-sig'), 'Input,Code point sequence,U-label,A-label,Note\r\n'
                                                               'مكتب,U+0645 U+0643 U+062A U+0628,مكتب,xn--ngbd8eh,-\r\n'
                                                               'été,U+00E9 U+0074 U+00E9,été,xn--t-9fab,-\r\n')

    def test_label_file_forms_invalid_label(self):
        self.login_user()

        labels_file = SimpleUploadedFile('labels.txt', f'-invalid\nxn--abcd\nét é'.encode('utf-8'),
                                         content_type='text/plain')

        url = reverse('lgr_label_file_forms')
        response = self.client.post(url, {'labels-form-labels': labels_file})

        self.assertEqual(response['Content-Type'], 'text/csv')
        self.assertEqual(response.content.decode('utf-8-sig'), 'Input,Code point sequence,U-label,A-label,Note\r\n'
                                                               '-invalid,U+002D U+0069 U+006E U+0076 U+0061 U+006C U+0069 U+0064,-,-,-invalid is invalid due to hypen restrictions in the RFC5891 as it starts with a hyphen-minus.\r\n'
                                                               'xn--abcd,U+0078 U+006E U+002D U+002D U+0061 U+0062 U+0063 U+0064,-,-,xn--abcd is invalid due to invalid Punycode.\r\n'
                                                               'ét é,U+00E9 U+0074 U+0020 U+00E9,-,-,ét é is invalid as it contains disallowed characters.\r\n')

    def test_label_form(self):
        request = RequestFactory().post('lgr_label_forms', data={'label': 'مكتب'})
        view = LabelFormsView()
        view.setup(request)
        view.post(request)

        context = view.get_context_data()

        self.assertEqual(context['cp_list'], 'U+0645 U+0643 U+062A U+0628')
        self.assertEqual(context['u_label'], 'مكتب')
        self.assertEqual(context['a_label'], 'xn--ngbd8eh')

    def test_label_form_idna_error(self):
        request = RequestFactory().post('lgr_label_forms', data={'label': 'xn--abcd'})
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        request._messages = messages
        request._messages = default_storage(request)
        view = LabelFormsView()
        view.setup(request)
        resp = view.post(request)

        context = resp.context_data

        self.assertEqual(context['cp_list'], 'U+0078 U+006E U+002D U+002D U+0061 U+0062 U+0063 U+0064')
        self.assertEqual(context['u_label'], '-')
        self.assertEqual(context['a_label'], '-')
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'xn--abcd is invalid due to invalid Punycode.')

    def test_label_form_unicode_error(self):
        request = RequestFactory().post('lgr_label_forms', data={'label': '-invalid'})
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        request._messages = messages
        request._messages = default_storage(request)
        view = LabelFormsView()
        view.setup(request)
        resp = view.post(request)

        context = resp.context_data

        self.assertEqual(context['cp_list'], 'U+002D U+0069 U+006E U+0076 U+0061 U+006C U+0069 U+0064')
        self.assertEqual(context['u_label'], '-')
        self.assertEqual(context['a_label'], '-')
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]),
                         '-invalid is invalid due to hypen restrictions in the RFC5891 as it starts with a hyphen-minus.')

    def test_label_form_error(self):
        request = RequestFactory().post('lgr_label_forms', data={'label': 'ét é'})
        setattr(request, 'session', 'session')
        messages = FallbackStorage(request)
        setattr(request, '_messages', messages)
        request._messages = messages
        view = LabelFormsView()
        view.setup(request)
        resp = view.post(request)

        context = resp.context_data

        self.assertEqual(context['cp_list'], 'U+00E9 U+0074 U+0020 U+00E9')
        self.assertEqual(context['u_label'], '-')
        self.assertEqual(context['a_label'], '-')
        messages = list(get_messages(request))
        self.assertEqual(len(messages), 1)
        self.assertEqual(str(messages[0]), 'ét é is invalid as it contains disallowed characters.')
