import codecs
import csv

from django.utils.safestring import mark_safe
from django.utils.translation import gettext_lazy as _
from lgr.core import LGR
from lgr.tools.diff_collisions import get_collisions
from lgr.utils import cp_to_ulabel

from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_web.config import get_lgr_settings


def _get_validity(lgr, label_cplist, idna_encoder):
    label_u = cp_to_ulabel(label_cplist)
    conversion_error = False
    try:
        label_a = idna_encoder(label_u)
    except UnicodeError as e:
        label_a = lgr_exception_to_text(e)
        conversion_error = True

    (eligible, label_valid_parts, label_invalid_parts, disp, action_idx, logs) = lgr.test_label_eligible(label_cplist)

    invalid_codepoints = set([c for c, _ in label_invalid_parts])

    def format_cphex(c, want_html=True):
        if want_html and c in invalid_codepoints:
            return u'<span class="text-danger not-in-rep">U+{:04X} (&#{};)</span>'.format(c, c)
        else:
            return u"U+{:04X} (&#{};)".format(c, c)

    label_display_html = mark_safe(u' '.join(map(format_cphex, label_cplist)))
    label_display_text = u' '.join(u"U+{:04X}".format(cp) for cp in label_cplist)

    lgr_actions = lgr.effective_actions_xml  # save it once (since `lgr.effective_actions` is dynamically computed)
    return {
        'u_label': label_u,
        'a_label': label_a,
        'conversion_error': conversion_error,
        'cp_display_html': label_display_html,
        'cp_display': label_display_text,
        'eligible': eligible,
        'disposition': disp,
        'label_invalid_parts': label_invalid_parts,
        'action_idx': action_idx,
        'action': lgr_actions[action_idx] if action_idx >= 0 else None,
        'logs': logs
    }, lgr_actions


def _get_variants(lgr: LGR, label_cplist, ignore_thresholds, idna_encoder, lgr_actions,
                  hide_mixed_script_variants=False):
    lgr_settings = get_lgr_settings()
    res = {}
    var_results = []
    summary, label_dispositions = lgr.compute_label_disposition_summary(
        label_cplist, include_invalid=True, hide_mixed_script_variants=hide_mixed_script_variants)
    res['summary'] = ", ".join("{}: {}".format(k, v) for k, v in summary.items())
    res['num_variants'] = len(label_dispositions)
    res['threshold_include_vars'] = lgr_settings.variant_calculation_limit if not ignore_thresholds else -1
    include_blocked = True
    if res['num_variants'] > lgr_settings.variant_calculation_limit:
        res['csv_available'] = True
        if not ignore_thresholds:
            include_blocked = False

    for (variant_cp, var_disp, var_invalid_parts, action_idx, disp_set, logs) in label_dispositions:
        if not include_blocked and var_disp not in ['valid', 'allocatable']:
            continue

        invalid_codepoints = set([c for c, _ in var_invalid_parts or []])

        def format_cphex(c, want_html=True):
            if want_html and c in invalid_codepoints:
                return u'<span class="text-danger not-in-rep">U+{:04X} (&#{};)</span>'.format(c, c)
            else:
                return u"U+{:04X} (&#{};)".format(c, c)

        variant_u = cp_to_ulabel(variant_cp)
        variant_display_html = mark_safe(u' '.join(map(format_cphex, variant_cp)))
        variant_display = u' '.join(u"U+{:04X}".format(cp, cp_to_ulabel(cp)) for cp in variant_cp)
        variant_input = u' '.join(u"U+{:04X}".format(cp) for cp in variant_cp)
        try:
            conversion_error = False
            variant_a = idna_encoder(variant_u)
        except UnicodeError as e:
            variant_a = lgr_exception_to_text(e)
            conversion_error = True
            var_disp = 'invalid'

        var_results.append({
            'u_label': variant_u,
            'a_label': variant_a,
            'conversion_error': conversion_error,
            'cp_display_html': variant_display_html,
            'cp_display': variant_display,
            'cp_input': variant_input,
            'disposition': var_disp,
            'label_invalid_parts': var_invalid_parts,
            'action_idx': action_idx,
            'action': lgr_actions[action_idx] if action_idx >= 0 else None,
            'disp_set': list(disp_set),
            'logs': logs,
        })
    res['variants'] = var_results

    return res


