#! /bin/env python
# -*- coding: utf-8 -*-
# Author: Viagénie
"""
test_api - 
"""
import logging
import os
import shutil

from django.conf import settings
from django.test import TestCase
from parameterized import parameterized

from lgr.core import LGR
from lgr.metadata import Metadata
from lgr_idn_table_review.icann_tools.api import get_reference_lgr, NoRefLgrFound
from lgr_models.models.lgr import RefLgr, RzLgrMember, RzLgr, LgrBaseModel, RefLgrMember

logger = logging.getLogger('api')


def custom_name_func(testcase_func, param_num, param):
    expected = None
    for lgr_data in param.args[2]:
        if lgr_data.get('expected'):
            expected = f"{lgr_data['lgr-type']}_{lgr_data['language-tag']}"
    return "%s_%s" % (
        testcase_func.__name__,
        parameterized.to_safe_name(f"{param.args[0]}_got_{param.args[1]}_expect_{expected}"),
    )


class TestApi(TestCase):
    test_path = os.path.join(settings.MEDIA_ROOT, 'test_files')

    def setUp(self):
        RzLgr.objects.all().delete()
        RefLgr.objects.all().delete()
        RzLgrMember.objects.all().delete()
        RefLgrMember.objects.all().delete()
        os.makedirs(self.test_path, exist_ok=True)

    @parameterized.expand([
        (0, 'th-Thai', [
            {
                'lgr-type': 'ref',
                'language-tag': 'Thai'
            }, {
                'lgr-type': 'ref',
                'language-tag': 'th-Thai',
                'expected': True
            }, {
                'lgr-type': 'rz',
                'language-tag': 'und-Thai'
            }
        ]),
        (1, 'bs-Cyrl', [
            {
                'lgr-type': 'ref',
                'language-tag': 'bs-Cyrl',
                'expected': True
            }, {
                'lgr-type': 'ref',
                'language-tag': 'bs-Latn'
            }, {
                'lgr-type': 'rz',
                'language-tag': 'und-Latn'
            }
        ]),
        (2, 'bs-Latn', [
            {
                'lgr-type': 'ref',
                'language-tag': 'en-Latn'
            }, {
                'lgr-type': 'rz',
                'language-tag': 'und-Latn',
                'expected': True
            }
        ]),
        (3, 'zh', [
            {
                'lgr-type': 'ref',
                'language-tag': 'zh-Hani',
                'expected': True
            }, {
                'lgr-type': 'rz',
                'language-tag': 'Hans',
            }
        ]),
        (4, 'zh-Hans', [
            {
                'lgr-type': 'ref',
                'language-tag': 'zh-Hani'
            }
        ]),
        (5, 'bs-Latn', [
            {
                'lgr-type': 'ref',
                'language-tag': 'bs-Cyrl'
            }
        ]),
        (6, 'th', [
            {
                'lgr-type': 'ref',
                'language-tag': 'Thai'
            }, {
                'lgr-type': 'ref',
                'language-tag': 'th-Thai',
                'expected': True
            }, {
                'lgr-type': 'rz',
                'language-tag': 'und-Thai'
            }
        ]),
        (7, 'zh', [
            {
                'lgr-type': 'ref',
                'language-tag': 'zh',
                'expected': True
            }
        ]),
        (8, 'bs', [
            {
                'lgr-type': 'ref',
                'language-tag': 'bs-Cyrl',
            }, {
                'lgr-type': 'ref',
                'language-tag': 'bs-Latn',
                'expected': True
            }, {
                'lgr-type': 'rz',
                'language-tag': 'und-Latn'
            }
        ]),
        (9, 'th', [
            {
                'lgr-type': 'rz',
                'language-tag': 'und-Thai',
                'expected': True
            }
        ]),
        (10, 'en', [
            {
                'lgr-type': 'ref',
                'language-tag': 'fr-Latn'
            }
        ]),
        (11, 'bs-Latn', [
            {
                'lgr-type': 'ref',
                'language-tag': 'bs-Cyrl',
            }
        ]),
        (12, 'zh-Hans', [
            {
                'lgr-type': 'rz',
                'language-tag': 'und-Hani'
            }, {
                'lgr-type': 'ref',
                'language-tag': 'und-Hans',
                'expected': True
            }
        ]),
        (13, 'fr-Latn', [
            {
                'lgr-type': 'ref',
                'language-tag': 'en-Latn',
            }, {
                'lgr-type': 'rz',
                'language-tag': 'und-Latn',
                'expected': True
            }
        ]),
        (14, 'bs', [
            {
                'lgr-type': 'rz',
                'language-tag': 'und-Cyrl'
            }
        ]),
        (15, 'th', [
            {
                'lgr-type': 'ref',
                'language-tag': 'Thai',
                'expected': True
            }, {
                'lgr-type': 'rz',
                'language-tag': 'und-Thai'
            }
        ]),
        (16, 'th', [
            {
                'lgr-type': 'rz',
                'language-tag': 'und-Thai',
                'expected': True
            }
        ]),
        (17, 'Thai', [
            {
                'lgr-type': 'ref',
                'language-tag': 'Thai',
                'expected': True
            }, {
                'lgr-type': 'ref',
                'language-tag': 'th-Thai'
            }, {
                'lgr-type': 'rz',
                'language-tag': 'und-Thai'
            }
        ]),
        (18, 'Thai', [
            {
                'lgr-type': 'ref',
                'language-tag': 'th-Thai'
            }, {
                'lgr-type': 'rz',
                'language-tag': 'und-Thai',
                'expected': True
            }
        ]),
        (19, 'Hans', [
            {
                'lgr-type': 'ref',
                'language-tag': 'zh-Hani'
            }, {
                'lgr-type': 'rz',
                'language-tag': 'Hans',
                'expected': True
            }
        ]),
        (20, 'Hant', [
            {
                'lgr-type': 'ref',
                'language-tag': 'zh-Hani'
            }, {
                'lgr-type': 'rz',
                'language-tag': 'Hans'
            }
        ]),
        (21, 'Thai', [
            {
                'lgr-type': 'ref',
                'language-tag': 'th-Thai',
            }
        ]),
        (22, 'ko', [
            {
                'lgr-type': 'ref',
                'language-tag': 'ko-Hang'
            }, {
                'lgr-type': 'ref',
                'language-tag': 'ko-Kore',
                'expected': True
            }
        ]),
        (23, 'ko-Hang', [
            {
                'lgr-type': 'ref',
                'language-tag': 'ko-Hang',
                'expected': True
            }, {
                'lgr-type': 'ref',
                'language-tag': 'ko-Kore'
            }
        ]),
        (24, 'ko-Hang', [
            {
                'lgr-type': 'ref',
                'language-tag': 'ko-Kore'
            }, {
                'lgr-type': 'ref',
                'language-tag': 'Hang',
                'expected': True
            }
        ]),
        (25, 'ko-Hang', [
            {
                'lgr-type': 'ref',
                'language-tag': 'ko-Kore'
            }, {
                'lgr-type': 'ref',
                'language-tag': 'Hang',
                'expected': True
            }, {
                'lgr-type': 'rz',
                'language-tag': 'Hang'
            }
        ]),
        (26, 'ja', [
            {
                'lgr-type': 'ref',
                'language-tag': 'Jpan',
                'expected': True
            }, {
                'lgr-type': 'ref',
                'language-tag': 'Hira'
            }
        ])
    ], name_func=custom_name_func)
    def test_get_reference_lgr(self, idx, idn_table_language_tag, lgr_datas):
        logger.info("Launching test %s", idx)
        rz_lgr = RzLgr.objects.create(file=os.path.join(self.test_path, 'RZ'), name='RZ LGR TEST', active=True)
        ref_lgr = RefLgr.objects.create(file=os.path.join(self.test_path, 'Ref'), name='Ref LGR TEST', active=True)
        expected = None
        for lgr_data in lgr_datas:
            model = None
            attrs = {
                'file': os.path.join(self.test_path, f"{lgr_data['lgr-type']}-{lgr_data['language-tag']}.xml"),
                "name": f"{lgr_data['lgr-type']}-{lgr_data['language-tag']}",
            }
            if lgr_data['lgr-type'] == 'ref':
                model = RefLgrMember
                attrs['ref_lgr'] = ref_lgr
                attrs['language_script'] = lgr_data['language-tag']
            elif lgr_data['lgr-type'] == 'rz':
                model = RzLgrMember
                attrs['rz_lgr'] = rz_lgr
                metadata = Metadata()
                metadata.add_language(lgr_data['language-tag'], force=True)
                lgr = LGR(metadata=metadata)
                xml = LgrBaseModel._parse_lgr_xml(lgr)
                with open(attrs['file'], 'wb') as f:
                    f.write(xml)

            lgr = model.objects.create(**attrs)
            if lgr_data.get('expected', False):
                expected = lgr

        idn_table_metadata = Metadata()
        idn_table_metadata.add_language(idn_table_language_tag, force=True)
        lgr = LGR(name=idn_table_language_tag, metadata=idn_table_metadata)

        if expected:
            self.assertEqual(get_reference_lgr(lgr), expected)
        else:
            self.assertRaises(NoRefLgrFound, get_reference_lgr, lgr)

    def tearDown(self):
        shutil.rmtree(self.test_path)
        RzLgr.objects.all().delete()
        RefLgr.objects.all().delete()
        RzLgrMember.objects.all().delete()
