from http import HTTPStatus
from io import BytesIO

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse

from lgr_manage.tests.test_views_common import MIN_LGR, AdminLgrTestCase
from lgr_models.models.lgr import RefLgr, RefLgrMember


class RefLgrTestCase(AdminLgrTestCase):
    model = RefLgr
    base_view_name = 'lgr_admin_ref_lgr'
    active_view_name = 'lgr_admin_isactive_ref_lgr'
    delete_view_name = 'lgr_admin_delete_ref_lgr'

    def setUp(self):
        super().setUp()
        self.ref_member1 = RefLgrMember.objects.create(name='ref_lgr_member1',
                                                       language_script='und-Latn',
                                                       file=File(BytesIO(MIN_LGR), name='ref_lgr_member1'),
                                                       language='und',
                                                       script='Latn',
                                                       common=self.other)
        self.ref_member2 = RefLgrMember.objects.create(name='ref_lgr_member2',
                                                       language_script='und-Latn',
                                                       file=File(BytesIO(MIN_LGR), name='ref_lgr_member2'),
                                                       language='und',
                                                       script='Latn',
                                                       common=self.other)

    def get_create_body(self):
        return {
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
        }

    def test_create_when_logged_in(self):
        super().test_create_when_logged_in()

        ref: RefLgr = RefLgr.objects.get(name='Test Ref. LGR')
        self.assertListEqual(list(ref.repository.values_list('name', flat=True)),
                             ['ref-lgr-1', 'ref-lgr-2'])
        self.assertListEqual(list(ref.repository.values_list('language_script', flat=True)),
                             ['fr-Latn', 'it-Latn'])
        self.assertListEqual(list(ref.repository.values_list('language', flat=True)),
                             ['fr', 'it'])
        self.assertListEqual(list(ref.repository.values_list('script', flat=True)),
                             ['Latn', 'Latn'])

    def test_update_when_logged_in(self):
        self.login_admin()
        url = reverse('lgr_admin_update_ref_lgr', kwargs={'lgr_pk': self.ref_member1.pk})

        self.client.post(url, data={'language_script': 'ar-Arab'})

        self.ref_member1.refresh_from_db()
        self.assertEquals(self.ref_member1.language_script, 'ar-Arab')

    def test_update_duplicate_member(self):
        self.login_admin()
        url = reverse('lgr_admin_update_ref_lgr', kwargs={'lgr_pk': self.ref_member1.pk})

        response = self.client.post(url, data={'file': File(BytesIO(MIN_LGR), name=self.ref_member2.name),
                                               'language_script': 'hebr'})

        self.assertContains(response, "Failed to update Reference LGR member", status_code=HTTPStatus.OK)
        self.assertContains(response, "This reference LGR member already exists", status_code=HTTPStatus.OK)
        self.ref_member1.refresh_from_db()
        self.assertEquals(self.ref_member1.language_script, 'und-Latn')

    def test_update_overwrite_member(self):
        """
        Same as duplicate but this time we upload a file with the same name as the one we are updating, this should
        overwrite
        """
        self.login_admin()
        url = reverse('lgr_admin_update_ref_lgr', kwargs={'lgr_pk': self.ref_member1.pk})

        self.client.post(url, data={'file': File(BytesIO(MIN_LGR), name='ref_lgr_member1'),
                                    'language_script': 'jp'})

        self.ref_member1.refresh_from_db()
        self.assertEquals(self.ref_member1.name, 'ref_lgr_member1')
        self.assertEquals(self.ref_member1.language_script, 'jp')

    def test_update_when_icann_user(self):
        self.login_icann()
        url = reverse('lgr_admin_update_ref_lgr', kwargs={'lgr_pk': self.ref_member1.pk})

        response = self.client.post(url, data={})

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_update_when_user(self):
        self.login_user()
        url = reverse('lgr_admin_update_ref_lgr', kwargs={'lgr_pk': self.ref_member1.pk})

        response = self.client.post(url, data={})

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_update_when_not_logged_in(self):
        url = reverse('lgr_admin_update_ref_lgr', kwargs={'lgr_pk': self.ref_member1.pk})

        response = self.client.post(url, data={})

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, f'/auth/login/?next={url}')

    def test_delete_when_logged_in(self):
        super().test_delete_when_logged_in()
        self.assertFalse(RefLgrMember.objects.filter(common=self.other.pk).exists())
