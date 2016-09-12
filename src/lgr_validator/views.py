# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import json
import csv
from django.http import HttpResponse
from django.shortcuts import render
from django.conf import settings
from django.utils.encoding import force_bytes
from lgr_validator.api import evaluate_label

select_lgr = getattr(__import__(settings.LGR_SELECTOR_FUNC.rpartition('.')[0],
                                fromlist=[settings.LGR_SELECTOR_FUNC.rpartition('.')[0]]),
                     settings.LGR_SELECTOR_FUNC.rpartition('.')[2])

get_unidb = getattr(__import__(settings.UNIDB_LOADER_FUNC.rpartition('.')[0],
                               fromlist=[settings.UNIDB_LOADER_FUNC.rpartition('.')[0]]),
                    settings.UNIDB_LOADER_FUNC.rpartition('.')[2])


def validate_label(request, lgr_id,
                   threshold_include_vars=settings.LGR_VALIDATOR_MAX_VARS_DISPLAY_INLINE,
                   output_func=None):
    lgr_info = select_lgr(request, lgr_id)
    ctx = {}
    input_label = request.GET.get('label', '')
    if input_label:
        label_cplist = [ord(c) for c in input_label]
        ctx = evaluate_label(lgr_info.lgr, label_cplist, threshold_include_vars=threshold_include_vars,
                             idna_encoder=get_unidb(lgr_info.lgr.metadata.unicode_version).idna_encode_label)

    ctx['label'] = input_label
    ctx['lgr_id'] = lgr_id
    ctx['max_label_len'] = lgr_info.lgr.max_label_length()
    if output_func:
        return output_func(ctx)
    else:
        return render(request, 'lgr_validator/validator.html', context=ctx)


def validate_label_json(request, lgr_id):
    return validate_label(request, lgr_id, threshold_include_vars=-1,
                          output_func=lambda ctx: HttpResponse(json.dumps(ctx), content_type='application/json'))


def validate_label_csv(request, lgr_id):
    return validate_label(request, lgr_id, threshold_include_vars=-1,
                          output_func=_prepare_csv_response)


def _prepare_csv_response(ctx):
    response = HttpResponse(content_type='text/csv')
    cd = 'attachment; filename="lgr-val-{0}.csv"'.format(ctx['a_label'])
    response['Content-Disposition'] = cd

    writer = csv.writer(response)
    writer.writerow([b'Type', b'U-label', b'A-label', b'Disposition',
                     b'Code point sequence', b'Action index', b'Action XML'])
    writer.writerow(map(force_bytes,
                        ['original', ctx['u_label'], ctx['a_label'], ctx['disposition'],
                         ctx['cp_display'], ctx['action_idx'], ctx['action']]))
    for var in ctx.get('variants', []):
        writer.writerow(map(force_bytes,
                            ['varlabel', var['u_label'], var['a_label'], var['disposition'],
                             var['cp_display'], var['action_idx'], var['action']]))

    return response
