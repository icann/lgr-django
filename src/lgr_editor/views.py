# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json

from lxml.etree import XMLSyntaxError

import os
import re
import logging
from io import StringIO
from itertools import islice

from django.core.exceptions import SuspiciousOperation
from django.contrib import messages
from django.conf import settings
from django.shortcuts import render, redirect
from django.utils.six import StringIO, iteritems
from django.utils.encoding import force_text
from django.utils.text import slugify
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html_join
from django.http import (HttpResponse,
                         HttpResponseBadRequest,
                         FileResponse,
                         JsonResponse)
from django.core.cache import cache
from django.views.generic import FormView
from django.urls import reverse
from django.template.response import TemplateResponse
from django.template.loader import render_to_string
from django.views.decorators.http import require_POST

from lgr.exceptions import LGRException, NotInLGR, CharInvalidContextRule, LGRFormatException
from lgr.metadata import Scope, Description, Metadata, Version
from lgr.char import RangeChar
from lgr.parser.xml_parser import LGR_NS
from lgr.utils import format_cp, cp_to_ulabel
from lgr.validate.transitivity import check_transitivity
from lgr.validate.symmetry import check_symmetry
from lgr.parser.rfc3743_parser import RFC3743Parser
from lgr.parser.rfc4290_parser import RFC4290Parser
from lgr.parser.line_parser import LineParser
from lgr.core import LGR

from .repertoires import get_by_name, get_all_scripts_from_repertoire
from .forms import (AddCodepointForm,
                    AddRangeForm,
                    AddCodepointFromScriptForm,
                    ImportCodepointsFromFileForm,
                    AddVariantForm,
                    CodepointForm,
                    CodepointVariantFormSet,
                    ImportLGRForm,
                    ReferenceForm,
                    ReferenceFormSet,
                    MetadataForm,
                    CreateLGRForm,
                    AddMultiCodepointsForm,
                    LanguageFormSet,
                    LabelFormsForm,
                    EditCodepointsForm)

from .lgr_exceptions import lgr_exception_to_text
from .api import (session_open_lgr,
                  session_select_lgr,
                  session_save_lgr,
                  session_delete_lgr,
                  session_new_lgr,
                  session_list_lgr,
                  session_get_file,
                  session_delete_file,
                  session_merge_set,
                  get_builtin_or_session_repertoire,
                  LGRInfo)
from .utils import (render_char,
                    render_name,
                    render_age,
                    render_cp_or_sequence,
                    cp_to_slug,
                    slug_to_cp,
                    slug_to_var,
                    var_to_slug,
                    make_lgr_session_key,
                    LGR_REPERTOIRE_CACHE_KEY,
                    LGR_CACHE_TIMEOUT)
from . import unidb


TRUNCATE_AFTER_N_CP_TAGS = 10
RE_SAFE_FILENAME = re.compile(r'[a-zA-Z0-9. _\-()]+')
logger = logging.getLogger(__name__)

INPUT_FILE_PARSER = {
    'rfc3743': RFC3743Parser,
    'rfc4290': RFC4290Parser,
    'one_per_line': LineParser
}


def new_lgr(request):
    """
    Create a new empty LGR.
    """
    form = CreateLGRForm(request.POST or None)
    if form.is_valid():
        lgr_id = form.cleaned_data['name']
        if lgr_id.endswith('.xml'):
            lgr_id = lgr_id.rsplit('.', 1)[0]
        lgr_id = slugify(lgr_id)

        if lgr_id in [lgr['name'] for lgr in session_list_lgr(request)]:
            logger.error("Import existing LGR")
            return render(request, 'lgr_editor/import_invalid.html',
                          context={'error': _("The LGR you have tried to create already exists in your working session. Please use a new name.")})

        session_new_lgr(request, lgr_id,
                        form.cleaned_data['unicode_version'],
                        form.cleaned_data['validating_repertoire'])
        return redirect('codepoint_list', lgr_id=lgr_id)
    ctx = {
        'form': form,
        'lgrs': session_list_lgr(request),
    }
    return render(request, 'lgr_editor/new_form.html', context=ctx)


def import_lgr(request):
    """
    Import an LGR from XML file supplied by user.
    """
    form = ImportLGRForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        lgr_names = [lgr['name'] for lgr in session_list_lgr(request)]
        is_set = len(form.cleaned_data['file']) > 1
        merged_id = None
        lgr_info_set = []
        for lgr_file in form.cleaned_data['file']:
            lgr_id = lgr_file.name
            if not RE_SAFE_FILENAME.match(lgr_id):
                raise SuspiciousOperation()
            if lgr_id.endswith('.xml'):
                lgr_id = lgr_id.rsplit('.', 1)[0]
            lgr_id = slugify(lgr_id)

            if not is_set and lgr_id in lgr_names:
                logger.error("Import existing LGR")
                return render(request, 'lgr_editor/import_invalid.html',
                              context={'error': _("The LGR you have tried to import already exists in your working "
                                                  "session. Please rename it before importing it.")})

            if is_set and lgr_id in [lgr.name for lgr in lgr_info_set]:
                logger.error("Import existing LGR in set")
                return render(request, 'lgr_editor/import_invalid.html',
                              context={'error': _("The LGR you have tried to import already exists in your set. "
                                                  "Please rename it before importing it.")})

            try:
                lgr_info = session_open_lgr(request,
                                            lgr_id,
                                            lgr_file.read(),
                                            form.cleaned_data['validating_repertoire'],
                                            validate=True,
                                            from_set=is_set)
            except Exception as import_error:
                logger.error("Input is not valid: '%s'",
                             import_error)
                return render(request, 'lgr_editor/import_invalid.html',
                              context={'error': lgr_exception_to_text(import_error)})

            lgr_info_set.append(lgr_info)

        if is_set:
            merged_id = slugify(form.cleaned_data['set_name'])
            if merged_id in lgr_names:
                logger.error("Import existing LGR set")
                return render(request, 'lgr_editor/import_invalid.html',
                              context={'error': _("The LGR set name already exists. Please use another name.")})

            try:
                merged_id = session_merge_set(request, lgr_info_set,
                                              form.cleaned_data['set_name'])
            except Exception as import_error:
                # remove imported LGRs, those that were already existing won't be erased
                logger.exception("Merge LGR from set is invalid")
                return render(request, 'lgr_editor/import_invalid.html',
                              context={'error': lgr_exception_to_text(import_error)})

        # All green, redirect to codepoint list
        return redirect('codepoint_list', lgr_id=merged_id if is_set else lgr_id)

    ctx = {
        'form': form,
        'lgrs': session_list_lgr(request),
    }
    return render(request, 'lgr_editor/import_form.html', context=ctx)


def import_reference_lgr(request, filename):
    """
    Import a built-in LGR to user's session.
    """
    if not RE_SAFE_FILENAME.match(filename):
        raise SuspiciousOperation()

    lgr_id = filename
    if lgr_id.endswith('.xml'):
        lgr_id = lgr_id.rsplit('.', 1)[0]
    lgr_id = slugify(lgr_id)
    with open(os.path.join(settings.LGR_STORAGE_LOCATION, filename + '.xml'), 'rb') as f:
        session_open_lgr(request, lgr_id, f.read())
    return redirect('codepoint_list', lgr_id=lgr_id)


def view_lgr_xml(request, lgr_id, force_download=False, lgr_set_id=None):
    """
    Display the XML of the LGR.

    Display the content of the LGR as XML. Optionally,
    set content-disposition to open download box on browser.
    """
    lgr_info = session_select_lgr(request, lgr_id, lgr_set_id)
    lgr_info.update_xml(pretty_print=True)
    resp = HttpResponse(lgr_info.xml, content_type='text/xml', charset='UTF-8')
    if force_download:
        resp['Content-disposition'] = 'attachment'
    return resp


def validate_lgr(request, lgr_id, output_func=None, lgr_set_id=None):
    """
    Validate an LGR and display result.
    """
    lgr_info = session_select_lgr(request, lgr_id, lgr_set_id)
    # Construct options dictionary for checks/validations
    options = {}
    try:
        options['unidb'] = unidb.manager.get_db_by_version(lgr_info.lgr.metadata.unicode_version)
    except KeyError:
        pass
    if lgr_info.validating_repertoire is not None:
        options['validating_repertoire'] = lgr_info.validating_repertoire
    options['rng_filepath'] = settings.LGR_RNG_FILE

    results = lgr_info.lgr.validate(options)
    tpl_name = 'lgr_editor/validate_lgr.html'
    context = {
        'results': results,
        'name': lgr_id
    }
    if output_func:
        return output_func(lgr_id, render_to_string(tpl_name, context))
    else:
        return render(request, tpl_name, context)


def validate_lgr_save(request, lgr_id, lgr_set_id=None):
    return validate_lgr(request, lgr_id, lgr_set_id=lgr_set_id,
                        output_func=_prepare_html_file_response)


