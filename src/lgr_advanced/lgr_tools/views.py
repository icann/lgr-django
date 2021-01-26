# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.conf import settings
from django.shortcuts import render, redirect

from lgr.tools.utils import download_file
from lgr_advanced.lgr_editor.api import session_list_lgr, session_select_lgr, session_get_storage, LabelInfo
from lgr_advanced.lgr_editor.utils import cp_to_slug
from lgr_advanced.lgr_tools.api import lgr_intersect_union, lgr_comp_diff, lgr_harmonization, LGRCompInvalidException
from lgr_advanced.lgr_tools.forms import (LGRCompareSelector,
                                          LGRDiffSelector,
                                          LGRCollisionSelector,
                                          LGRAnnotateSelector,
                                          LGRCrossScriptVariantsSelector,
                                          LGRHarmonizeSelector,
                                          LGRComputeVariantsSelector)
from .tasks import (diff_task,
                    collision_task,
                    annotate_task,
                    lgr_set_annotate_task,
                    cross_script_variants_task,
                    validate_labels_task)


def lgr_compare(request, lgr_id):
    form = LGRCompareSelector(request.POST or None,
                              session_lgrs=session_list_lgr(request),
                              lgr_id=lgr_id)

    lgr_info = None
    if lgr_id is not None:
        lgr_info = session_select_lgr(request, lgr_id)

    if form.is_valid():
        lgr_id_1 = form.cleaned_data['lgr_1']
        lgr_id_2 = form.cleaned_data['lgr_2']
        action = form.cleaned_data['action']

        lgr_info_1 = session_select_lgr(request, lgr_id_1)
        lgr_info_2 = session_select_lgr(request, lgr_id_2)

        if action in ['INTERSECTION', 'UNION']:
            try:
                lgr_id = lgr_intersect_union(request,
                                             lgr_info_1, lgr_info_2,
                                             action)
            except LGRCompInvalidException as lgr_xml:
                from io import BytesIO
                from django.core.files.storage import FileSystemStorage
                from gzip import GzipFile
                from time import strftime

                sio = BytesIO()
                base_filename = '{comp_type}-of-{lgr1}-and-{lgr2}-{date}.xml'.format(
                    comp_type=action.lower(),
                    lgr1=lgr_info_1.name,
                    lgr2=lgr_info_2.name,
                    date=strftime('%Y%m%d_%H%M%S'))
                with GzipFile(filename=base_filename,
                              fileobj=sio, mode='w') as gzf:
                    gzf.write(lgr_xml.content)

                storage = FileSystemStorage(location=session_get_storage(request),
                                            file_permissions_mode=0o440)
                filename = storage.save('{}.gz'.format(base_filename), sio)
                return render(request, 'lgr_tools/comp_invalid.html',
                              context={
                                  'lgr_1': lgr_info_1,
                                  'lgr_2': lgr_info_2,
                                  'lgr_file_name': filename,
                                  'comp_type': action.lower(),
                                  'lgr_id': lgr_id if lgr_id is not None else '',
                                  'lgr': lgr_info.lgr if lgr_info is not None else '',
                                  'is_set': lgr_info.is_set if lgr_info is not None else '',
                                  'error': lgr_xml.error})
            else:
                return redirect('codepoint_list', lgr_id)
        else:
            content = lgr_comp_diff(request, lgr_info_1, lgr_info_2, form.cleaned_data['full_dump'])
            ctx = {
                'content': content,
                'lgr_1': lgr_info_1,
                'lgr_2': lgr_info_2,
                'lgr_id': lgr_id if lgr_id is not None else '',
                'lgr': lgr_info.lgr if lgr_info is not None else '',
                'is_set': lgr_info.is_set if lgr_info is not None else '',
            }
            return render(request, 'lgr_tools/comp_diff.html', context=ctx)

    ctx = {
        'form': form,
        'lgr_id': lgr_id if lgr_id is not None else '',
        'lgr': lgr_info.lgr if lgr_info is not None else '',
        'is_set': lgr_info.is_set if lgr_info is not None else '',
    }

    return render(request, 'lgr_tools/compare.html', context=ctx)