def _get_collisions(lgr, label_cplist, labels_list, idna_encoder, lgr_actions, is_set, is_collision_index=False):
    """

    :param lgr: The LGR
    :param label_cplist: The code points of the label to test against the label list
    :param labels_list: The list of labels to use for collision checking if is_cache is False else the already
                        generated index for the labels in the set
    :param is_set: Whether the LGR is
    :param is_collision_index: Whether check_collisions contains an index
    :return:
    """
    res = {'collisions_checked': True}
    label_u = cp_to_ulabel(label_cplist)
    label_for_compute = []
    cached = None
    if is_collision_index:
        labels = labels_list.keys()
        cached = labels_list
    else:
        labels = [l.strip() for l in labels_list]
        label_for_compute = labels

    debug_name = _("the LGR set labels") if is_set else _("the TLDs list")

    # if label is in the LGR set labels skip
    if label_u in labels:
        res['collisions_error'] = _('The label is in %(labels_list)s') % {'labels_list': debug_name}
        return res

    # check for collisions
    indexes = get_collisions(lgr, label_for_compute + [label_u], quiet=False, cached_indexes=cached)

    if len(indexes) == 0:
        return res

    index = lgr.generate_index_label(label_cplist)
    try:
        collisions = indexes[index]
    except KeyError:
        # label does not collide with the list of labels
        return res
    collision = None
    collide_with = []
    # retrieve label in collision list
    for col in collisions:
        if col['label'] == label_u:
            collision = col
            continue
        if col['label'] in labels:
            collide_with.append(col)

    if not collision:
        # this should not happen
        res['collisions_error'] = _('ERROR cannot retrieve label in collisions, please check %(labels_list)s') % {
            'labels_list': debug_name}
        return res

    for col in collide_with:
        variant_u = idna_encoder(col['label'])
        variant_display_html = mark_safe(
            u' '.join(u"U+{:04X} ({})".format(cp, cp_to_ulabel(cp)) for cp in col['cp']))
        variant_display = u' '.join(u"U+{:04X}".format(cp) for cp in col['cp'])
        try:
            variant_a = idna_encoder(variant_u)
        except UnicodeError as e:
            variant_a = '!ERROR - {}!'.format(e)

        # XXX Collided variants info may be retrieved in script LGR rather than in merged LGR
        action_idx = collision['action_idx'][col['label']]
        collision_dct = {
            'input': col['label'],
            'u_label': variant_u,
            'a_label': variant_a,
            'cp_display_html': variant_display_html,
            'cp_display': variant_display,
            'disposition': collision['disp'][col['label']],
            'action_idx': action_idx,
            'action': lgr_actions[action_idx] if action_idx >= 0 else None,
            'rules': collision['rules'][col['label']]
        }
        res.setdefault('collision', []).append(collision_dct)

    return res


def _get_validity_check_limits(lgr, label_cplist, hide_mixed_script_variants, ignore_thresholds, idna_encoder):
    # reload LGR settings
    # FIXME: find a way to do this automatically, this is necessary in case of multiple instances running
    lgr_settings = get_lgr_settings()
    lgr_settings.refresh_from_db()

    res, lgr_actions = _get_validity(lgr, label_cplist, idna_encoder)
    stop_computation = not ignore_thresholds
    if res['eligible'] and not ignore_thresholds:
        est_var_nbr = lgr.estimate_variant_number(label_cplist, hide_mixed_script_variants=hide_mixed_script_variants)
        res['nbr_variants'] = est_var_nbr
        res['launch_abort'] = False
        if est_var_nbr > lgr_settings.variant_calculation_abort:
            stop_computation = True
            res['launch_abort'] = True
        else:
            need_async = est_var_nbr > lgr_settings.variant_calculation_max
            stop_computation = need_async
            res['launched_as_task'] = need_async

    res['display_label_info'] = not res['eligible'] or not stop_computation
    return res, lgr_actions, stop_computation


def evaluate_label(lgr, label_cplist, ignore_thresholds=False, idna_encoder=lambda x: x.encode('idna'),
                   check_collisions=None, is_collision_index=False, hide_mixed_script_variants=False):
    """
    Evaluate the given `label_cplist` against the given `lgr`, which includes:
    * checking eligibility of the input label
    * determining the disposition of the input label
    * if eligible, variant labels (if any) are also generated and evaluated to determine
      their dispositions.

    :param lgr: The LGR object
    :param label_cplist: The label to test, as an array of codepoints.
    :param ignore_thresholds: Whether thresholds should be ignored
    :param idna_encoder: a function used to encode a string using IDNA
    :param check_collisions: Check for collision against the provided list of labels
    :param is_collision_index: Whether check_collisions contains an index
    :param hide_mixed_script_variants: Whether we hide mixed scripts variants
    :return: a dict containing results of the evaluation.
    """
    res, lgr_actions, stop_computation = _get_validity_check_limits(lgr, label_cplist, hide_mixed_script_variants,
                                                                    ignore_thresholds, idna_encoder)
    if stop_computation:
        return res

    res.update(_get_variants(lgr, label_cplist,
                             ignore_thresholds,
                             idna_encoder,
                             lgr_actions,
                             hide_mixed_script_variants=hide_mixed_script_variants))
    if check_collisions is not None:
        res.update(_get_collisions(lgr, label_cplist, check_collisions, idna_encoder, lgr_actions, False,
                                   is_collision_index=is_collision_index))

    return res