def _prepare_html_file_response(name, out):
    response = HttpResponse(content_type='text/html')
    cd = 'attachment; filename="{0}-{1}.html"'.format(name, 'validation-results')
    response['Content-Disposition'] = cd

    response.write(out)

    return response


def codepoint_list(request, lgr_id='default', lgr_set_id=None):
    """
    List the codepoints defined in an LGR.
    """
    lgr_info = session_select_lgr(request, lgr_id, lgr_set_id)

    # instantiate form
    cp_form = AddCodepointForm(request.POST if 'add_cp' in request.POST else None, prefix='add_cp')
    if 'add_cp' in request.POST and cp_form.is_valid():
        logger.debug("Add CP")
        # form was submitted, we parse the value from the form field
        cp_or_sequence = cp_form.cleaned_data['codepoint']
        override_repertoire = cp_form.cleaned_data['override_repertoire']
        try:
            lgr_info.lgr.add_cp(cp_or_sequence,
                                validating_repertoire=lgr_info.validating_repertoire,
                                override_repertoire=override_repertoire)
            session_save_lgr(request, lgr_info)
            messages.success(request, _('New code point %s added') % format_cp(cp_or_sequence))
        except LGRException as ex:
            messages.add_message(request, messages.ERROR,
                                 lgr_exception_to_text(ex))
            # redirect to myself to refresh display
            # Note: cannot add code point in set mode
            return redirect('codepoint_list',
                            lgr_id=lgr_id)

    rule_names = (('', ''),) + tuple((v, v) for v in lgr_info.lgr.rules)
    edit_codepoints_form = EditCodepointsForm(request.POST if ('add-rules' in request.POST or 'add-tags' in request.POST)
                                              else None, prefix='edit_codepoints', rule_names=rule_names)
    if ('add-rules' in request.POST or 'add-tags' in request.POST) and edit_codepoints_form.is_valid():
        logger.debug('Edit codepoints')
        cd = edit_codepoints_form.cleaned_data
        when = cd['when'] or None
        not_when = cd['not_when'] or None
        tags = cd['tags'].split()
        edited = cd['cp_id']
        invalid = []
        for cp in [slug_to_cp(c) for c in edited]:
            char = lgr_info.lgr.get_char(cp)
            new_tags = char.tags + tags

            try:
                if isinstance(char, RangeChar):
                    # Delete codepoint range from LGR, then add it
                    lgr_info.lgr.del_range(char.first_cp, char.last_cp)
                    lgr_info.lgr.add_range(char.first_cp,
                                           char.last_cp,
                                           comment=char.comment,
                                           when=when or char.when, not_when=not_when or char.not_when,
                                           ref=char.references,
                                           tag=new_tags)
                else:
                    # Delete codepoint from LGR, then add it + its variants
                    lgr_info.lgr.del_cp(char.cp)
                    lgr_info.lgr.add_cp(char.cp,
                                        comment=char.comment,
                                        ref=char.references,
                                        tag=new_tags,
                                        when=when or char.when, not_when=not_when or char.not_when)
                    for variant in char.get_variants():
                        lgr_info.lgr.add_variant(char.cp,
                                                 variant.cp,
                                                 variant_type=variant.type,
                                                 when=variant.when, not_when=variant.not_when,
                                                 comment=variant.comment, ref=variant.references)
            except (LGRFormatException, CharInvalidContextRule) as e:
                logger.warning('Cannot update char tags/wle:', exc_info=e)
                invalid.append(char)
                # Need to revert the deletion
                if isinstance(char, RangeChar):
                    lgr_info.lgr.add_range(char.first_cp,
                                           char.last_cp,
                                           comment=char.comment,
                                           when=char.when, not_when=char.not_when,
                                           ref=char.references,
                                           tag=char.tags)
                else:
                    lgr_info.lgr.add_cp(char.cp,
                                        comment=char.comment,
                                        ref=char.references,
                                        tag=char.tags,
                                        when=char.when, not_when=char.not_when)
                    for variant in char.get_variants():
                        lgr_info.lgr.add_variant(char.cp,
                                                 variant.cp,
                                                 variant_type=variant.type,
                                                 when=variant.when, not_when=variant.not_when,
                                                 comment=variant.comment, ref=variant.references)

        session_save_lgr(request, lgr_info)
        operation = _('Rule') if 'add-rules' in request.POST else _('Tag(s)')
        operation_lowercase = _('rule') if 'add-rules' in request.POST else _('tag(s)')
        if len(edited) - len(invalid):
            messages.add_message(request,
                                 messages.SUCCESS,
                                 _("%(operation)s successfully added to %(nb_cp)s code point(s)") % {'operation': operation,
                                                                                                     'nb_cp': len(edited) - len(invalid)})
        if invalid:
            messages.add_message(request,
                                 messages.WARNING,
                                 _("%(nb_cp)s code points were not updated to avoid invalid %(operation)s") % {'operation': operation_lowercase,
                                                                                                               'nb_cp': len(invalid)})

    has_range = False
    for char in lgr_info.lgr.repertoire.all_repertoire():
        if isinstance(char, RangeChar):
            has_range = True
            break

    ctx = {
        'cp_form': cp_form,
        'edit_codepoints_form': edit_codepoints_form,
        'lgr': lgr_info.lgr,
        'lgr_id': lgr_id,
        'is_set': lgr_info.is_set or lgr_set_id is not None,
        'has_range': has_range,
        'all_tags_json': json.dumps(lgr_info.lgr.all_tags()),
    }
    if lgr_set_id:
        lgr_set_info = session_select_lgr(request, lgr_set_id)
        ctx['lgr_set'] = lgr_set_info.lgr
        ctx['lgr_set_id'] = lgr_set_id

    return render(request, 'lgr_editor/codepoint_list.html', context=ctx)


def codepoint_list_json(request, lgr_id, lgr_set_id=None):
    lgr_info = session_select_lgr(request, lgr_id, lgr_set_id)
    udata = unidb.manager.get_db_by_version(lgr_info.lgr.metadata.unicode_version)

    repertoire_cache_key = make_lgr_session_key(LGR_REPERTOIRE_CACHE_KEY,
                                                request,
                                                lgr_id)
    repertoire = cache.get(repertoire_cache_key)
    if repertoire is None:
        # Generate repertoire
        repertoire = []
        for char in lgr_info.lgr.repertoire:
            cp_slug = cp_to_slug(char.cp)
            kwargs = {'lgr_id': lgr_id, 'codepoint_id': cp_slug}
            if lgr_set_id is not None:
                kwargs['lgr_set_id'] = lgr_set_id
            cp_view_url = reverse('codepoint_view', kwargs=kwargs)
            actions = [cp_view_url]
            is_range = isinstance(char, RangeChar)
            if is_range:
                expand_url = reverse('expand_range', kwargs={'lgr_id': lgr_id,
                                                             'codepoint_id': cp_slug})
                actions.append(expand_url)

            repertoire.append({
                'codepoint_id': cp_slug,
                'cp_disp': render_char(char),
                'comment': char.comment or '',
                'name': render_name(char, udata),
                'tags': char.tags,
                'variant_number': len(list(char.get_variants())),
                'is_range': is_range,
                'actions': actions
            })
        cache.set(repertoire_cache_key, repertoire, LGR_CACHE_TIMEOUT)

    response = {'data': repertoire}

    return JsonResponse(response)


def delete_lgr(request, lgr_id):
    """
    Delete the selected LGR from session.
    """
    session_delete_lgr(request, lgr_id)

    return redirect('/')


def download_file(request, filename):
    """
    Download the selected file from session.
    """
    res_file = session_get_file(request, filename)
    if res_file is None:
        # TODO show an error...
        return delete_file(request, filename)
    response = FileResponse(res_file[0], content_type='application/x-gzip')
    response['Content-Disposition'] = 'attachment; filename={}'.format(filename)
    return response


def delete_file(request, filename):
    """
    Delete the selected file from session.
    """
    session_delete_file(request, filename)

    return redirect('/')