def lgr_diff(request, lgr_id):
    form = LGRDiffSelector(request.POST or None, request.FILES or None,
                           session_lgrs=[lgr['name'] for lgr in session_list_lgr(request) if not lgr['is_set']],
                           lgr_id=lgr_id)

    lgr_info = None
    if lgr_id is not None:
        lgr_info = session_select_lgr(request, lgr_id)

    if form.is_valid():
        lgr_id_1 = form.cleaned_data['lgr_1']
        lgr_id_2 = form.cleaned_data['lgr_2']
        labels_file = form.cleaned_data['labels']
        email_address = form.cleaned_data['email']
        collision = form.cleaned_data['collision']
        full_dump = form.cleaned_data['full_dump']
        with_rules = form.cleaned_data['with_rules']

        lgr_info_1 = session_select_lgr(request, lgr_id_1)
        lgr_info_2 = session_select_lgr(request, lgr_id_2)

        storage_path = session_get_storage(request)

        # need to transmit json serializable data
        labels_json = LabelInfo.from_form(labels_file.name,
                                          labels_file.read()).to_dict()
        lgr_1_json = lgr_info_1.to_dict()
        lgr_2_json = lgr_info_2.to_dict()
        diff_task.delay(lgr_1_json, lgr_2_json, labels_json, email_address, collision,
                        full_dump, with_rules, storage_path)

        ctx = {
            'lgr_1': lgr_info_1,
            'lgr_2': lgr_info_2,
            'labels_file': labels_file.name,
            'email': email_address,
            'lgr_id': lgr_id if lgr_id is not None else '',
            'lgr': lgr_info.lgr if lgr_info is not None else '',
            'is_set': lgr_info.is_set if lgr_info is not None else '',
        }
        return render(request, 'lgr_tools/wait_diff.html', context=ctx)

    ctx = {
        'form': form,
        'lgr_id': lgr_id if lgr_id is not None else '',
        'lgr': lgr_info.lgr if lgr_info is not None else '',
        'is_set': lgr_info.is_set if lgr_info is not None else '',
    }

    return render(request, 'lgr_tools/diff.html', context=ctx)


def lgr_collisions(request, lgr_id):
    form = LGRCollisionSelector(request.POST or None, request.FILES or None,
                                session_lgrs=[lgr['name'] for lgr in session_list_lgr(request) if not lgr['is_set']],
                                lgr_id=lgr_id)

    lgr_info = None
    if lgr_id is not None:
        lgr_info = session_select_lgr(request, lgr_id)

    if form.is_valid():
        lgr_id = form.cleaned_data['lgr']
        labels_file = form.cleaned_data['labels']
        email_address = form.cleaned_data['email']
        full_dump = form.cleaned_data['full_dump']
        with_rules = form.cleaned_data['with_rules']
        with_tlds = False

        lgr_info = session_select_lgr(request, lgr_id)

        storage_path = session_get_storage(request)

        # need to transmit json serializable data
        labels_json = LabelInfo.from_form(labels_file.name, labels_file.read()).to_dict()
        tlds_json = None
        if form.cleaned_data['download_tlds']:
            tlds_json = LabelInfo.from_form('TLDs', download_file(settings.ICANN_TLDS)[1].read().lower()).to_dict()
            with_tlds = True
        lgr_json = lgr_info.to_dict()
        collision_task.delay(lgr_json, labels_json, tlds_json, email_address, full_dump, with_rules,
                             storage_path)

        ctx = {
            'lgr_info': lgr_info,
            'labels_file': labels_file.name,
            'icann_tlds': settings.ICANN_TLDS,
            'with_tlds': with_tlds,
            'email': email_address,
            'lgr_id': lgr_id if lgr_id is not None else '',
            'lgr': lgr_info.lgr if lgr_info is not None else '',
            'is_set': lgr_info.is_set if lgr_info is not None else '',
        }
        return render(request, 'lgr_tools/wait_coll.html', context=ctx)

    ctx = {
        'form': form,
        'lgr_id': lgr_id if lgr_id is not None else '',
        'lgr': lgr_info.lgr if lgr_info is not None else '',
        'is_set': lgr_info.is_set if lgr_info is not None else '',
    }

    return render(request, 'lgr_tools/collision.html', context=ctx)


