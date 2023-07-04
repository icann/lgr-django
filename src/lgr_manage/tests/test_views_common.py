from http import HTTPStatus
from io import BytesIO
from unittest import SkipTest

from django.core.files import File
from django.urls import reverse

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


class AdminLgrTestCase(LgrWebClientTestBase):
    model = None
    base_view_name = None
    active_view_name = None
    delete_view_name = None

    def setUp(self):
        self.__do_skip()
        super().setUp()
        self.model.objects.exclude(active=True).delete()
        self.default_active = self.model.objects.get(active=True)
        self.other = self.model.objects.create(name='Other',
                                               file=File(BytesIO(MIN_LGR), name='other.xml'))
        self.active_url = reverse(self.active_view_name)
        self.base_url = reverse(self.base_view_name)
        self.delete_url = reverse(self.delete_view_name, kwargs={'lgr_pk': self.other.pk})

    def __do_skip(self):
        if not self.model:
            raise SkipTest('Do not launch test in parent class')

    def get_create_body(self):
        raise NotImplementedError

    def test_access_active_when_logged_in(self):
        self.login_admin()

        response = self.client.get(self.active_url)
        self.assertContains(response,
                            f'<form class="form-horizontal" id="active-choice-form" '
                            f'url-data="{self.active_url}">',
                            status_code=HTTPStatus.OK)

    def test_access_active_when_icann_user(self):
        self.login_icann()

        response = self.client.get(self.active_url)
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

    def test_access_active_when_user(self):
        self.login_user()

        response = self.client.get(self.active_url)
        self.assertEquals(response.status_code, HTTPStatus.FORBIDDEN)

    def test_access_active_when_not_logged_in(self):
        response = self.client.get(self.active_url)
        self.assertEquals(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, f'/auth/login/?next={self.active_url}')

    def test_update_active_when_logged_in(self):
        self.login_admin()
        response = self.client.post(self.active_url, data={'active': self.other.pk})
        self.assertContains(response, f'"old_active": {self.default_active.pk}', status_code=HTTPStatus.OK)
        self.assertEquals(self.model.objects.get(active=True).pk, self.other.pk)

    def test_update_active_when_icann_user(self):
        self.login_icann()

        response = self.client.post(self.active_url, data={'active': 2})
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_update_active_when_user(self):
        self.login_user()

        response = self.client.post(self.active_url, data={'active': 2})
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_update_active_when_not_logged_in(self):
        response = self.client.post(self.active_url, data={'active': 2})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, f'/auth/login/?next={self.active_url}')

    def test_create_when_logged_in(self):
        self.login_admin()
        create_body = self.get_create_body()

        self.client.post(self.base_url, data=create_body)
        self.assertTrue(self.model.objects.filter(name=create_body['name']).exists())

    def test_create_when_icann_user(self):
        self.login_icann()

        response = self.client.post(self.base_url, data={})
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_create_when_user(self):
        self.login_user()

        response = self.client.post(self.base_url, data={})
        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)

    def test_create_when_not_logged_in(self):
        response = self.client.post(self.base_url, data={})
        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, f'/auth/login/?next={self.base_url}')

    def test_delete_when_logged_in(self):
        self.login_admin()

        self.client.post(self.delete_url)

        self.assertFalse(self.model.objects.filter(pk=self.other.pk).exists())

    def test_delete_when_icann_user(self):
        self.login_icann()

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTrue(self.model.objects.filter(pk=self.other.pk).exists())

    def test_delete_when_user(self):
        self.login_user()

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, HTTPStatus.FORBIDDEN)
        self.assertTrue(self.model.objects.filter(pk=self.other.pk).exists())

    def test_delete_when_not_logged_in(self):

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, HTTPStatus.FOUND)
        self.assertEquals(response.url, f'/auth/login/?next={self.delete_url}')
        self.assertTrue(self.model.objects.filter(pk=self.other.pk).exists())

    def test_delete_active_reference(self):
        # set other active
        self.test_update_active_when_logged_in()
        #  sanity check
        self.default_active.refresh_from_db()
        self.assertFalse(self.default_active.active)
        # then delete the active ref lgr
        self.test_delete_when_logged_in()

        # expect default LGR to be active again
        self.default_active.refresh_from_db()
        self.assertTrue(self.default_active.active)

    def test_set_first_active(self):
        self.model.objects.all().delete()
        #  sanity checks
        self.assertFalse(self.model.objects.filter(active=True).exists())

        self.test_create_when_logged_in()
        self.assertEqual(self.model.objects.count(), 1)
        self.assertTrue(self.model.objects.filter(active=True).exists())