def codepoint_view(request, lgr_id, codepoint_id, lgr_set_id=None):
    """
    View a specific codepoints of an LGR.
    """
    lgr_info = session_select_lgr(request, lgr_id, lgr_set_id)
    udata = unidb.manager.get_db_by_version(lgr_info.lgr.metadata.unicode_version)
    codepoint = slug_to_cp(codepoint_id)
    rule_names = (('', ''),) + tuple((v, v) for v in lgr_info.lgr.rules)

    if 'add_variant' in request.POST:
        if lgr_info.is_set or lgr_set_id:
            return HttpResponseBadRequest('Cannot edit LGR set')
        add_variant_form = AddVariantForm(request.POST, prefix='add_variant')
        logger.debug('Add variant')
        if add_variant_form.is_valid():
            var_cp_sequence = add_variant_form.cleaned_data['codepoint']
            override_repertoire = add_variant_form.cleaned_data['override_repertoire']
            try:
                lgr_info.lgr.add_variant(codepoint,
                                         var_cp_sequence,
                                         variant_type=settings.DEFAULT_VARIANT_TYPE,
                                         validating_repertoire=lgr_info.validating_repertoire,
                                         override_repertoire=override_repertoire)
                if var_cp_sequence not in lgr_info.lgr.repertoire:
                    # Added variant code point not in repertoire
                    # -> add it to the LGR
                    lgr_info.lgr.add_cp(var_cp_sequence,
                                        comment="Automatically added from out-of-repertoire variant")
                    lgr_info.lgr.add_variant(var_cp_sequence, codepoint,
                                             variant_type=settings.DEFAULT_VARIANT_TYPE,
                                             comment="Automatically added to map back to out-of-repertoire variant")
                    # Add identity mapping for newly added code point
                    lgr_info.lgr.add_variant(var_cp_sequence, var_cp_sequence, variant_type='out-of-repertoire',
                                             comment='Out-of-repertoire')
                    messages.success(request, _('Automatically added codepoint %s from out-of-repertoire variant') %
                                     format_cp(var_cp_sequence))
                session_save_lgr(request, lgr_info)
                messages.success(request, _('New variant %s added') % format_cp(var_cp_sequence))
            except LGRException as ex:
                messages.add_message(request, messages.ERROR,
                                     lgr_exception_to_text(ex))
                # redirect to myself to refresh display
                return redirect('codepoint_view',
                                lgr_id=lgr_id,
                                codepoint_id=codepoint_id)
        else:
            logger.error('Add variant: form is not valid')
            logger.error(add_variant_form.errors)
    else:
        add_variant_form = AddVariantForm(None, prefix='add_variant')

    if 'edit_cp' in request.POST:
        if lgr_info.is_set or lgr_set_id:
            return HttpResponseBadRequest('Cannot edit LGR set')
        logger.debug('Edit CP')
        codepoint_form = CodepointForm(request.POST,
                                       prefix='edit_cp',
                                       rules=rule_names)
        variants_form = CodepointVariantFormSet(request.POST,
                                                prefix='variants',
                                                rules=rule_names)

        if codepoint_form.is_valid():
            comment = codepoint_form.cleaned_data['comment'] or None
            char = lgr_info.lgr.get_char(codepoint)
            when = codepoint_form.cleaned_data['when'] or None
            not_when = codepoint_form.cleaned_data['not_when'] or None
            ref = char.references
            tag = codepoint_form.cleaned_data['tags'].split()

            try:
                if isinstance(char, RangeChar):
                    lgr_info.lgr.del_range(char.first_cp, char.last_cp)
                    # No validating repertoire since
                    # the codepoint is being edited
                    lgr_info.lgr.add_range(char.first_cp,
                                           char.last_cp,
                                           comment=comment,
                                           when=when, not_when=not_when,
                                           ref=ref,
                                           tag=tag)
                else:
                    if variants_form.is_valid():
                        # Delete codepoint from LGR, then add it + its variants
                        lgr_info.lgr.del_cp(codepoint)
                        # No validating repertoire here neither
                        lgr_info.lgr.add_cp(codepoint,
                                            comment=comment,
                                            ref=ref,
                                            tag=tag,
                                            when=when, not_when=not_when)
                        for v_form in variants_form:
                            variant_codepoint = slug_to_cp(v_form.cleaned_data['cp'])
                            variant_comment = v_form.cleaned_data['comment'] or None
                            variant_type = v_form.cleaned_data['type']
                            variant_when = v_form.cleaned_data['when'] or None
                            variant_not_when = v_form.cleaned_data['not_when'] or None
                            # No validating repertoire here neither
                            lgr_info.lgr.add_variant(codepoint,
                                                     variant_codepoint,
                                                     comment=variant_comment,
                                                     variant_type=variant_type,
                                                     when=variant_when,
                                                     not_when=variant_not_when)
                    else:
                        logger.error('Edit CP: form is not valid')
                        logger.error(variants_form.errors)

                # Save edition
                session_save_lgr(request, lgr_info)
                messages.success(request, _('Code point edited'))
                # redirect to myself to refresh display
                return redirect('codepoint_view',
                                lgr_id=lgr_id,
                                codepoint_id=codepoint_id)
            except LGRException as ex:
                messages.add_message(request, messages.ERROR,
                                     lgr_exception_to_text(ex))
                # redirect to myself to refresh display
                return redirect('codepoint_view',
                                lgr_id=lgr_id,
                                codepoint_id=codepoint_id)

    char = lgr_info.lgr.get_char(codepoint)
    variants = []
    for v in char.get_variants():
        in_lgr = True
        try:
            lgr_info.lgr.get_char(v.cp)
        except NotInLGR:
            in_lgr = False

        variants.append({
            'cp': cp_to_slug(v.cp),
            'slug': var_to_slug(v),
            'cp_disp': render_char(v),
            'name': render_name(v, udata),
            'age': render_age(v, udata),
            'when': v.when,
            'not_when': v.not_when,
            'type': v.type,
            'comment': v.comment or '',
            'references': v.references,
            'in_lgr': in_lgr
        })
    variants_form = CodepointVariantFormSet(initial=variants,
                                            prefix='variants',
                                            rules=rule_names,
                                            disabled=lgr_info.is_set or lgr_set_id is not None)
    codepoint_form = CodepointForm(initial={'comment': char.comment,
                                            'tags': ' '.join(char.tags),
                                            'when': char.when,
                                            'not_when': char.not_when
                                            },
                                   prefix='edit_cp',
                                   rules=rule_names,
                                   disabled=lgr_info.is_set or lgr_set_id is not None)

    # References
    cp_references = []
    for ref_id in char.references:
        ref = lgr_info.lgr.reference_manager.get(str(ref_id), None)
        if ref is None:
            # Invalid reference id
            continue

        cp_references.append({
            'ref_id': ref_id,
            'description': ref.get('value', ''),
            'comment': ref.get('comment', '')
        })

    ctx = {
        'add_variant_form': add_variant_form,
        'codepoint_form': codepoint_form,
        'variants_form': variants_form,
        'is_range': isinstance(char, RangeChar),
        'cp': codepoint_id,
        'lgr': lgr_info.lgr,
        'lgr_id': lgr_id,
        'variants': variants,
        'cp_references': cp_references,
        'cp_references_json': json.dumps(cp_references),
        'cp_disp': render_char(char),
        'all_tags_json': json.dumps(lgr_info.lgr.all_tags()),
        'name': render_name(char, udata),
        'age': render_age(char, udata),
        'is_set': lgr_info.is_set or lgr_set_id is not None
    }
    if lgr_set_id:
        lgr_set_info = session_select_lgr(request, lgr_set_id)
        ctx['lgr_set'] = lgr_set_info.lgr
        ctx['lgr_set_id'] = lgr_set_id

    return render(request, 'lgr_editor/codepoint_view.html', context=ctx)


def expand_ranges(request, lgr_id):
    """
    Expand all ranges into code points.
    """
    lgr_info = session_select_lgr(request, lgr_id)
    if lgr_info.is_set:
        return HttpResponseBadRequest('Cannot edit LGR set')
    try:
        lgr_info.lgr.expand_ranges()
    except LGRException as ex:
        messages.add_message(request, messages.ERROR,
                             lgr_exception_to_text(ex))

    session_save_lgr(request, lgr_info)
    # Redirect to code point list
    return redirect('codepoint_list',
                    lgr_id=lgr_id)


def expand_range(request, lgr_id, codepoint_id):
    """
    Expand a range into code points.
    """
    lgr_info = session_select_lgr(request, lgr_id)
    if lgr_info.is_set:
        return HttpResponseBadRequest('Cannot edit LGR set')

    codepoint = slug_to_cp(codepoint_id)
    char = lgr_info.lgr.get_char(codepoint)

    if not isinstance(char, RangeChar):
        logger.error("Cannot expand non-range code point")
        return redirect('codepoint_list',
                        lgr_id=lgr_id)

    try:
        lgr_info.lgr.expand_range(char.first_cp, char.last_cp)
    except LGRException as ex:
        messages.add_message(request, messages.ERROR,
                             lgr_exception_to_text(ex))

    session_save_lgr(request, lgr_info)
    # Redirect to code point list
    return redirect('codepoint_list',
                    lgr_id=lgr_id)


def populate_variants(request, lgr_id):
    lgr_info = session_select_lgr(request, lgr_id)
    lgr = lgr_info.lgr

    if 'test' in request.GET:
        return JsonResponse({'result': check_symmetry(lgr_info.lgr, None)[0] and check_transitivity(lgr_info.lgr, None)[0]})

    log_output = StringIO()
    ch = logging.StreamHandler(log_output)
    ch.setLevel(logging.INFO)
    populate_logger = logging.getLogger('lgr.populate')

    # Configure module logger - since user may have disabled the 'lgr' logger,
    # reset its level
    populate_logger.addHandler(ch)
    populate_logger.setLevel('INFO')
    lgr.populate_variants()
    messages.add_message(request, messages.INFO, log_output.getvalue())
    messages.add_message(request, messages.SUCCESS, _("Variants populated"))
    session_save_lgr(request, lgr_info)
    return redirect('codepoint_list', lgr_id)