def _create_set_compatible_form_instance(form_class, request, lgr_id):
    # Retrieve complete list of all scripts defined in all sets
    lgr_scripts = set()
    for lgr_dct in session_list_lgr(request):
        if lgr_dct['is_set']:
            lgr_set = [l['name'] for l in lgr_dct['lgr_set_dct']]
            scripts = []
            for lgr_name in lgr_set:
                lgr_info = session_select_lgr(request, lgr_name, lgr_dct['name'])
                try:
                    scripts.append((lgr_info.name, lgr_info.lgr.metadata.languages[0]))
                except (AttributeError, IndexError):
                    pass
            lgr_scripts |= set(scripts)

    lgr_info = None
    if lgr_id is not None:
        lgr_info = session_select_lgr(request, lgr_id)

    form = form_class(request.POST or None, request.FILES or None,
                      session_lgrs=session_list_lgr(request),
                      lgr_info=lgr_info,
                      scripts=list(lgr_scripts))
    return form


def lgr_annotate(request, lgr_id):
    lgr_info = None
    if lgr_id is not None:
        lgr_info = session_select_lgr(request, lgr_id)

    form = _create_set_compatible_form_instance(LGRAnnotateSelector,
                                                request, lgr_id)
    if form.is_valid():
        ctx = {}
        lgr_id = form.cleaned_data['lgr']
        labels_file = form.cleaned_data['labels']
        email_address = form.cleaned_data['email']

        lgr_info = session_select_lgr(request, lgr_id)

        storage_path = session_get_storage(request)

        # need to transmit json serializable data
        labels_json = LabelInfo.from_form(labels_file.name,
                                          labels_file.read()).to_dict()
        if lgr_info.is_set:
            set_labels_file = form.cleaned_data['set_labels']
            if set_labels_file is not None:
                # Handle label set
                if lgr_info.set_labels_info is None or lgr_info.set_labels_info.name != set_labels_file.name:
                    lgr_info.set_labels_info = LabelInfo.from_form(set_labels_file.name,
                                                                   set_labels_file.read())
        lgr_json = lgr_info.to_dict()
        if not lgr_info.is_set:
            annotate_task.delay(lgr_json, labels_json, email_address, storage_path)
        else:
            script_lgr_id = form.cleaned_data['script']
            script_lgr_info = session_select_lgr(request, script_lgr_id, lgr_set_id=lgr_id)

            script_lgr_json = script_lgr_info.to_dict()
            lgr_set_annotate_task.delay(lgr_json, script_lgr_json, labels_json, email_address, storage_path)
            ctx['script'] = script_lgr_id

        ctx.update({
            'lgr_info': lgr_info,
            'labels_file': labels_file.name,
            'email': email_address,
            'lgr_id': lgr_id if lgr_id is not None else '',
            'lgr': lgr_info.lgr if lgr_info is not None else '',
            'is_set': lgr_info.is_set if lgr_info is not None else '',
        })
        return render(request, 'lgr_tools/wait_annotate.html', context=ctx)

    ctx = {
        'form': form,
        'lgr_id': lgr_id if lgr_id is not None else '',
        'lgr': lgr_info.lgr if lgr_info is not None else '',
        'is_set': lgr_info.is_set if lgr_info is not None else '',
    }

    return render(request, 'lgr_tools/annotate.html', context=ctx)


def lgr_cross_script_variants(request, lgr_id):
    lgr_info = None
    if lgr_id is not None:
        lgr_info = session_select_lgr(request, lgr_id)

    form = _create_set_compatible_form_instance(LGRCrossScriptVariantsSelector,
                                                request, lgr_id)

    if form.is_valid():
        ctx = {}
        lgr_id = form.cleaned_data['lgr']
        labels_file = form.cleaned_data['labels']
        email_address = form.cleaned_data['email']

        lgr_info = session_select_lgr(request, lgr_id)

        storage_path = session_get_storage(request)

        # need to transmit json serializable data
        labels_json = LabelInfo.from_form(labels_file.name,
                                          labels_file.read()).to_dict()

        if lgr_info.is_set:
            script_lgr_id = form.cleaned_data['script']
            script_lgr = session_select_lgr(request, script_lgr_id,
                                            lgr_set_id=lgr_id)
            lgr_info = script_lgr

        cross_script_variants_task.delay(lgr_info.to_dict(), labels_json,
                                         email_address, storage_path)

        ctx.update({
            'lgr_info': lgr_info,
            'labels_file': labels_file.name,
            'email': email_address,
        })
        return render(request, 'lgr_tools/wait_cross_scripts.html', context=ctx)

    ctx = {
        'form': form,
        'lgr_id': lgr_id if lgr_id is not None else '',
        'lgr': lgr_info.lgr if lgr_info is not None else '',
        'is_set': lgr_info.is_set if lgr_info is not None else '',
    }

    return render(request, 'lgr_tools/cross_script_variants.html', context=ctx)


