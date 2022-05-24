from lgr_models.tests.lgr_webclient_test_base import LgrWebClientTestBase
from lgr_manage.forms import RzLgrIsActiveForm
from lgr_models.models.lgr import RzLgr

class RzLgrActiveTestCase(LgrWebClientTestBase):
    def test_access_active_when_logged_in(self):
        self.login()

        response = self.client.get('/m/rz-lgr/isactive')
        self.assertContains(response,
                            '<form class="form-horizontal" id="active-choice-form" url-data="/m/rz-lgr/isactive">',
                            status_code=200)

    def test_access_active_when_not_logged_in(self):
        response = self.client.get('/m/msr')
        self.assertContains(response, status_code=403)

    def test_update_active_when_logged_in(self):
        self.login()
        form = RzLgrIsActiveForm()
        form.data = {'active': ['2']}
        response = self.client.post('/m/rz-lgr/isactive', form)
        self.assertContains(response, status_code=200)
        self.assertContains(RzLgr.filter(active=True).first().pk, 2)

    def test_update_active_when_not_logged_in(self):
        form = RzLgrIsActiveForm()
        form.data = {'active': ['2']}
        response = self.client.post('/m/rz-lgr/isactive', form)
        self.assertContains(response, status_code=403)