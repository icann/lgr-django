from django.core.files.uploadedfile import SimpleUploadedFile

from lgr_manage.tests.test_views_common import AdminLgrTestCase, MIN_LGR
from lgr_models.models.lgr import IDNARepertoire


class IDNARepertoireTestCase(AdminLgrTestCase):
    model = IDNARepertoire
    base_view_name = 'lgr_admin_idna'
    active_view_name = 'lgr_admin_isactive_idna'
    delete_view_name = 'lgr_admin_delete_idna'

    def get_create_body(self):
        return {
            'name': 'Test IDNA Repertoire',
            'file': SimpleUploadedFile('idna-rep.xml', MIN_LGR, content_type='text/xml')
        }