def lgr_harmonize(request, lgr_id):
    form = LGRHarmonizeSelector(request.POST or None,
                                session_lgrs=[lgr['name'] for lgr in session_list_lgr(request) if not lgr['is_set']],
                                lgr_id=lgr_id)

    if form.is_valid():
        ctx = {}
        lgr_1_id, lgr_2_id = form.cleaned_data['lgr_1'], form.cleaned_data['lgr_2']
        rz_lgr_id = form.cleaned_data['rz_lgr'] or None

        lgr_1_info, lgr_2_info = (session_select_lgr(request, l) for l in (lgr_1_id, lgr_2_id))
        rz_lgr = session_select_lgr(request, rz_lgr_id).lgr if rz_lgr_id is not None else None

        h_lgr_1_id, h_lgr_2_id, cp_review = lgr_harmonization(request, lgr_1_info.lgr, lgr_2_info.lgr, rz_lgr)

        ctx.update({
            'lgr_1': lgr_1_info,
            'lgr_2': lgr_2_info,
            'h_lgr_1_id': h_lgr_1_id,
            'h_lgr_2_id': h_lgr_2_id,
            'cp_review': ((h_lgr_1_id, ((c, cp_to_slug(c)) for c in cp_review[0])),
                          (h_lgr_2_id, ((c, cp_to_slug(c)) for c in cp_review[1]))),
            'has_cp_review': bool(cp_review[0]) or bool(cp_review[1])
        })
        return render(request, 'lgr_tools/harmonization_result.html', context=ctx)

    ctx = {
        'form': form,
        'lgr_id': lgr_id if lgr_id is not None else ''
    }

    return render(request, 'lgr_tools/harmonize.html', context=ctx)


def lgr_compute_variants(request, lgr_id):
    form = LGRComputeVariantsSelector(request.POST or None, request.FILES or None,
                                      session_lgrs=[lgr['name'] for lgr in session_list_lgr(request) if
                                                    not lgr['is_set']],
                                      lgr_id=lgr_id)

    lgr_info = None
    if lgr_id is not None:
        lgr_info = session_select_lgr(request, lgr_id)

    if form.is_valid():
        lgr_id = form.cleaned_data['lgr']
        labels_file = form.cleaned_data['labels']
        email_address = form.cleaned_data['email']

        lgr_info = session_select_lgr(request, lgr_id)

        storage_path = session_get_storage(request)

        # need to transmit json serializable data
        labels_json = LabelInfo.from_form(labels_file.name, labels_file.read()).to_dict()
        lgr_json = lgr_info.to_dict()
        validate_labels_task.delay(lgr_json, labels_json, email_address, storage_path)

        ctx = {
            'lgr_info': lgr_info,
            'labels_file': labels_file.name,
            'email': email_address,
            'lgr_id': lgr_id if lgr_id is not None else '',
            'lgr': lgr_info.lgr if lgr_info is not None else '',
            'is_set': lgr_info.is_set if lgr_info is not None else '',
        }
        return render(request, 'lgr_tools/wait_variants.html', context=ctx)

    ctx = {
        'form': form,
        'lgr_id': lgr_id if lgr_id is not None else '',
        'lgr': lgr_info.lgr if lgr_info is not None else '',
        'is_set': lgr_info.is_set if lgr_info is not None else '',
    }

    return render(request, 'lgr_tools/variants.html', context=ctx)
