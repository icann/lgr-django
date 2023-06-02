#! /bin/env python
# -*- coding: utf-8 -*-
"""
api - 
"""
import logging

from django.core.files import File
from django.utils import timezone

from lgr_idn_table_review.idn_tool.models import IdnReviewReport, IdnTable, IdnRefTable
from lgr_session.api import LGRStorage
from django.template.loader import render_to_string
from lgr.tools.idn_review.review import review_lgr, review_with_core_requirements
from typing import Dict
from lgr_models.models.lgr import LgrBaseModel

logger = logging.getLogger(__name__)


RFC_CORE_REQUIREMENT = 'core'


class LGRIdnReviewApi(LGRStorage):
    storage_model = IdnReviewReport
    lgr_model = IdnTable

    @staticmethod
    def generate_report_id():
        return timezone.now().strftime('%Y-%m-%d-%H%M%S.%f')

    def lgr_queryset(self):
        return self.lgr_model.objects.filter(owner=self.user)

    def get_lgr(self, pk):
        return self.lgr_model.get_object(self.user, pk)

    def create_lgr(self, file, name, report_id):
        return IdnTable.objects.create(file=File(file),
                                       name=name,
                                       owner=self.user,
                                       report_id=report_id)

    def create_reflgr(self, file, name, report_id):
        return IdnRefTable.objects.create(file=File(file),
                                          name=name,
                                          owner=self.user,
                                          report_id=report_id)

    def create_review_report(self, idn_table_pk, lgr_info, absolute_url):
        idn_table = self.get_lgr(idn_table_pk)
        html_report = ''

        context = {
            'idn_table': idn_table.name,
            'idn_table_url': absolute_url + idn_table.display_url()
        }

        review_method = self.review_idn_table
        review_args = [context, idn_table, lgr_info, absolute_url, self.user]
        template = 'lgr_idn_table_review/review.html'
        if lgr_info == RFC_CORE_REQUIREMENT:
            # handle the case where 'RFC Core Requirements' is selected
            review_method = self.review_idn_table_with_core_requirements
            review_args = [context, idn_table]
            template = 'lgr_idn_table_review/review_core.html'

        try:
            review_method(*review_args)
        except BaseException:
            logger.exception('Failed to review IDN table')
            html_report = render_to_string('lgr_idn_table_review/error.html', context)
        else:
            html_report = render_to_string(template, context)
        finally:
            return idn_table.name, html_report

    def review_idn_table(self, context: Dict, idn_table: IdnTable, lgr_info, absolute_url, user):
        ref_lgr = LgrBaseModel.from_tuple(lgr_info, user)
        context.update({
            'ref_lgr': ref_lgr.name,
            'ref_lgr_url': absolute_url + ref_lgr.display_url()
        })
        context.update(review_lgr(idn_table.to_lgr(), ref_lgr.to_lgr()))

    def review_idn_table_with_core_requirements(self, context: Dict, idn_table: IdnTable):
        context.update({
            'ref_lgr': 'RFC Core Requirements',
            'ref_lgr_url': None
        })
        context.update(review_with_core_requirements(idn_table.to_lgr()))

    def get_lgrs_in_report(self, report_id):
        return self.lgr_queryset().filter(report_id=report_id)

    def delete_report(self, report_id):
        self.storage_delete_report(report_id)
        self.get_lgrs_in_report(report_id).delete()


class LGRIdnRefReviewApi(LGRStorage):
    lgr_model = IdnRefTable

    def lgr_queryset(self):
        return self.lgr_model.objects.filter(owner=self.user)
