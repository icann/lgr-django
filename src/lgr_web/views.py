import codecs
import csv
import pathlib
from enum import Enum, auto

from dal import autocomplete
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.utils.translation import gettext_lazy as _
from django.views.generic import FormView, TemplateView
from lgr.tools.utils import read_labels
from lgr.utils import cp_to_ulabel, format_cp, is_idna_valid_cp_or_sequence

from lgr_advanced.api import LabelInfo
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_utils import unidb
from lgr_web.forms import LabelFileFormsForm, LabelFormsForm
from lgr_web.utils import IANA_LANG_REGISTRY


class Interfaces(Enum):
    ADVANCED = auto()
    BASIC = auto()
    IDN_REVIEW = auto()
    IDN_ICANN = auto()
    IDN_ADMIN = auto()


class LGRModesView(TemplateView):
    template_name = 'lgr_modes.html'


class LGRAboutView(TemplateView):
    """
    About dialog
    """
    template_name = 'about.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['output'] = settings.SUPPORTED_UNICODE_VERSION
        return ctx


class LGRHelpView(TemplateView):
    """
    Help dialog
    """
    template_name = 'help.html'


class LabelFormsView(LoginRequiredMixin, FormView):
    form_class = LabelFormsForm
    template_name = 'label_forms.html'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.label = ''
        self.udata = None

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['file_form'] = LabelFileFormsForm(prefix='labels-form')
        if self.label:
            try:
                ctx['cp_list'] = format_cp(self.label)
                ulabel = cp_to_ulabel(self.label)
                ulabel.encode('utf-8')  # ensure encode won't fail
                if not is_idna_valid_cp_or_sequence(self.label, self.udata)[0]:
                    # FIXME: labels are parsed with ICU that implements UTS#46, so we may miss some invalid cp
                    ctx['u_label'] = '-'
                    ctx['a_label'] = '-'
                    messages.add_message(self.request, messages.ERROR,
                                         _('%(label)s is invalid as it contains disallowed characters.' % {
                                             'label': ulabel
                                         }))
                    return ctx
                ctx['u_label'] = ulabel
                ctx['a_label'] = self.udata.idna_encode_label(ctx['u_label'])
            except UnicodeError as ex:
                ctx['u_label'] = '-'
                ctx['a_label'] = '-'
                messages.add_message(self.request, messages.ERROR, lgr_exception_to_text(ex))

        return ctx

    def form_valid(self, form):
        self.label = form.cleaned_data['label']
        self.udata = unidb.manager.get_db_by_version(settings.SUPPORTED_UNICODE_VERSION)
        return self.render_to_response(self.get_context_data(form=form))


class LabelFileFormsView(LoginRequiredMixin, FormView):
    form_class = LabelFileFormsForm
    template_name = 'label_forms.html'

    def get_prefix(self):
        return 'labels-form'

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
        writer.writerow(['Input', 'Code point sequence', 'U-label', 'A-label', 'Note'])
        for label, parsed_label, valid, error in read_labels(label_info.labels, unidb=udata, as_cp=True,
                                                             return_exceptions=True):
            # FIXME: read_labels parse labels with ICU that implements UTS#46, so we may miss some invalid cp
            if not is_idna_valid_cp_or_sequence(parsed_label, udata)[0]:
                valid = False
                error = _('%(label)s is invalid as it contains disallowed characters.' % {
                    'label': label
                })
            if valid:
                try:
                    ulabel = cp_to_ulabel(parsed_label)
                    writer.writerow([label,
                                     format_cp(parsed_label),
                                     ulabel,
                                     udata.idna_encode_label(ulabel),
                                     '-'])
                except Exception as e:
                    valid = False
                    error = e

            if not valid:
                writer.writerow([label, format_cp(parsed_label) or '-', '-', '-', lgr_exception_to_text(error)])

        return response

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx['file_form'] = ctx['form']
        ctx['form'] = LabelFormsForm()
        return ctx


class LanguageAutocomplete(autocomplete.Select2ListView):

    def get_list(self):
        return sorted(IANA_LANG_REGISTRY)

    def create(self, value):
        return value
