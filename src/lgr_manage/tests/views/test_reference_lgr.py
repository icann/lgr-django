import os
from http import HTTPStatus
from io import BytesIO

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile

from lgr_manage.tests.views.utils import MIN_LGR
from lgr_models.models.lgr import RefLgr, RefLgrMember
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestRefLgrCreateView(LgrWebClientTestBase):
    model = RefLgr
    base_url = '/m/ref-lgr'

    @staticmethod
    def get_create_body():
        return {
            'name': 'Test Ref. LGR',
            'file': SimpleUploadedFile('ref-lgr.xml', MIN_LGR, content_type='text/xml'),
            'members': [
                SimpleUploadedFile('ref-lgr-1.xml', MIN_LGR, content_type='text/xml'),
                SimpleUploadedFile('ref-lgr-2.xml', MIN_LGR, content_type='text/xml')],
            'form-TOTAL_FORMS': 2,
            'form-INITIAL_FORMS': 0,
            'form-0-file_name': 'ref-lgr-1.xml',
            'form-0-language_script': 'fr-Latn',
            'form-1-file_name': 'ref-lgr-2.xml',
            'form-1-language_script': 'it-Latn'
        }

    def setUp(self):
        super().setUp()
        self.model.objects.all().delete()

    def tearDown(self):
        for instance in self.model.objects.all():
            os.remove(instance.file.path)

    def test_creates_when_logged_in_as_admin(self):
        self.login_admin()
        create_body = self.get_create_body()

        self.client.post(self.base_url, data=create_body)

        created_instance = self.model.objects.get(name=create_body['name'])
        self.assertListEqual(
            list(created_instance.repository.values_list('name', flat=True)),
            ['ref-lgr-1', 'ref-lgr-2'])
        self.assertListEqual(
            list(created_instance.repository.values_list('language_script', flat=True)),
            ['fr-Latn', 'it-Latn'])
        self.assertListEqual(
            list(created_instance.repository.values_list('language', flat=True)),
            ['fr', 'it'])
        self.assertListEqual(
            list(created_instance.repository.values_list('script', flat=True)),
            ['Latn', 'Latn'])

    def test_set_first_active(self):
        self.model.objects.all().delete()

        self.test_creates_when_logged_in_as_admin()

        self.assertEqual(self.model.objects.count(), 1)
        self.assertTrue(self.model.objects.filter(active=True).exists())

    def test_cannot_create_as_icann_user(self):
        self.login_icann()

        response = self.client.post(self.base_url, data={})

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_cannot_create_as_regular_user(self):
        self.login_user()

        response = self.client.post(self.base_url, data={})

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_cannot_create_when_not_logged_in(self):
        response = self.client.post(self.base_url, data={})

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, f'/auth/login/?next={self.base_url}')


class TestRefLgrDeleteView(LgrWebClientTestBase):
    model = RefLgr
    base_url = '/m/ref-lgr'

    def setUp(self):
        super().setUp()
        self.model.objects.exclude(active=True).delete()
        self.default_active = self.model.objects.get(active=True)
        self.other_instance = self.model.objects.create(name='Other', file=File(BytesIO(MIN_LGR), name='other.xml'))
        self.ref_member1 = RefLgrMember.objects.create(
            name='ref_lgr_member1',
            language_script='und-Latn',
            file=File(BytesIO(MIN_LGR), name='ref_lgr_member1'),
            language='und',
            script='Latn',
            common=self.other_instance)
        self.ref_member2 = RefLgrMember.objects.create(
            name='ref_lgr_member2',
            language_script='und-Latn',
            file=File(BytesIO(MIN_LGR), name='ref_lgr_member2'),
            language='und',
            script='Latn',
            common=self.other_instance)
        self.delete_url = f'{self.base_url}/{self.other_instance.id}/delete'

    def tearDown(self):
        for instance in self.model.objects.exclude(active=True):
            os.remove(instance.file.path)

    def test_delete_when_logged_in_as_admin(self):
        self.login_admin()

        self.client.post(self.delete_url)

        self.assertFalse(self.model.objects.filter(pk=self.other_instance.pk).exists())
        self.assertFalse(RefLgrMember.objects.filter(common=self.other_instance.pk).exists())

    def test_cannot_delete_as_icann_user(self):
        self.login_icann()

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTrue(self.model.objects.filter(pk=self.other_instance.pk).exists())

    def test_cannot_delete_as_regular_user(self):
        self.login_user()

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTrue(self.model.objects.filter(pk=self.other_instance.pk).exists())

    def test_cannot_delete_when_not_logged_in(self):
        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, f'/auth/login/?next={self.delete_url}')
        self.assertTrue(self.model.objects.filter(pk=self.other_instance.pk).exists())

    def test_delete_active_reference(self):
        self.login_admin()
        self.other_instance.active = True
        self.other_instance.save()
        self.default_active.active = False
        self.default_active.save()

        self.client.post(self.delete_url)

        self.default_active.refresh_from_db()
        self.assertTrue(self.default_active.active)


