# -*- coding: utf-8 -*-
import codecs
import csv
import pathlib

from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.views.generic import TemplateView, FormView

from lgr.tools.utils import parse_label_input, parse_codepoint_input
from lgr.utils import cp_to_ulabel, format_cp
from lgr_advanced.api import LGRToolStorage, LabelInfo
from lgr_advanced.forms import LabelFormsForm
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_advanced.models import LgrModel
from lgr_advanced.utils import list_built_in_lgr
from lgr_models.models.lgr import RzLgr
from lgr_utils import unidb


class LGRViewMixin(LoginRequiredMixin):

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.storage = LGRToolStorage(request.user)

    def get_context_data(self, **kwargs):
        ctx = super(LGRViewMixin, self).get_context_data(**kwargs)
        ctx.update({
            'home_url_name': 'lgr_advanced_mode'
        })
        return ctx


class AdvancedModeView(LGRViewMixin, TemplateView):
    template_name = 'lgr_advanced/index.html'

    def get_context_data(self, **kwargs):
        ctx = super(AdvancedModeView, self).get_context_data(**kwargs)
        current_lgrs = set(LgrModel.objects.filter(owner=self.request.user).values_list('name', flat=True))
        xml_files = [l for l in list_built_in_lgr() if l not in current_lgrs]
        ctx.update({
            'built_in_lgr_files': xml_files,
            'built_in_lgrs': RzLgr.objects.exclude(name__in=current_lgrs),
            'lgrs': LgrModel.objects.filter(owner=self.request.user).all(),
            'reports': self.storage.list_storage(),
        })
        return ctx


class LabelFormsView(LoginRequiredMixin, FormView):
    form_class = LabelFormsForm
    template_name = 'lgr_advanced/label_forms.html'

    def get_initial(self):
        initial = super().get_initial()
        return initial

    def form_valid(self, form):
        labels_file = form.cleaned_data['labels']
        label_info = LabelInfo.from_form(pathlib.Path(labels_file.name).stem,
                                         labels_file.read())
        udata = unidb.manager.get_db_by_version(settings.SUPPORTED_UNICODE_VERSION)

        response = HttpResponse(content_type='text/csv', charset='utf-8')
        cd = f'attachment; filename="{label_info.name}-label-forms.csv"'
        response['Content-Disposition'] = cd  # write BOM at the beginning to allow Excel decoding UTF-8

        response.write(codecs.BOM_UTF8.decode('utf-8'))
        writer = csv.writer(response)
        writer.writerow(['Code point sequence', 'U-label', 'A-label', 'Note'])
        for label in label_info.labels:
            try:
                parsed_label = parse_label_input(label.strip(), idna_decoder=udata.idna_decode_label)
                ulabel = cp_to_ulabel(parsed_label)
                writer.writerow([format_cp(parsed_label),
                                 ulabel,
                                 udata.idna_encode_label(ulabel),
                                 '-'])
            except Exception as e:
                if label.lower().startswith('xn--'):
                    row = ['-', '-', label]
                elif ' ' in label:
                    try:
                        parse_codepoint_input(label)
                        row = ['-', label, '-']
                    except:
                        row = [label, '-', '-']
                elif 'U+' in label.upper():
                    row = ['-', label, '-']
                else:
                    row = [label, '-', '-']

                row.append(lgr_exception_to_text(e))
                writer.writerow(row)

        return response