def codepoint_update_refs(request, lgr_id, codepoint_id):
    """
    Update a codepoint's references.
    """
    lgr_info = session_select_lgr(request, lgr_id)
    if lgr_info.is_set:
        return HttpResponseBadRequest('Cannot edit LGR set')

    codepoint = slug_to_cp(codepoint_id)

    ref_ids = filter(None, request.POST.getlist('ref_id'))  # filter away empty entries (an artifact of the editing form)

    try:
        char = lgr_info.lgr.get_char(codepoint)
        tags = char.tags
        comment = char.comment

        if isinstance(char, RangeChar):
            lgr_info.lgr.del_range(char.first_cp,
                                   char.last_cp)
            # No validating repertoire here since we're only updating references
            lgr_info.lgr.add_range(char.first_cp,
                                   char.last_cp,
                                   comment=comment,
                                   when=char.when,
                                   not_when=char.not_when,
                                   ref=ref_ids,  # update the ref ids
                                   tag=tags)
        else:
            lgr_info.lgr.del_cp(codepoint)
            # No validating repertoire either
            lgr_info.lgr.add_cp(codepoint,
                                comment=char.comment,
                                when=char.when, not_when=char.not_when,
                                ref=ref_ids,  # update the ref ids
                                tag=tags)
            for var in char.get_variants():
                # add back the variants
                lgr_info.lgr.add_variant(codepoint,
                                         variant_cp=var.cp,
                                         variant_type=var.type,
                                         when=var.when,
                                         not_when=var.not_when,
                                         comment=var.comment,
                                         ref=var.references)
        session_save_lgr(request, lgr_info)
        messages.success(request, _('References updated successfully'))
    except LGRException as ex:
        messages.add_message(request, messages.ERROR,
                             lgr_exception_to_text(ex))

    return redirect('codepoint_view', lgr_id, codepoint_id)


def var_update_refs(request, lgr_id, codepoint_id, var_slug):
    """
    Update a variant's references.
    """
    lgr_info = session_select_lgr(request, lgr_id)
    if lgr_info.is_set:
        return HttpResponseBadRequest('Cannot edit LGR set')

    codepoint = slug_to_cp(codepoint_id)
    var_cp, var_when, var_not_when = slug_to_var(var_slug)
    ref_ids = filter(None, request.POST.getlist('ref_id'))  # filter away empty entries (an artifact of the editing form)

    try:
        char = lgr_info.lgr.get_char(codepoint)
        # find our variant
        for variant in char.get_variants():
            if variant.cp == var_cp and variant.when == (var_when or None) and variant.not_when == (var_not_when or None):
                # found it!
                char.del_variant(variant.cp, when=variant.when, not_when=variant.not_when)
                lgr_info.lgr.add_variant(codepoint,
                                         variant.cp,
                                         variant_type=variant.type,
                                         when=variant.when,
                                         not_when=variant.not_when,
                                         comment=variant.comment,
                                         ref=ref_ids)
                session_save_lgr(request, lgr_info)
                messages.success(request,
                                 _('References updated successfully'))
                break
        else:
            errmsg = _("Variant %(var_codepoint)s for code point %(codepoint)s "
                       "with when=%(when)s and "
                       "not-when=%(not_when)s could not be found") % {
                'var_codepoint': var_cp,
                'codepoint': codepoint_id,
                'when': var_when,
                'not_when': var_not_when,
            }
            messages.error(request, errmsg)

    except LGRException as ex:
        messages.add_message(request, messages.ERROR,
                             lgr_exception_to_text(ex))

    return redirect('codepoint_view', lgr_id, codepoint_id)


def codepoint_delete(request, lgr_id, codepoint_id):
    """
    Delete a codepoint from an LGR.
    """
    # TODO - only accept POST request
    lgr_info = session_select_lgr(request, lgr_id)
    if lgr_info.is_set:
        return HttpResponseBadRequest('Cannot edit LGR set')

    codepoint = slug_to_cp(codepoint_id)

    char = lgr_info.lgr.get_char(codepoint)

    try:
        if isinstance(char, RangeChar):
            lgr_info.lgr.del_range(char.first_cp, char.last_cp)
        else:
            lgr_info.lgr.del_cp(codepoint)
        session_save_lgr(request, lgr_info)
        messages.info(request, _("Code point %s has been deleted") % format_cp(codepoint))
    except LGRException as ex:
        messages.add_message(request, messages.ERROR,
                             lgr_exception_to_text(ex))

    return redirect('codepoint_list', lgr_id)


def variant_delete(request, lgr_id, codepoint_id, var_slug):
    """
    Delete a variant of a codepoint from an LGR.
    """
    # TODO - only accept POST request
    lgr_info = session_select_lgr(request, lgr_id)
    if lgr_info.is_set:
        return HttpResponseBadRequest('Cannot edit LGR set')

    codepoint = slug_to_cp(codepoint_id)
    var_cp, var_when, var_not_when = slug_to_var(var_slug)

    try:
        r = lgr_info.lgr.del_variant(codepoint, var_cp, when=var_when or None, not_when=var_not_when or None)
        var_msg_prefix = _("Variant %(var_cp)s with when='%(when)s' and not-when='%(not_when)s'") \
                         % {'var_cp': format_cp(var_cp),
                            'when': var_when,
                            'not_when': var_not_when}
        if r:
            session_save_lgr(request, lgr_info)
            messages.info(request, _("%(var_msg_prefix)s has been deleted") % {'var_msg_prefix': var_msg_prefix})
        else:
            messages.error(request,
                           _("%(var_msg_prefix)s could not be deleted because it was not found")
                           % {'var_msg_prefix': var_msg_prefix})
    except LGRException as ex:
        messages.add_message(request, messages.ERROR,
                             lgr_exception_to_text(ex))

    return redirect('codepoint_view', lgr_id, codepoint_id)


def reference_list(request, lgr_id, lgr_set_id=None):
    """
    List/edit references of an LGR.
    """
    lgr_info = session_select_lgr(request, lgr_id, lgr_set_id)

    add_reference_form = ReferenceForm(request.POST if 'add_reference' in request.POST else None,
                                       prefix='add_reference', ro_id=False)
    if 'add_reference' in request.POST:
        if lgr_info.is_set or lgr_set_id:
            return HttpResponseBadRequest('Cannot edit LGR set')

        logger.debug('Add reference')
        if add_reference_form.is_valid():
            # form was submitted, we parse the value from the form field
            ref_id = add_reference_form.cleaned_data['ref_id']
            description = add_reference_form.cleaned_data['description']
            url = add_reference_form.cleaned_data['comment']
            try:
                lgr_info.lgr.reference_manager.add_reference(description, url, ref_id=ref_id or None)
                session_save_lgr(request, lgr_info)
                messages.success(request, _('New reference created'))
            except LGRException as ex:
                messages.add_message(request, messages.ERROR,
                                     lgr_exception_to_text(ex))
                # redirect to myself to refresh display
                return redirect('references', lgr_id)
        else:
            logger.error('Add reference: form is not valid')
            logger.error(add_reference_form.errors)

    if 'edit_references' in request.POST:
        if lgr_info.is_set or lgr_set_id:
            return HttpResponseBadRequest('Cannot edit LGR set')

        logger.debug('Edit reference')
        references_form = ReferenceFormSet(request.POST or None,
                                           prefix='references')
        if references_form.is_valid():
            reference_manager = lgr_info.lgr.reference_manager
            for ref_form in references_form:
                ref_id = ref_form.cleaned_data['ref_id']
                description = ref_form.cleaned_data['description']
                comment = ref_form.cleaned_data['comment']
                try:
                    reference_manager.update_reference(ref_id,
                                                       value=description,
                                                       comment=comment)
                    session_save_lgr(request, lgr_info)
                except LGRException as ex:
                    messages.add_message(request, messages.ERROR,
                                         lgr_exception_to_text(ex))
                    # redirect to myself to refresh display
                    return redirect('references', lgr_id)
        else:
            logger.error('Edit reference: form is not valid')
            logger.error(references_form.errors)

    references = [{
        'ref_id': ref_id,
        'description': ref.get('value', ''),
        'comment': ref.get('comment', '')
    } for (ref_id, ref) in iteritems(lgr_info.lgr.reference_manager)]
    references_form = ReferenceFormSet(initial=references, prefix='references',
                                       disabled=lgr_info.is_set or lgr_set_id is not None)

    ctx = {
        'add_reference_form': add_reference_form,
        'references_form': references_form,
        'lgr': lgr_info.lgr,
        'lgr_id': lgr_id,
        'is_set': lgr_info.is_set or lgr_set_id is not None
    }
    if lgr_set_id:
        lgr_set_info = session_select_lgr(request, lgr_set_id)
        ctx['lgr_set'] = lgr_set_info.lgr
        ctx['lgr_set_id'] = lgr_set_id

    return render(request, 'lgr_editor/references.html', context=ctx)


