from django.core.files.uploadedfile import SimpleUploadedFile

from lgr_manage.tests.test_views_common import AdminLgrTestCase, MIN_LGR
from lgr_models.models.lgr import MSR


class MSRTestCase(AdminLgrTestCase):
    model = MSR
    base_view_name = 'lgr_admin_msr'
    active_view_name = 'lgr_admin_isactive_msr'
    delete_view_name = 'lgr_admin_delete_msr'

    def get_create_body(self):
        return {
            'name': 'Test MSR',
            'file': SimpleUploadedFile('msr.xml', MIN_LGR, content_type='text/xml')
        }
