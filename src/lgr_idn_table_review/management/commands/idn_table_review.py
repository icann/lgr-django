# -*- coding: utf-8 -*-
"""
idn_table_review - Django management command to review an IDN Table
"""
from __future__ import unicode_literals

import io
import sys

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from lgr.tools.idn_review.review import review_lgr
from lgr_idn_table_review.idn_tool.api import IdnTableInfo


class Command(BaseCommand):
    help = 'IDN Table Review Tool'

    def handle(self, *args, **options):
        with open(options['idn_table'], 'rb') as idn_table:
            idn_table_info = IdnTableInfo(options['idn_table'], idn_table.read().decode('utf-8'))
        with open(options['reference_lgr'], 'rb') as ref_lgr:
            ref_lgr_info = IdnTableInfo(options['reference_lgr'], ref_lgr.read().decode('utf-8'))

            context = review_lgr(idn_table_info.lgr, ref_lgr_info.lgr)
            html = render_to_string('lgr_idn_table_review/review.html', context)
            if not options['output']:
                sys.stdout.write(html)
            else:
                with io.open(options['output'], 'w', encoding='utf-8') as output_file:
                    output_file.write(html)

    def add_arguments(self, parser):
        parser.add_argument('idn_table', help='The IDN table to review')
        parser.add_argument('reference_lgr', help='The reference LGR used to review IDN table')
        parser.add_argument('-o', '--output', help='Output filename')