def reference_list_json(request, lgr_id, lgr_set_id=None):
    """
    Return the list of defined references as JSON.
    """
    lgr_info = session_select_lgr(request, lgr_id, lgr_set_id)

    references = [{
        'ref_id': ref_id,
        'description': ref.get('value', ''),
        'comment': ref.get('comment', '')
    } for (ref_id, ref) in iteritems(lgr_info.lgr.reference_manager)]

    return HttpResponse(json.dumps(references), content_type='application/json', charset='UTF-8')


@require_POST
def add_reference_ajax(request, lgr_id):
    """
    AJAX interface to create a new reference.
    """
    lgr_info = session_select_lgr(request, lgr_id)
    if lgr_info.is_set:
        return HttpResponseBadRequest('Cannot edit LGR set')

    add_reference_form = ReferenceForm(request.POST)
    if add_reference_form.is_valid():
        ref_id = add_reference_form.cleaned_data['ref_id'] or None
        description = add_reference_form.cleaned_data['description']
        url = add_reference_form.cleaned_data['comment']
        try:
            lgr_info.lgr.reference_manager.add_reference(description, url, ref_id=ref_id)
            session_save_lgr(request, lgr_info)
            references = [{
                              'ref_id': ref_id,
                              'description': ref.get('value', ''),
                              'comment': ref.get('comment', '')
                          } for (ref_id, ref) in iteritems(lgr_info.lgr.reference_manager)]
            rv = {'ok': True, 'data': references}
        except LGRException as ex:
            rv = {'ok': False, 'error': lgr_exception_to_text(ex)}

        return HttpResponse(json.dumps(rv), content_type='application/json', charset='UTF-8')
    else:
        return HttpResponseBadRequest(add_reference_form.errors)


def delete_reference(request, lgr_id, ref_id):
    """
    Delete a reference from an LGR.
    """
    logger.debug("Delete reference %s'", ref_id)
    lgr_info = session_select_lgr(request, lgr_id)
    if lgr_info.is_set:
        return HttpResponseBadRequest('Cannot edit LGR set')

    try:
        lgr_info.lgr.del_reference(ref_id)
        session_save_lgr(request, lgr_info)
    except LGRException as ex:
        messages.add_message(request, messages.ERROR,
                             lgr_exception_to_text(ex))

    return redirect('references', lgr_id)


def tag_list(request, lgr_id, lgr_set_id=None):
    """
        List/edit tags of an LGR.
    """
    lgr_info = session_select_lgr(request, lgr_id, lgr_set_id)

    tag_classes = lgr_info.lgr.get_tag_classes()

    tags = [{
        'name': tag,
        'nb_cp':  len(clz.codepoints),
        'view_more': len(clz.codepoints) > TRUNCATE_AFTER_N_CP_TAGS,
        'codepoints': [{
            'cp_disp': render_cp_or_sequence(c),
            'cp_id': cp_to_slug((c, )),
        } for c in islice(clz.codepoints, TRUNCATE_AFTER_N_CP_TAGS)]
    } for tag, clz in tag_classes.items()]

    ctx = {
        'tags': tags,
        'lgr': lgr_info.lgr,
        'lgr_id': lgr_id,
        'is_set': lgr_info.is_set or lgr_set_id is not None
    }
    if lgr_set_id:
        lgr_set_info = session_select_lgr(request, lgr_set_id)
        ctx['lgr_set'] = lgr_set_info.lgr
        ctx['lgr_set_id'] = lgr_set_id

    return render(request, 'lgr_editor/tags.html', context=ctx)


def tag_list_json(request, tag_id, lgr_id, lgr_set_id=None):
    """
    Return the full list of code points associated with a tag in JSON.
    """
    lgr_info = session_select_lgr(request, lgr_id, lgr_set_id)

    tag_classes = lgr_info.lgr.get_tag_classes()
    if tag_id not in tag_classes:
        # Error
        return

    clz = tag_classes[tag_id]

    data = []
    cp_list = []
    for c in clz.codepoints:
        cp_slug = cp_to_slug((c, ))
        kwargs = {'lgr_id': lgr_id, 'codepoint_id': cp_slug}
        if lgr_set_id is not None:
            kwargs['lgr_set_id'] = lgr_set_id
        cp_view_url = reverse('codepoint_view', kwargs=kwargs)
        obj = {'cp_disp': render_cp_or_sequence(c), 'cp_view': cp_view_url}
        cp_list.append(obj)
        if len(cp_list) == 10:
            data.append(cp_list)
            cp_list = []
    # Do not forget to add the remaining code points, if any
    if cp_list:
        data.append(cp_list)

    response = {'data': data}
    return JsonResponse(response)


def delete_tag(request, lgr_id, tag_id):
    """
    Delete a tag from an LGR.
    """
    logger.debug("Delete tag %s'", tag_id)
    lgr_info = session_select_lgr(request, lgr_id)
    if lgr_info.is_set:
        return HttpResponseBadRequest('Cannot edit LGR set')

    try:
        lgr_info.lgr.del_tag(tag_id)
        session_save_lgr(request, lgr_info)
    except LGRException as ex:
        messages.add_message(request, messages.ERROR,
                             lgr_exception_to_text(ex))
    else:
        messages.add_message(request, messages.INFO,
                             _("References to tag %(tag)s have been removed from the repertoire. "
                               "Do not forget to update any WLE that might reference it.") % {'tag': tag_id})

    return redirect('tags', lgr_id)


def rule_list_simple(request, lgr_id, lgr_set_id=None):
    """
    Display a verbatim view of the <rules> section.
    """
    lgr_info = session_select_lgr(request, lgr_id, lgr_set_id)

    rules = {
        'classes': '\n\n'.join(lgr_info.lgr.classes_xml),
        'rules': '\n\n'.join(lgr_info.lgr.rules_xml),
        'actions': '\n\n'.join(lgr_info.lgr.actions_xml),
    }
    ctx = {
        'rules': rules,
        'lgr': lgr_info.lgr,
        'lgr_id': lgr_id,
        'is_set': lgr_info.is_set or lgr_set_id is not None
    }
    if lgr_set_id:
        lgr_set_info = session_select_lgr(request, lgr_set_id)
        ctx['lgr_set'] = lgr_set_info.lgr
        ctx['lgr_set_id'] = lgr_set_id

    return render(request, 'lgr_editor/rules.html', context=ctx)


# TODO - warn if the LGR already has duplicate classes or rules, we cannot reliably work on them
# TODO - prevent class or rule from being deleted if it is being referenced
# TODO - convert functional views into into CBV


def _del_class(lgr, clsname):
    del lgr.classes_lookup[clsname]
    i = lgr.classes.index(clsname)
    del lgr.classes[i]
    del lgr.classes_xml[i]


def _update_class(lgr, clsname, cls, body):
    if clsname in lgr.classes_lookup:
        del lgr.classes_lookup[clsname]     # `clsname` is the existing class name, `cls.name` is new (could be different)
        lgr.classes_lookup[cls.name] = cls
        i = lgr.classes.index(clsname)
        lgr.classes[i] = clsname
        lgr.classes_xml[i] = body
    else:
        lgr.add_class(cls)
        lgr.classes_xml.append(body)


def _json_response(success, error_msg=None):
    rv = {'success': success}
    if error_msg:
        rv['message'] = force_text(error_msg)
    return HttpResponse(json.dumps(rv), content_type='application/json', charset='UTF-8')


@require_POST
def rule_edit_class_ajax(request, lgr_id, clsname):
    delete_action = request.POST.get('delete')
    body = request.POST.get('body')

    if not delete_action and not body:
        return _json_response(False, _('No body specified'))

    lgr_info = session_select_lgr(request, lgr_id)
    if lgr_info.is_set:
        return HttpResponseBadRequest('Cannot edit LGR set')

    lgr = lgr_info.lgr

    if clsname not in lgr.classes_lookup and clsname != NEW_ELEMENT_NAME_PARAM:
        return _json_response(False, _('Class "%s" does not exist') % clsname)

    if delete_action:
        _del_class(lgr, clsname)
        msg = _('Class "%s" deleted.') % clsname
    else:
        try:
            cls = _parse_class(body)
            if not cls:
                return _json_response(False, _('No class element found'))
            if cls.name is None:
                return _json_response(False, _('Name attribute must be present'))
        except LGRException as e:
            return _json_response(False, lgr_exception_to_text(e))
        except XMLSyntaxError as e:
            return _json_response(False, _('Encountered XML syntax error: %s (line number may be wrong, '
                                           'try subtracting one from the reported line number)') % (e,))
        except Exception:
            return _json_response(False, _('Your XML is not valid'))

        if clsname != cls.name:
            # user has renamed the class, check that there is no dupe
            if cls.name in lgr.classes_lookup:
                return _json_response(False, _('Class "%s" already exists') % cls.name)
        _update_class(lgr, clsname, cls, body)
        msg = _('Class "%s" saved.') % cls.name

    try:
        session_save_lgr(request, lgr_info)
    except LGRException as e:
        return _json_response(False, lgr_exception_to_text(e))
    except XMLSyntaxError as e:
        return _json_response(False, _('Encountered XML syntax error: %s (line number may be wrong, '
                                       'try subtracting one from the reported line number)') % (e,))
    except Exception:
        return _json_response(False, _('Your XML is not valid'))
    return _json_response(True, msg)