def lgr_set_evaluate_label(lgr, script_lgr, label_cplist, set_labels,
                           ignore_thresholds=False,
                           idna_encoder=lambda x: x.encode('idna'),
                           hide_mixed_script_variants=False):
    """
    Evaluate the given `label_cplist` against the given `lgr`, which includes:
    * checking eligibility of the input label
    * determining the disposition of the input label
    * if eligible, variant labels (if any) are also generated and evaluated to determine
      their dispositions.

    :param lgr: The LGR
    :param script_lgr: The LGR for the script used to check label validity
    :param label_cplist: The label to test, as an array of codepoints.
    :param set_labels: The labels in the lgr set
    :param ignore_thresholds: Whether thresholds should be ignored
    :param idna_encoder: a function used to encode a string using IDNA
    :param hide_mixed_script_variants: Whether we hide mixed scripts variants
    :return: a dict containing results of the evaluation.
    """
    # First, verify that a proposed label is valid by processing it with the Element LGR corresponding to the script
    # that was selected for the label in the application.
    res, script_lgr_actions, stop_computation = _get_validity_check_limits(script_lgr, label_cplist, idna_encoder)
    res['script'] = script_lgr.name
    lgr_actions = lgr.effective_actions_xml

    if stop_computation:
        return res

    # Second, process the now validated label against the common LGR to verify it does not collide with any existing
    # delegated labels (and any of their variants, whether blocked or allocatable).
    # TODO may need lgr_script and script_lgr_actions for variants and rules
    res.update(_get_collisions(lgr, label_cplist, set_labels, idna_encoder, lgr_actions, True))

    # Third, now that the label is known to be valid, and not in collision, use the appropriate element LGR to
    # generate all allocatable variants.
    if 'collision' not in res and 'collisions_error' not in res:
        # XXX if collide => eligible = False remove collision condition
        res.update(_get_variants(script_lgr, label_cplist, ignore_thresholds, idna_encoder, lgr_actions,
                                 hide_mixed_script_variants=hide_mixed_script_variants))

    return res


def validation_results_to_csv(ctx, fileobj, with_header=True):
    """
    Convert validation results to a CSV.
    """
    if with_header:
        # write BOM at the beginning to allow Excel decoding UTF-8
        # fileobj.write(codecs.BOM_UTF8.decode('utf-8'))
        fileobj.write(codecs.BOM_UTF8.decode('utf-8'))

    writer = csv.writer(fileobj)
    if with_header:
        writer.writerow([
            'Type', 'U-label', 'A-label', 'Disposition', 'Code point sequence',
            'Invalid code points', 'Action index', 'Action XML'])

    invalid_formatted = []
    for cp, rules in ctx['label_invalid_parts']:
        reason = "not in repertoire" if rules is None else "does not comply with rules '{}'".format('|'.join(rules))
        invalid_formatted.append("{cp} {reason}".format(cp="U+{:04X}".format(cp), reason=reason))
    invalid_formatted = '-'.join(invalid_formatted) or '-'

    writer.writerow([
        'original', ctx['u_label'], ctx['a_label'], ctx['disposition'], ctx['cp_display'],
        invalid_formatted, ctx['action_idx'], ctx['action']])
    col = ctx.get('collision', None)
    if col:
        writer.writerow([
            'collision', col['u_label'], col['a_label'], col['disposition'], col['cp_display'],
            col['action_idx'], col['action']])
    for var in ctx.get('variants', []):
        invalid_formatted = []
        for cp, rules in var['label_invalid_parts'] or []:
            reason = "not in repertoire" if rules is None else "does not comply with rules '{}'".format('|'.join(rules))
            invalid_formatted.append("{cp} {reason}".format(cp="U+{:04X}".format(cp), reason=reason))
        invalid_formatted = '-'.join(invalid_formatted) or '-'
        writer.writerow([
            'varlabel', var['u_label'], var['a_label'], var['disposition'], var['cp_display'],
            invalid_formatted, var['action_idx'], var['action']])
    # add empty row
    writer.writerow([])
