import io
import sys

from django.core.files import File
from django.core.management.base import BaseCommand
from django.template.loader import render_to_string
from lgr.tools.idn_review.review import review_lgr

from lgr_models.models.lgr import TemporaryLgrBase


class Command(BaseCommand):
    help = 'IDN Table Review Tool'

    def handle(self, *args, **options):
        idn_table_review(options['idn_table'], options['reference_lgr'], options['output'])

    def add_arguments(self, parser):
        parser.add_argument('idn_table', help='The IDN table to review')
        parser.add_argument('reference_lgr', help='The reference LGR used to review IDN table')
        parser.add_argument('-o', '--output', help='Output filename')


def idn_table_review(idn_table, reference_lgr, output=None):
    # TODO: See if we can replace this with `LGRIdnReviewApi`
    with open(idn_table, 'rb') as idn_table_file:
        idn_table = TemporaryLgrBase(name=idn_table, file=File(idn_table_file))

        with open(reference_lgr, 'rb') as ref_lgr_file:
            ref_lgr = TemporaryLgrBase(name=reference_lgr, file=File(ref_lgr_file))
            context = review_lgr(idn_table.to_lgr(), ref_lgr.to_lgr())

    html = render_to_string('lgr_idn_table_review/review.html', context)

    if not output:
        sys.stdout.write(html)
    else:
        with io.open(output, 'w', encoding='utf-8') as output_file:
            output_file.write(html)