NEW_ELEMENT_NAME_PARAM = '__new__'

# In `LGR_SKEL` below, the content preceding `{xml}` should be on a single line, so that the line
# number reported in error messages can be more consistent.
# Skel contains fake char in order to get a valid RNG
LGR_SKEL = '''<lgr xmlns="{ns}"><meta /><data><char cp="0061"/></data><rules>
{xml}
</rules></lgr>'''

CLASS_SKEL = '''<class name="{}" comment="EXAMPLE - last letter of the English alphabet">007A</class>'''

RULE_SKEL = '''<rule name="{}" comment="EXAMPLE - must be the start of label">
  <start/>
</rule>'''

ACTION_SKEL = '''<action disp="blocked" comment="EXAMPLE - disallowed"/>'''


def _parse_class(xml):
    lgr_xml = LGR_SKEL.format(ns=LGR_NS, xml=xml).encode('utf-8')
    lgr_info = LGRInfo.from_dict(
        {
            'xml': lgr_xml,
            'validate': False,
        },
        lgr_loader_func=None
    )
    if lgr_info.lgr.classes_lookup:
        return list(lgr_info.lgr.classes_lookup.values())[0]
    else:
        return None


def rule_list(request, lgr_id, lgr_set_id=None):
    """
    Edit rules
    """
    lgr_info = session_select_lgr(request, lgr_id, lgr_set_id)

    # set
    if lgr_info.is_set or lgr_set_id is not None:
        return rule_list_simple(request, lgr_id, lgr_set_id)

    lgr = lgr_info.lgr
    rules = {
        'classes': [{'name': cls_name, 'content': cls_xml} for cls_name, cls_xml in zip(lgr.classes, lgr.classes_xml)],
        'rules': [{'name': rule_name, 'content': rule_xml} for rule_name, rule_xml in zip(lgr.rules, lgr.rules_xml)],
        'actions': [{'name': action_idx, 'content': action_xml} for action_idx, action_xml in enumerate(lgr.actions_xml)],
    }

    # try to suggest a non-clashing class name, but a clash should not be catastrophic
    for i in range(20):
        new_class_name = 'untitled-class-{}'.format(i)
        if new_class_name not in lgr_info.lgr.classes_lookup:
            break

    for i in range(20):
        new_rule_name = 'untitled-rule-{}'.format(i)
        if new_rule_name not in lgr_info.lgr.rules_lookup:
            break

    ctx = {
        'rules': rules,
        'class_skeleton': CLASS_SKEL.format(new_class_name),
        'rule_skeleton': RULE_SKEL.format(new_rule_name),
        'action_skeleton': ACTION_SKEL,
        'lgr': lgr_info.lgr,
        'lgr_id': lgr_id,
        'NEW_ELEMENT_NAME_PARAM': NEW_ELEMENT_NAME_PARAM,
        'is_set': False
    }

    return render(request, 'lgr_editor/rules_edit.html', context=ctx)


def _del_rule(lgr, rule_name):
    del lgr.rules_lookup[rule_name]
    i = lgr.rules.index(rule_name)
    del lgr.rules[i]
    del lgr.rules_xml[i]


def _update_rule(lgr, rule_name, rule, body):
    if rule_name in lgr.rules_lookup:
        del lgr.rules_lookup[rule_name]    # `rule_name` is the existing rule name, `rule.name` is new (could be different)
        lgr.rules_lookup[rule.name] = rule
        i = lgr.rules.index(rule_name)
        lgr.rules[i] = rule_name
        lgr.rules_xml[i] = body
    else:
        lgr.add_rule(rule)
        lgr.rules_xml.append(body)


def _parse_rule(xml):
    lgr_xml = LGR_SKEL.format(ns=LGR_NS, xml=xml).encode('utf-8')
    lgr_info = LGRInfo.from_dict(
        {
            'xml': lgr_xml,
            'validate': True
        },
        lgr_loader_func=None
    )
    if lgr_info.lgr.rules_lookup:
        return list(lgr_info.lgr.rules_lookup.values())[0]
    else:
        return None


@require_POST
def rule_edit_rule_ajax(request, lgr_id, rulename):
    delete_action = request.POST.get('delete')
    body = request.POST.get('body')

    if not delete_action and not body:
        return _json_response(False, _('No body specified'))

    lgr_info = session_select_lgr(request, lgr_id)
    if lgr_info.is_set:
        return HttpResponseBadRequest('Cannot edit LGR set')

    lgr = lgr_info.lgr

    if rulename not in lgr.rules_lookup and rulename != NEW_ELEMENT_NAME_PARAM:
        return _json_response(False, _('Rule "%s" does not exist') % rulename)

    if delete_action:
        _del_rule(lgr, rulename)
        msg = _('Rule "%s" deleted.') % rulename
    else:
        try:
            rule = _parse_rule(body)
            if not rule:
                return _json_response(False, _('No rule element found'))
        except LGRException as e:
            return _json_response(False, lgr_exception_to_text(e))
        except XMLSyntaxError as e:
            return _json_response(False, _('Encountered XML syntax error: %s (line number may be wrong, '
                                           'try subtracting one from the reported line number)') % (e,))
        except Exception:
            return _json_response(False, _('Your XML is not valid'))

        if rulename != rule.name:
            # user has renamed the rule, check that there is no dupe
            if rule.name in lgr.rules_lookup:
                return _json_response(False, _('Rule "%s" already exists') % rule.name)
        _update_rule(lgr, rulename, rule, body)
        msg = _('Rule "%s" saved.') % rule.name

    try:
        session_save_lgr(request, lgr_info)
    except LGRException as e:
        return _json_response(False, lgr_exception_to_text(e))
    except XMLSyntaxError as e:
        return _json_response(False, _('Encountered XML syntax error: %s (line number may be wrong, '
                                       'try subtracting one from the reported line number)') % (e,))
    except Exception:
        return _json_response(False, _('Your XML is not valid'))
    return _json_response(True, msg)


def _del_action(lgr, idx):
    del lgr.actions[idx]
    action_xml = lgr.actions_xml.pop(idx)
    logger.debug('deleted action[%d]: %s', idx, action_xml)


def _update_action(lgr, idx, action, body):
    if 0 <= idx < len(lgr.actions):
        lgr.actions[idx] = action
        lgr.actions_xml[idx] = body
    else:
        lgr.add_action(action)
        lgr.actions_xml.append(body)


def _parse_action(xml):
    lgr_xml = LGR_SKEL.format(ns=LGR_NS, xml=xml).encode('utf-8')
    lgr_info = LGRInfo.from_dict(
        {
            'xml': lgr_xml,
            'validate': False
        },
        lgr_loader_func=None
    )
    if lgr_info.lgr.actions:
        return lgr_info.lgr.actions[0]
    else:
        return None


@require_POST
def rule_edit_action_ajax(request, lgr_id, action_idx):
    delete_action = request.POST.get('delete')
    body = request.POST.get('body')

    if not delete_action and not body:
        return _json_response(False, _('No body specified'))

    lgr_info = session_select_lgr(request, lgr_id)
    if lgr_info.is_set:
        return HttpResponseBadRequest('Cannot edit LGR set')

    lgr = lgr_info.lgr

    action_idx = int(action_idx) # 0-based
    # negative action_idx means to add new
    if action_idx + 1 > len(lgr.actions):
        return _json_response(False, _('Action "%s" does not exist') % action_idx)

    if delete_action:
        _del_action(lgr, action_idx)
        msg = _('Action "%s" deleted.') % action_idx
    else:
        try:
            action = _parse_action(body)
            if not action:
                return _json_response(False, _('No action element found'))
        except LGRException as e:
            return _json_response(False, lgr_exception_to_text(e))
        except XMLSyntaxError as e:
            return _json_response(False, _('Encountered XML syntax error: %s (line number may be wrong, '
                                           'try subtracting one from the reported line number)') % (e,))
        except Exception:
            return _json_response(False, _('Your XML is not valid'))

        _update_action(lgr, action_idx, action, body)
        msg = _('Action saved.')

    try:
        session_save_lgr(request, lgr_info)
    except LGRException as e:
        return _json_response(False, lgr_exception_to_text(e))
    except XMLSyntaxError as e:
        return _json_response(False, _('Encountered XML syntax error: %s (line number may be wrong, '
                                       'try subtracting one from the reported line number)') % (e,))
    except Exception:
        return _json_response(False, _('Your XML is not valid'))
    return _json_response(True, msg)


