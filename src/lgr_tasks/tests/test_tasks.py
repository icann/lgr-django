#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os

from django.core.cache import cache
from django.core.files import File
from django.test import TestCase, override_settings

from lgr_models.models.lgr import RzLgr
from lgr_tasks.tasks import calculate_index_variant_labels_tlds, _cache_key


class TasksTest(TestCase):
    fixtures_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'fixtures'))

    def setUp(self):
        cache.clear()
        RzLgr.objects.all().update(active=False)
        with open(os.path.join(self.fixtures_path, 'Sample-French-a-variant.xml'), 'r') as f:
            self.rz_lgr = RzLgr.objects.create(file=File(f, name='Sample-French-a-variant.xml'),
                                               name='RZ LGR Test', active=True)

    @override_settings(ICANN_TLDS=f"file://{os.path.join(fixtures_path, 'tlds.txt')}")
    def test_calculate_index_variant_labels_tlds(self):
        calculate_index_variant_labels_tlds()
        lgr_model, lgr_pk = self.rz_lgr.to_tuple()
        self.assertEqual(cache.get(_cache_key('àbc', lgr_model, lgr_pk)), cache.get(_cache_key('abc', lgr_model, lgr_pk)))
        self.assertIsNotNone(cache.get(_cache_key('def', lgr_model, lgr_pk)))
        self.assertEqual('NotInLGR', cache.get(_cache_key('ghi', lgr_model, lgr_pk)))
