# -*- coding: utf-8 -*-
"""
render_html - Django management command to render an LGR document into a HTML page.
"""
from __future__ import unicode_literals

import os
import sys
import io

from django.core.files import File
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from lgr_models.models.lgr import LgrBaseModel
from lgr_renderer.api import generate_context


class Command(BaseCommand):
    help = 'Render an LGR into HTML'

    def handle(self, *args, **options):
        with open(options['xml'], 'rb') as lgr_xml:
            filename = os.path.basename(options['xml'])
            name = os.path.splitext(filename)[0]
            lgr_object = LgrBaseModel(file=File(lgr_xml, name=filename),
                                      name=name)

            lgr = lgr_object.to_lgr(validate=options['validate'])
            context = generate_context(lgr)
            html = render_to_string('lgr_renderer.html', context)
            if not options['output']:
                sys.stdout.write(html)
            else:
                with io.open(options['output'], 'w', encoding='utf-8') as output_file:
                    output_file.write(html)

    def add_arguments(self, parser):
        parser.add_argument('xml', metavar='XML')
        parser.add_argument('-o', '--output', help='Output filename')
        parser.add_argument('-t', '--validate', help='Validate input LGR',
                            default=False, action='store_true')
