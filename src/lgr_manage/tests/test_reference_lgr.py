from http import HTTPStatus
from io import BytesIO

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from lgr_models.models.lgr import RefLgr, RefLgrMember
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase

MIN_LGR = """<?xml version='1.0' encoding='utf-8'?>
<lgr xmlns="urn:ietf:params:xml:ns:lgr-1.0">
  <meta>
    <version>1</version>
    <unicode-version>6.3.0</unicode-version>
  </meta>
  <data>
  </data>
  <rules/>
</lgr>""".encode('utf-8')


class RefLgrActiveTestCase(LgrWebClientTestBase):

    def setUp(self):
        super().setUp()
        self.default_ref = RefLgr.objects.get(active=True)
        self.ref_lgr = RefLgr.objects.create(name='Ref. LGR',
                                             file=File(BytesIO(MIN_LGR), name='Ref. LGR'))
        self.ref_member = RefLgrMember.objects.create(name='Ref. LGR member',
                                                      language_script='und-Latn',
                                                      file=File(BytesIO(MIN_LGR), name='Ref. LGR member'),
                                                      language='und',
                                                      script='Latn',
                                                      ref_lgr=self.ref_lgr)

    def test_access_active_when_logged_in(self):
        self.login_admin()

        response = self.client.get('/m/ref-lgr')
        self.assertContains(response,
                            '<form class="form-horizontal" id="active-choice-form" url-data="/m/ref-lgr/isactive">',
                            status_code=HTTPStatus.OK)

    def test_access_active_when_icann_user(self):
        self.login_icann()

        response = self.client.get('/m/ref-lgr')
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

    def test_access_active_when_user(self):
        self.login_user()

        response = self.client.get('/m/ref-lgr')
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

    def test_access_active_when_not_logged_in(self):
        response = self.client.get('/m/ref-lgr')
        self.assertEquals(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, '/auth/login/?next=/m/ref-lgr')

    def test_update_active_when_logged_in(self):
        self.login_admin()
        response = self.client.post('/m/ref-lgr/isactive', data={'active': self.ref_lgr.pk})
        self.assertContains(response, f'"old_active": {self.default_ref.pk}', status_code=HTTPStatus.OK)
        self.assertEquals(RefLgr.objects.get(active=True).pk, self.ref_lgr.pk)

    def test_update_active_when_icann_user(self):
        self.login_icann()

        response = self.client.post('/m/ref-lgr/isactive', data={'active': 2})
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_update_active_when_user(self):
        self.login_user()

        response = self.client.post('/m/ref-lgr/isactive', data={'active': 2})
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_update_active_when_not_logged_in(self):
        response = self.client.post('/m/ref-lgr/isactive', data={'active': 2})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, '/auth/login/?next=/m/ref-lgr/isactive')

    def test_create_when_logged_in(self):
        self.login_admin()

        self.client.post(reverse('lgr_admin_ref_lgr'), data={
            'name': 'Test Ref. LGR',
            'file': SimpleUploadedFile('ref-lgr.xml', MIN_LGR, content_type='text/xml'),
            'members': [SimpleUploadedFile('ref-lgr-1.xml', MIN_LGR, content_type='text/xml'),
                        SimpleUploadedFile('ref-lgr-2.xml', MIN_LGR, content_type='text/xml')],
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 0,
            'form-0-file_name': 'ref-lgr-1.xml',
            'form-0-language_script': 'fr-Latn',
            'form-1-file_name': 'ref-lgr-2.xml',
            'form-1-language_script': 'it-Latn',
        })
        self.assertTrue(RefLgr.objects.filter(name='Test Ref. LGR').exists())
        ref: RefLgr = RefLgr.objects.get(name='Test Ref. LGR')
        self.assertListEqual(list(ref.repository.values_list('name', flat=True)),
                             ['Test Ref. LGR-ref-lgr-1', 'Test Ref. LGR-ref-lgr-2'])
        self.assertListEqual(list(ref.repository.values_list('language_script', flat=True)),
                             ['fr-Latn', 'it-Latn'])
        self.assertListEqual(list(ref.repository.values_list('language', flat=True)),
                             ['fr', 'it'])
        self.assertListEqual(list(ref.repository.values_list('script', flat=True)),
                             ['Latn', 'Latn'])

    def test_create_when_icann_user(self):
        self.login_icann()

        response = self.client.post(reverse('lgr_admin_ref_lgr'), data={})
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_create_when_user(self):
        self.login_user()

        response = self.client.post(reverse('lgr_admin_ref_lgr'), data={})
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_create_when_not_logged_in(self):
        response = self.client.post(reverse('lgr_admin_ref_lgr'), data={})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, '/auth/login/?next=/m/ref-lgr')

    def test_update_when_logged_in(self):
        self.login_admin()
        url = reverse('lgr_admin_update_ref_lgr', kwargs={'lgr_pk': self.ref_member.pk})

        self.client.post(url, data={'language_script': 'ar-Arab'})

        self.assertListEqual(list(self.ref_lgr.repository.values_list('language_script', flat=True)),
                             ['ar-Arab'])

    def test_update_when_icann_user(self):
        self.login_icann()
        url = reverse('lgr_admin_update_ref_lgr', kwargs={'lgr_pk': self.ref_member.pk})

        response = self.client.post(url, data={})

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_update_when_user(self):
        self.login_user()
        url = reverse('lgr_admin_update_ref_lgr', kwargs={'lgr_pk': self.ref_member.pk})

        response = self.client.post(url, data={})

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_update_when_not_logged_in(self):
        url = reverse('lgr_admin_update_ref_lgr', kwargs={'lgr_pk': self.ref_member.pk})

        response = self.client.post(url, data={})

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, f'/auth/login/?next={url}')

    def test_delete_when_logged_in(self):
        self.login_admin()
        url = reverse('lgr_admin_delete_ref_lgr', kwargs={'lgr_pk': self.ref_lgr.pk})

        self.client.post(url)

        self.assertFalse(RefLgr.objects.filter(pk=self.ref_lgr.pk).exists())

    def test_delete_when_icann_user(self):
        self.login_icann()
        url = reverse('lgr_admin_delete_ref_lgr', kwargs={'lgr_pk': self.ref_lgr.pk})

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_delete_when_user(self):
        self.login_user()
        url = reverse('lgr_admin_delete_ref_lgr', kwargs={'lgr_pk': self.ref_lgr.pk})

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_delete_when_not_logged_in(self):
        url = reverse('lgr_admin_delete_ref_lgr', kwargs={'lgr_pk': self.ref_lgr.pk})

        response = self.client.post(url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, f'/auth/login/?next={url}')

    def test_delete_active_reference(self):
        # set ref_lgr active
        self.test_update_active_when_logged_in()
        #  sanity check
        self.default_ref.refresh_from_db()
        self.assertFalse(self.default_ref.active)
        # then delete the active ref lgr
        self.test_delete_when_logged_in()

        # expect default LGR to be active again
        self.default_ref.refresh_from_db()
        self.assertTrue(self.default_ref.active)

    def test_set_first_active(self):
        RefLgr.objects.all().delete()
        #  sanity checks
        self.assertEquals(RefLgrMember.objects.count(), 0)
        self.assertFalse(RefLgr.objects.filter(active=True).exists())

        self.test_create_when_logged_in()
        self.assertEqual(RefLgr.objects.count(), 1)
        self.assertTrue(RefLgr.objects.filter(active=True).exists())
