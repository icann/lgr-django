import os
from http import HTTPStatus
from io import BytesIO

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile

from lgr_manage.tests.views.utils import MIN_LGR
from lgr_models.models.lgr import MSR
from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase


class TestMSRCreateView(LgrWebClientTestBase):
    model = MSR
    base_url = '/m/msr'

    @staticmethod
    def get_create_body():
        return {
            'name': 'Test MSR',
            'file': SimpleUploadedFile('msr.xml', MIN_LGR, content_type='text/xml')
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

        self.assertTrue(self.model.objects.filter(name=create_body['name']).exists())

    def test_set_first_active(self):
        self.login_admin()
        self.assertFalse(self.model.objects.filter(active=True).exists())
        create_body = self.get_create_body()

        self.client.post(self.base_url, data=create_body)

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


class TestMSRDeleteView(LgrWebClientTestBase):
    model = MSR
    base_url = '/m/msr'

    def setUp(self):
        super().setUp()
        self.model.objects.exclude(active=True).delete()
        self.default_active = self.model.objects.get(active=True)
        self.other_instance = self.model.objects.create(name='Other', file=File(BytesIO(MIN_LGR), name='other.xml'))
        self.delete_url = f'{self.base_url}/{self.other_instance.id}/delete'

    def tearDown(self):
        for instance in self.model.objects.exclude(active=True):
            os.remove(instance.file.path)

    def test_delete_when_logged_in_as_admin(self):
        self.login_admin()

        self.client.post(self.delete_url)

        self.assertFalse(self.model.objects.filter(pk=self.other_instance.pk).exists())

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


class TestMSRUpdateView(LgrWebClientTestBase):
    model = MSR
    base_url = '/m/msr'

    def setUp(self):
        super().setUp()
        self.model.objects.exclude(active=True).delete()
        self.default_active = self.model.objects.get(active=True)
        self.other_instance = self.model.objects.create(name='Other', file=File(BytesIO(MIN_LGR), name='other.xml'))
        self.active_url = f'{self.base_url}/isactive'

    def tearDown(self):
        for instance in self.model.objects.exclude(active=True):
            os.remove(instance.file.path)

    def test_update_when_logged_in_as_admin(self):
        self.login_admin()

        response = self.client.post(self.active_url, data={'active': self.other_instance.pk})

        self.assertContains(response, f'"old_active": {self.default_active.pk}', status_code=HTTPStatus.OK)
        self.assertEqual(self.model.objects.get(active=True).pk, self.other_instance.pk)

    def test_cannot_update_as_icann_user(self):
        self.login_icann()

        response = self.client.post(self.active_url, data={'active': self.other_instance.pk})

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_cannot_update_as_regular_user(self):
        self.login_user()

        response = self.client.post(self.active_url, data={'active': self.other_instance.pk})

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_cannot_update_when_not_logged_in(self):
        response = self.client.post(self.active_url, data={'active': self.other_instance.pk})

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEqual(response.url, f'/auth/login/?next={self.active_url}')


class TestMSRAccessView(LgrWebClientTestBase):
    model = MSR
    base_url = '/m/msr'

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
