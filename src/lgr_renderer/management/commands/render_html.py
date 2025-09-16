"""
render_html - Django management command to render an LGR document into a HTML page.
"""
from django.core.management.base import BaseCommand

from lgr_renderer.api import render_html


class Command(BaseCommand):
    help = 'Render an LGR into HTML'

    def handle(self, *args, **options):
        render_html(options['xml'], options['validate'], options['output'])

    def add_arguments(self, parser):
        parser.add_argument('xml', metavar='XML')
        parser.add_argument('-o', '--output', help='Output filename')
        parser.add_argument('-t', '--validate', help='Validate input LGR',
                            default=False, action='store_true')
