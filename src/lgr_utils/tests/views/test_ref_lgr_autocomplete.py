from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import SimpleTestCase

from lgr_models.models.lgr import RefLgr, RefLgrMember
from lgr_utils.views import RefLgrAutocomplete, RefLgrAutocompleteWithCore


@patch("lgr_models.models.lgr.RefLgr.objects")
@patch("lgr_models.models.lgr.RefLgrMember.objects")
@patch("lgr_models.models.lgr.RzLgr.objects")
class TestRefLgrAutocomplete(SimpleTestCase):
    def setUp(self):
        self.expected_list_results = [
            (
                ('reflgr one', 'reflgr one'),
                (
                    ("('lgr_models.RefLgr', 1)", 'filename_common1'),
                    ("('lgr_models.RefLgrMember', 1)", 'member1'),
                    ("('lgr_models.RefLgrMember', 3)", 'member2')
                )
            ),
            (
                ('reflgr two', 'reflgr two'),
                (
                    ("('lgr_models.RefLgr', 3)", 'filename_common2'),
                    ("('lgr_models.RefLgrMember', 1)", 'member1'),
                    ("('lgr_models.RefLgrMember', 3)", 'member2')
                )
            )
        ]
        self.expected_core_list_results = [
            (
                ('RFC Core Requirements', 'RFC Core Requirements'),
                (
                    ('core', 'RFC Core Requirements'),
                )
            )
        ]

    @staticmethod
    def ref_lgr_member_list():
        member1_file = SimpleUploadedFile('member_1.txt', b'For Testing')
        member2_file = SimpleUploadedFile('member_2.txt', b'For Testing')

        ref_member1 = RefLgrMember(file=member1_file, name='member1', pk=1)
        ref_member2 = RefLgrMember(file=member2_file, name='member2', pk=3)
        return [ref_member1, ref_member2]

    @staticmethod
    def ref_lgr_list():
        ref_lgr1_file = SimpleUploadedFile('filename_common1.txt', b'For Testing')
        ref_lgr2_file = SimpleUploadedFile('filename_common2.txt', b'For Testing')

        ref_lgr1 = RefLgr(file=ref_lgr1_file, name='reflgr one', active=True, pk=1)
        ref_lgr2 = RefLgr(file=ref_lgr2_file, name='reflgr two', active=True, pk=3)
        return [ref_lgr1, ref_lgr2]

    @staticmethod
    def rz_lgr_list():
        return []

    def test_returns_list_of_ref_lgr(self, rz_lgr_manager_mock, ref_lgr_member_manager_mock, ref_lgr_manager_mock):
        rz_lgr_manager_mock.filter.return_value = self.rz_lgr_list()
        ref_lgr_member_manager_mock.filter.return_value = self.ref_lgr_member_list()
        ref_lgr_manager_mock.filter.return_value = self.ref_lgr_list()

        response = RefLgrAutocomplete.get_list()

        self.assertEqual(response, self.expected_list_results)

    def test_returns_list_of_ref_lgr_with_core(
            self, rz_lgr_manager_mock, ref_lgr_member_manager_mock, ref_lgr_manager_mock):
        rz_lgr_manager_mock.filter.return_value = self.rz_lgr_list()
        ref_lgr_member_manager_mock.filter.return_value = self.ref_lgr_member_list()
        ref_lgr_manager_mock.filter.return_value = self.ref_lgr_list()

        response = RefLgrAutocompleteWithCore.get_list()

        self.assertEqual(response, self.expected_list_results + self.expected_core_list_results)