class TestRefLgrUpdateView(LgrWebClientTestBase):
    model = RefLgr
    base_url = '/m/ref-lgr'

    def setUp(self):
        super().setUp()
        self.model.objects.exclude(active=True).delete()
        self.default_active = self.model.objects.get(active=True)
        self.other_instance = self.model.objects.create(name='Other', file=File(BytesIO(MIN_LGR), name='other.xml'))
        self.ref_member1 = RefLgrMember.objects.create(
            name='ref_lgr_member1',
            language_script='und-Latn',
            file=File(BytesIO(MIN_LGR), name='ref_lgr_member1'),
            language='und',
            script='Latn',
            common=self.other_instance)
        self.ref_member2 = RefLgrMember.objects.create(
            name='ref_lgr_member2',
            language_script='und-Latn',
            file=File(BytesIO(MIN_LGR), name='ref_lgr_member2'),
            language='und',
            script='Latn',
            common=self.other_instance)
        self.update_url = f'{self.base_url}/{self.ref_member1.pk}/update'

    def tearDown(self):
        for instance in self.model.objects.exclude(active=True):
            os.remove(instance.file.path)

    def test_update_when_logged_in_as_admin(self):
        self.login_admin()

        self.client.post(self.update_url, data={'language_script': 'ar-Arab'})

        self.ref_member1.refresh_from_db()
        self.assertEqual(self.ref_member1.language_script, 'ar-Arab')

    def test_update_duplicate_member(self):
        self.login_admin()

        response = self.client.post(
            self.update_url, data={
                'file': File(BytesIO(MIN_LGR), name=self.ref_member2.name),
                'language_script': 'hebr'})

        self.assertContains(response, "Failed to update Reference LGR member", status_code=HTTPStatus.OK)
        self.assertContains(response, "This reference LGR member already exists", status_code=HTTPStatus.OK)
        self.ref_member1.refresh_from_db()
        self.assertEqual(self.ref_member1.language_script, 'und-Latn')

    def test_update_overwrite_member(self):
        """
        Same as duplicate, but this time we upload a file with the same
        name as the one we are updating, this should overwrite.
        """
        self.login_admin()

        self.client.post(
            self.update_url,
            data={
                'file': File(BytesIO(MIN_LGR), name='ref_lgr_member1'),
                'language_script': 'jp'})

        self.ref_member1.refresh_from_db()
        self.assertEqual(self.ref_member1.name, 'ref_lgr_member1')
        self.assertEqual(self.ref_member1.language_script, 'jp')

    def test_cannot_update_as_icann_user(self):
        self.login_icann()

        response = self.client.post(self.update_url, data={'language_script': 'ar-Arab'})

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_cannot_update_as_regular_user(self):
        self.login_user()

        response = self.client.post(self.update_url, data={'language_script': 'ar-Arab'})

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_cannot_update_when_not_logged_in(self):
        response = self.client.post(self.update_url, data={'language_script': 'ar-Arab'})

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, f'/auth/login/?next={self.update_url}')


class TestRefLgrAccessView(LgrWebClientTestBase):
    model = RefLgr
    base_url = '/m/ref-lgr'

    def setUp(self):
        super().setUp()
        self.model.objects.exclude(active=True).delete()
        self.default_active = self.model.objects.get(active=True)
        self.active_url = f'{self.base_url}/isactive'

    def tearDown(self):
        for instance in self.model.objects.exclude(active=True):
            os.remove(instance.file.path)

    def test_access_when_logged_in_as_admin(self):
        self.login_admin()

        response = self.client.get(self.active_url)

        self.assertContains(
            response,
            f'<form class="form-horizontal" id="active-choice-form" url-data="{self.active_url}">',
            status_code=HTTPStatus.OK)

    def test_cannot_access_as_icann_user(self):
        self.login_icann()

        response = self.client.get(self.active_url)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_cannot_access_as_regular_user(self):
        self.login_user()

        response = self.client.get(self.active_url)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_cannot_access_when_not_logged_in(self):
        response = self.client.get(self.active_url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, f'/auth/login/?next={self.active_url}')