class MultiCodepointsView(FormView):
    """
    Basic view to handle some kind of input which generates a list of
    codepoints.

    It first presents the `form_class` to get inputs from user.
    Then, it renders the `AddMultiCodepointsForm` with the choices.
    """
    template_name = 'lgr_editor/add_list.html'
    success_template_name = 'lgr_editor/add_list_success.html'

    def __init__(self, discrete_cp=False):
        super(MultiCodepointsView, self).__init__()
        self.lgr_info = None
        self.unidata = None
        self.discrete_cp = discrete_cp

    def post(self, request, *args, **kwargs):
        self.lgr_info = session_select_lgr(self.request, self.kwargs['lgr_id'])
        if self.lgr_info.is_set:
            return HttpResponseBadRequest('Cannot edit LGR set')

        self.unidata = unidb.manager.get_db_by_version(self.lgr_info.lgr.metadata.unicode_version)

        tmp_lgr_info = None
        if 'tmp_lgr' in request.POST:
            tmp_lgr_name = self.request.POST.get('tmp_lgr')
            if tmp_lgr_name:
                for saved_lgr in session_list_lgr(self.request):
                    if tmp_lgr_name == saved_lgr['name']:
                        tmp_lgr_info = session_select_lgr(self.request, tmp_lgr_name)
                if not tmp_lgr_info:
                    logger.warning("Unable to find temporary LGR, won't be able to "
                                   "get variants")
                    session_delete_lgr(request, tmp_lgr_name)
        if 'codepoint' in request.POST:
            # assume that we are submitting the `AddMultiCodepointsForm`
            codepoints = [slug_to_cp(cp) for cp in self.request.POST.getlist('codepoint')]
            if self.discrete_cp:
                for cp in codepoints:
                    self.lgr_info.lgr.add_cp(cp)
                    # find variants in temporary LGR
                    if tmp_lgr_info:
                        for variant in tmp_lgr_info.lgr.get_variants(cp):
                            self.lgr_info.lgr.add_variant(cp, variant.cp)
            else:
                # slug_to_cp returns a list of tuples, add codepoints need a
                # list. There is not variant here so taking first element of the
                # tuple is correct
                codepoints = [x[0] for x in codepoints]
                self.lgr_info.lgr.add_codepoints(codepoints)
                # no variants in range
            session_save_lgr(request, self.lgr_info)
            messages.add_message(self.request,
                                 messages.SUCCESS,
                                 _("%d code points added") % len(codepoints))
            # remove temporary LGR
            if tmp_lgr_info:
                session_delete_lgr(request, tmp_lgr_info.name)
            return self.render_success_page()

        return super(MultiCodepointsView, self).post(request, *args, **kwargs)

    def render_success_page(self):
        return TemplateResponse(
            request=self.request,
            template=self.success_template_name,
            context={'url': reverse('codepoint_list', args=(self.kwargs['lgr_id'],))},
            using=self.template_engine,
        )

    def format_cp_choice(self, cp):
        slug = cp_to_slug(cp)
        return (slug, format_html_join('', 'U+{} {}',
                                       (('{:04X}'.format(c), self.unidata.get_char_name(c)) for c in cp)))

    def _handle_discrete(self, lgr, input_lgr, manual):
        logger.debug("Import: Copy references")
        # No choice here, we have to import references
        for (ref_id, ref) in iteritems(input_lgr.reference_manager):
            value = ref['value']
            comment = ref.get('comment', None)
            try:
                lgr.add_reference(value, comment, ref_id=ref_id)
            except LGRException:
                logger.warning("Cannot add reference: '%s'", ref_id)

        if manual:
            # Start by expanding all ranges in manual mode
            input_lgr.expand_ranges()
            # we now use `AddMultiCodepointsForm` to present the list of code points
            range_form = AddMultiCodepointsForm()

            # Do note that importing codepoints from a file in manual mode
            # will lose some data from the file:
            #  - No codepoint attributes (comments, references, etc.)
            codepoint = []
            disabled_codepoint = []
            for char in input_lgr.repertoire:
                try:
                    lgr.add_cp(char.cp,
                               comment=char.comment,
                               ref=char.references,
                               validating_repertoire=self.lgr_info.validating_repertoire)
                except LGRException:
                    disabled_codepoint.append(self.format_cp_choice(char.cp))
                else:
                    codepoint.append(self.format_cp_choice(char.cp))

            if len(codepoint) == 0:
                messages.add_message(self.request,
                                     messages.ERROR,
                                     _("No code point in input file"))
                return self.render_to_response(self.get_context_data())

            # Save LGR in sessions in order to retrieve variants in post
            tmp_lgr_id = input_lgr.name
            tmp_lgr_id = tmp_lgr_id
            if tmp_lgr_id.endswith('.txt'):
                tmp_lgr_id = tmp_lgr_id.rsplit('.', 1)[0]
            tmp_lgr_id += '_tmp'
            tmp_lgr_id = slugify(tmp_lgr_id)
            if tmp_lgr_id in [saved_lgr['name'] for saved_lgr in session_list_lgr(self.request)]:
                # The temporary LGR already exists... This should not happen
                logger.warning("Temporary LGR already exists...")
            else:
                tmp_lgr_info = session_new_lgr(self.request, tmp_lgr_id,
                                               lgr.metadata.unicode_version,
                                               self.lgr_info.validating_repertoire.name if self.lgr_info.validating_repertoire else None)
                self._copy_characters(tmp_lgr_info.lgr, input_lgr, force=True)
                session_save_lgr(self.request, tmp_lgr_info)

            range_form.fields['codepoint'].choices = codepoint
            range_form.fields['disabled_codepoint'].choices = disabled_codepoint
            range_form.fields['tmp_lgr'].initial = tmp_lgr_id
            return self.render_to_response(self.get_context_data(form=range_form))

        # Automatic import
        logger.debug("Import: Copy characters")
        nb_codepoints = self._copy_characters(lgr, input_lgr)
        session_save_lgr(self.request, self.lgr_info)
        messages.add_message(self.request,
                             messages.SUCCESS,
                             _("%d code points added") % nb_codepoints)
        return self.render_success_page()

    def _copy_characters(self, lgr, input_lgr, force=False):
        nb_codepoints = 0
        for char in input_lgr.repertoire:
            char_len = 1
            add_fct = lambda c: lgr.add_cp(c.cp,
                                           comment=c.comment,
                                           ref=c.references,
                                           validating_repertoire=self.lgr_info.validating_repertoire,
                                           force=force)
            if isinstance(char, RangeChar):
                char_len = char.last_cp - char.first_cp + 1
                add_fct = lambda c: lgr.add_range(c.first_cp, c.last_cp,
                                                  comment=c.comment,
                                                  ref=c.references,
                                                  validating_repertoire=self.lgr_info.validating_repertoire,
                                                  force=force)
            try:
                add_fct(char)
                nb_codepoints += char_len
            except LGRException as exc:
                logger.warning("Cannot add code point '%s': %s",
                               format_cp(char.cp),
                               lgr_exception_to_text(exc))
            else:
                for variant in char.get_variants():
                    try:
                        lgr.add_variant(char.cp,
                                        variant.cp,
                                        variant_type=variant.type,
                                        when=variant.when,
                                        not_when=variant.not_when,
                                        comment=variant.comment,
                                        ref=variant.references,
                                        validating_repertoire=self.lgr_info.validating_repertoire,
                                        force=force)
                    except LGRException as exc:
                        logger.warning("Cannot add variant '%s' to "
                                       "code point '%s': %s",
                                       format_cp(variant.cp),
                                       format_cp(char.cp),
                                       lgr_exception_to_text(exc))
        return nb_codepoints


class AddRangeView(MultiCodepointsView):
    """
    This view uses the `AddRangeForm` form to accept the `first_cp` and
    `last_cp` inputs from user.
    """
    form_class = AddRangeForm
    template_name = 'lgr_editor/add_list_range.html'

    def form_valid(self, form):
        # we now use `AddMultiCodepointsForm` to present the list of code points
        self.template_name = 'lgr_editor/add_list.html'
        range_form = AddMultiCodepointsForm()
        cd = form.cleaned_data
        # populate the choices with code points of the view
        codepoint_status = self.lgr_info.lgr.check_range(cd['first_cp'],
                                                         cd['last_cp'],
                                                         validating_repertoire=self.lgr_info.validating_repertoire)

        codepoint = []
        disabled_codepoint = []
        for (cp, status) in codepoint_status:
            if status is None:
                codepoint.append(self.format_cp_choice((cp, )))
            elif isinstance(status, LGRException):
                disabled_codepoint.append(self.format_cp_choice((cp, )))
        range_form.fields['codepoint'].choices = codepoint
        range_form.fields['disabled_codepoint'].choices = disabled_codepoint
        return self.render_to_response(self.get_context_data(form=range_form))


