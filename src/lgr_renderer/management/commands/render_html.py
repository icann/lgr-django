# -*- coding: utf-8 -*-
"""
render_html - Django management command to render an LGR document into a HTML page.
"""
from __future__ import unicode_literals
import sys
import io

from django.core.management.base import BaseCommand
from django.template.loader import render_to_string

from lgr_editor.api import LGRInfo
from lgr_renderer.api import generate_context


class Command(BaseCommand):
    help = 'Render an LGR into HTML'

    def handle(self, *args, **options):
        with open(options['xml'], 'rb') as lgr_xml:
            lgr_info = LGRInfo.from_dict(
                {
                    'xml': lgr_xml.read(),
                    'validate': options['validate'],
                }, None
            )

            lgr = lgr_info.lgr
            context = generate_context(lgr)
            html = render_to_string('lgr_renderer.html', context)
            if 'output' not in options:
                sys.stdout.write(html)
            else:
                with io.open(options['output'], 'w', encoding='utf-8') as output_file:
                    output_file.write(html)

    def add_arguments(self, parser):
        parser.add_argument('xml', metavar='XML')
        parser.add_argument('-o', '--output', help='Output filename')
        parser.add_argument('-t', '--validate', help='Validate input LGR',
                            default=False, action='store_true')
