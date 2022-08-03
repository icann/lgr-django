from lgr_models.models.lgr import RzLgr, RefLgr, RefLgrMember
from unittest import mock

MockListExpected = [(('reflgr one', 'reflgr one'),
                     (("('filename_common1', 1)", 'trucmuch'),
                      ("('ref_member_label1', 1)", 'member1'),
                      ("('ref_member_label2', 3)", 'member2'))),
                    (('reflgr two', 'reflgr two'),
                     (("('label_1', 3)", 'filename_common2'),
                      ("('ref_member_label1', 1)", 'member1'),
                      ("('ref_member_label2', 3)", 'member2')))]


class RefLgrMemberMock:

    def filter(self, ref_lgr):
        ref_member1: RefLgrMember = mock.Mock()
        ref_member1.filename = 'member_1'
        ref_member1.name = 'member1'
        ref_member1.pk = 1
        ref_member1._meta.label = 'ref_member_label1'
        ref_member1.to_tuple = mock.Mock(return_value=RefLgrMember.to_tuple(ref_member1))
        ref_member2: RefLgrMember = mock.Mock()
        ref_member2.filename = 'member_2'
        ref_member2.name = 'member2'
        ref_member2.pk = 3
        ref_member2._meta.label = 'ref_member_label2'
        ref_member2.to_tuple = mock.Mock(return_value=RefLgrMember.to_tuple(ref_member2))
        return [ref_member1, ref_member2]


class RefLgrMock:

    def filter(self, active):
        ref_lgr1: RefLgr = mock.Mock()
        ref_lgr1.name = 'reflgr one'
        ref_lgr1.active = True
        ref_lgr1.pk = 1
        ref_lgr1._meta.label = "filename_common1"
        ref_lgr1.filename = 'trucmuch'
        ref_lgr1.to_tuple = mock.Mock(return_value=RefLgr.to_tuple(ref_lgr1))
        ref_lgr2: RefLgr = mock.Mock()
        ref_lgr2.active = True
        ref_lgr2.name = 'reflgr two'
        ref_lgr2.pk = 3
        ref_lgr2.filename = 'filename_common2'
        ref_lgr2._meta.label = "label_1"
        ref_lgr2.to_tuple = mock.Mock(return_value=RefLgr.to_tuple(ref_lgr2))
        result = [ref_lgr1, ref_lgr2]
        return result


class RzLgrMock:

    def filter(self, active):
        return []