class ImportCodepointsFromFileView(MultiCodepointsView):
    """
    This view uses the `ImportCodepointsFromFileForm` form to parse a file.
    """
    form_class = ImportCodepointsFromFileForm
    template_name = 'lgr_editor/add_list_import.html'

    def __init__(self):
        # Importing codepoint from file should insert discrete codepoints
        super(ImportCodepointsFromFileView, self).__init__(discrete_cp=True)

    def form_valid(self, form):
        self.template_name = 'lgr_editor/add_list.html'
        cd = form.cleaned_data

        logger.debug("Import CP from file")
        # Get the type of input file and send it to LGR Core
        # Assume encoded in UTF-8
        file = StringIO(cd['file'].read().decode('utf-8'))
        type = cd['type']

        parser_cls = INPUT_FILE_PARSER.get(type, None)
        if parser_cls is None:
            logger.error("Unknown type '%s'", type)
            # Re-render the context data with the data-filled form and errors.
            return self.render_to_response(self.get_context_data(form=form))

        lgr = self.lgr_info.lgr
        parser = parser_cls(file, filename=cd['file'].name)
        input_lgr = parser.parse_document()
        return self._handle_discrete(lgr, input_lgr, cd['manual_import'])


class AddCodepointFromScriptView(MultiCodepointsView):
    """
    This view uses the `AddCodepointFromScriptForm` form to retrieve code points from script based on MSR or
    IDNA2008.
    """
    form_class = AddCodepointFromScriptForm
    template_name = 'lgr_editor/add_list_from_script.html'

    def get(self, request, *args, **kwargs):
        self.lgr_info = session_select_lgr(request, kwargs['lgr_id'])
        if self.lgr_info.is_set:
            return HttpResponseBadRequest('Cannot edit LGR set')

        scripts = get_all_scripts_from_repertoire(self.lgr_info.lgr.unicode_database)
        self.initial['scripts'] = [(s, s) for s in sorted(scripts)]

        return super(AddCodepointFromScriptView, self).get(request, *args, **kwargs)

    def form_valid(self, form):
        self.template_name = 'lgr_editor/add_list.html'

        lgr = self.lgr_info.lgr
        cd = form.cleaned_data
        script = cd['script']
        validating_repertoire = get_by_name(cd['validating_repertoire'])
        validating_repertoire.expand_ranges()  # need to get through all code points

        codepoints = []
        for char in validating_repertoire.repertoire.all_repertoire():
            # XXX: Assume validating repertoire only contains single CP
            cp = char.cp[0]
            if script == self.lgr_info.lgr.unicode_database.get_script(cp, alpha4=True):
                try:
                    lgr.get_char(cp)
                except LGRException:
                    codepoints.append(cp)

        fake_lgr = LGR(name=script)
        fake_lgr.add_codepoints(codepoints)
        return self._handle_discrete(lgr, fake_lgr, cd['manual_import'])


class MetadataView(FormView):
    """
    This view is used to display the metadata screen.
    """
    form_class = MetadataForm
    template_name = 'lgr_editor/metadata.html'

    def __init__(self):
        super(MetadataView, self).__init__()
        self.lgr_info = None

    def get_form_kwargs(self):
        kwargs = super(MetadataView, self).get_form_kwargs()

        # Set LGR info reference
        self.lgr_info = session_select_lgr(self.request, self.kwargs['lgr_id'], self.kwargs.get('lgr_set_id'))

        metadata = self.lgr_info.lgr.metadata
        language = metadata.languages[0] if len(metadata.languages) > 0 else ""
        scope = metadata.scopes[0] if len(metadata.scopes) > 0 else Scope('')

        description = ""
        description_type = ""
        if metadata.description is not None:
            description = metadata.description.value
            description_type = metadata.description.description_type or ""

        validating_repertoire_name = ""
        if self.lgr_info.validating_repertoire is not None:
            validating_repertoire_name = self.lgr_info.validating_repertoire.name

        kwargs['initial'] = {
            'version': metadata.version.value if metadata.version else "",
            'version_comment': metadata.version.comment if metadata.version else "",
            'date': metadata.date,
            'language': language,
            'scope': scope.value,
            'scope_type': scope.scope_type,
            'unicode_version': metadata.unicode_version,
            'validity_start': metadata.validity_start,
            'validity_end': metadata.validity_end,
            'description': description,
            'description_type': description_type,
            'validating_repertoire': validating_repertoire_name,
        }

        # add other repertoires available in the user's session
        kwargs['additional_repertoires'] = [lgr['name'] for lgr in session_list_lgr(self.request)
                                            if lgr['name'] != self.lgr_info.name]

        kwargs['disabled'] = self.kwargs.get('lgr_set_id') is not None

        return kwargs

    def get_context_data(self, **kwargs):
        ctx = super(MetadataView, self).get_context_data(**kwargs)
        ctx['lgr_id'] = self.kwargs['lgr_id']
        ctx['lgr'] = self.lgr_info.lgr
        language_formset = LanguageFormSet(self.request.POST or None,
                                           prefix='lang',
                                           initial=[{'language': l} for l in
                                                    self.lgr_info.lgr.metadata.languages],
                                           disabled=self.kwargs.get('lgr_set_id') is not None)
        if self.kwargs.get('lgr_set_id'):
            # do not enable to update references for LGRs in a set => do not need an extra widget
            language_formset.extra = 0

        ctx['language_formset'] = language_formset

        ctx['is_set'] = self.lgr_info.is_set or self.kwargs.get('lgr_set_id')

        if self.kwargs.get('lgr_set_id'):
            ctx['lgr_set_id'] = self.kwargs['lgr_set_id']
            ctx['lgr_set'] = session_select_lgr(self.request, self.kwargs.get('lgr_set_id')).lgr
        return ctx

    def form_valid(self, form):
        # main `MetadataForm` is valid, now test for `LanguageFormSet`
        language_formset = LanguageFormSet(self.request.POST, prefix='lang')
        if language_formset.is_valid():
            cd = form.cleaned_data
            metadata = Metadata()

            try:
                if cd['version']:
                    metadata.version = Version(cd['version'], cd['version_comment'] or None)
                else:
                    metadata.version = None

                if cd['date']:
                    metadata.set_date(cd['date'].isoformat())

                # save languages
                metadata.set_languages(filter(None, (f.get('language') for f in language_formset.cleaned_data)))

                if cd['scope']:
                    scope = Scope(value=cd['scope'],
                                  scope_type=cd['scope_type'] or None)
                    if len(metadata.scopes) > 0:
                        metadata.scopes[0] = scope
                    else:
                        metadata.scopes.append(scope)
                if cd['unicode_version']:
                    metadata.set_unicode_version(cd['unicode_version'])
                if cd['validity_start']:
                    metadata.set_validity_start(cd['validity_start'].isoformat())
                if cd['validity_end']:
                    metadata.set_validity_end(cd['validity_end'].isoformat())
                if cd['description']:
                    metadata.description = Description(value=cd['description'],
                                                       description_type=cd['description_type'] or None)

                if cd['validating_repertoire']:
                    self.lgr_info.validating_repertoire = \
                        get_builtin_or_session_repertoire(cd['validating_repertoire'],
                                                          self.request)
                else:
                    self.lgr_info.validating_repertoire = None

                self.lgr_info.lgr.metadata = metadata
                session_save_lgr(self.request, self.lgr_info)
                messages.add_message(self.request,
                                     messages.SUCCESS,
                                     _("Meta data saved"))
                return redirect('metadata', self.kwargs['lgr_id'])  # redirect to myself
            except LGRException as ex:
                messages.add_message(self.request, messages.ERROR,
                                     lgr_exception_to_text(ex))

        context = self.get_context_data(form=form)
        return self.render_to_response(context)


def label_forms(request):
    unicode_versions = ((v, v) for v in settings.SUPPORTED_UNICODE_VERSIONS)
    form = LabelFormsForm(request.POST or None,
                          unicode_versions=unicode_versions)
    ctx = {}
    if form.is_bound and form.is_valid():
        label = form.cleaned_data['label']
        unicode_version = form.cleaned_data['unicode_version']
        udata = unidb.manager.get_db_by_version(unicode_version)
        try:
            ctx['cp_list'] = format_cp(label)
            ctx['u_label'] = cp_to_ulabel(label)
            ctx['a_label'] = udata.idna_encode_label(ctx['u_label'])
        except UnicodeError as ex:
            messages.add_message(request, messages.ERROR,
                                 lgr_exception_to_text(ex))

    ctx['form'] = form
    return render(request, 'lgr_editor/label_forms.html', context=ctx)


def embedded_lgrs(request, lgr_id):
    lgr_info = session_select_lgr(request, lgr_id)
    if not lgr_info.is_set:
        return HttpResponseBadRequest('LGR is not a set')

    ctx = {
        'lgr': lgr_info.lgr,
        'lgr_id': lgr_id,
        'embedded': lgr_info.lgr_set,
        'is_set': True
    }
    return render(request, 'lgr_editor/embedded_lgrs.html', context=ctx)


def about(request):
    """
    Show about dialog
    """
    output = {"versions": settings.SUPPORTED_UNICODE_VERSIONS}
    return render(request,
                  'lgr_editor/about.html',
                  context={'output': output})
