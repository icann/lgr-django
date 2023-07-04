from io import BytesIO

from django.core.files import File
from django.core.files.uploadedfile import SimpleUploadedFile

from lgr_manage.tests.test_views_common import AdminLgrTestCase, MIN_LGR
from lgr_models.models.lgr import RzLgr, RzLgrMember


class RzLgrTestCase(AdminLgrTestCase):
    model = RzLgr
    base_view_name = 'lgr_admin_rz_lgr'
    active_view_name = 'lgr_admin_isactive_rz_lgr'
    delete_view_name = 'lgr_admin_delete_rz_lgr'

    def setUp(self):
        super().setUp()
        RzLgrMember.objects.create(name='rz_lgr_member1',
                                   file=File(BytesIO(MIN_LGR), name='rz_lgr_member1'),
                                   common=self.other)
        RzLgrMember.objects.create(name='rz_lgr_member2',
                                   file=File(BytesIO(MIN_LGR), name='rz_lgr_member2'),
                                   common=self.other)

    def get_create_body(self):
        return {
            'name': 'Test RZ LGR',
            'file': SimpleUploadedFile('rz-lgr.xml', MIN_LGR, content_type='text/xml'),
            'repository': [SimpleUploadedFile('rz-lgr-1.xml', MIN_LGR, content_type='text/xml'),
                           SimpleUploadedFile('rz-lgr-2.xml', MIN_LGR, content_type='text/xml')],
        }

    def test_delete_when_logged_in(self):
        super().test_delete_when_logged_in()
        self.assertFalse(RzLgrMember.objects.filter(common=self.other.pk).exists())
