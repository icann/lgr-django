# -*- coding: utf-8 -*-
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from lgr.tools.diff_collisions import get_collisions
from lgr import wide_unichr


def _get_validity(lgr, label_cplist, idna_encoder):
    label_u = u''.join([wide_unichr(c) for c in label_cplist])
    try:
        label_a = idna_encoder(label_u)
    except UnicodeError as e:
        label_a = '!ERROR - {}!'.format(e)

    (eligible, label_valid_part, label_invalid_part, disp, action_idx, logs) = lgr.test_label_eligible(label_cplist)

    invalid_codepoints = set(label_invalid_part)

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
        'cp_display_html': label_display_html,
        'cp_display': label_display_text,
        'eligible': eligible,
        'invalid_codepoint': label_invalid_part,
        'disposition': disp,
        'action_idx': action_idx,
        'action': lgr_actions[action_idx] if action_idx >= 0 else None,
        'logs': logs
    }, lgr_actions


def _get_variants(lgr, label_cplist, threshold_include_vars, idna_encoder, lgr_actions):
    res = {}
    var_results = []
    summary, label_dispositions = lgr.compute_label_disposition_summary(label_cplist, include_invalid=True)
    res['summary'] = summary
    res['num_variants'] = len(label_dispositions)
    res['threshold_include_vars'] = threshold_include_vars
    if threshold_include_vars < 0 or len(label_dispositions) <= threshold_include_vars:
        for (variant_cp, var_disp, action_idx, disp_set, logs) in label_dispositions:
            variant_u = ''.join([wide_unichr(c) for c in variant_cp])
            variant_display_html = mark_safe(u' '.join(u"U+{:04X} ({})".format(cp, wide_unichr(cp)) for cp in variant_cp))
            variant_display = u' '.join(u"U+{:04X}".format(cp, wide_unichr(cp)) for cp in variant_cp)
            variant_input = u' '.join(u"U+{:04X}".format(cp) for cp in variant_cp)
            variant_a = idna_encoder(variant_u)

            var_results.append({
                'u_label': variant_u,
                'a_label': variant_a,
                'cp_display_html': variant_display_html,
                'cp_display': variant_display,
                'cp_input': variant_input,
                'disposition': var_disp,
                'action_idx': action_idx,
                'action': lgr_actions[action_idx] if action_idx >= 0 else None,
                'disp_set': disp_set,
                'logs': logs,
            })
        res['variants'] = var_results

    return res


def _get_collisions(lgr, label_cplist, set_labels, idna_encoder, lgr_actions):
    res = {}
    label_u = u''.join([wide_unichr(c) for c in label_cplist])
    set_labels = [l.strip() for l in set_labels]

    # if label is in the LGR set labels skip
    if label_u in set_labels:
        res['collisions_error'] = _('The label is in the LGR set labels.')
        return res

    # check for collisions
    indexes = get_collisions(lgr, set_labels + [label_u], quiet=False)
    if len(indexes) > 1:
        # there should be one collision as set labels are checked, this error should not happen
        res['collisions_error'] = _('ERROR more than one collision, please check your LGR set labels')
        return res

    if len(indexes) == 0:
        return res

    collisions = indexes[list(indexes.keys())[0]]
    collision = None
    collide_with = []
    # retrieve label in collision list
    for col in collisions:
        if col['label'] == label_u:
            collision = col
        if col['label'] in set_labels:
            collide_with.append(col)

    if not collision:
        # this should not happen
        res['collisions_error'] = _('ERROR cannot retrieve label in collisions, please check your LGR set labels')
        return res

    if len(collide_with) != 1:
        res['collisions_error'] = _('ERROR collision with more than one label in the LGR set labels,'
                                    'please check your LGR set labels')
        return res

    collide_with = collide_with[0]
    variant_u = idna_encoder(collide_with['label'])
    variant_display_html = mark_safe(u' '.join(u"U+{:04X} ({})".format(cp, wide_unichr(cp)) for cp in collide_with['cp']))
    variant_display = u' '.join(u"U+{:04X}".format(cp, wide_unichr(cp)) for cp in collide_with['cp'])
    try:
        variant_a = idna_encoder(variant_u)
    except UnicodeError as e:
        variant_a = '!ERROR - {}!'.format(e)

    # XXX Collided variants info may be retrieved in script LGR rather than in merged LGR
    action_idx = collision['action_idx'][collide_with['label']]
    collision_dct = {
        'input': collide_with['label'],
        'u_label': variant_u,
        'a_label': variant_a,
        'cp_display_html': variant_display_html,
        'cp_display': variant_display,
        'disposition': collision['disp'][collide_with['label']],
        'action_idx': action_idx,
        'action': lgr_actions[action_idx] if action_idx >= 0 else None,
        'rules': collision['rules'][collide_with['label']]
    }
    # remove variants that are not in our labels set
    res['collision'] = collision_dct

    return res


def evaluate_label(lgr, label_cplist, threshold_include_vars=-1, idna_encoder=lambda x: x.encode('idna')):
    """
    Evaluate the given `label_cplist` against the given `lgr`, which includes:
    * checking eligibility of the input label
    * determining the disposition of the input label
    * if eligible, variant labels (if any) are also generated and evaluated to determine
      their dispositions.

    :param lgr: The LGR object
    :param label_cplist: The label to test, as an array of codepoints.
    :param threshold_include_vars: Include variants in results if the number of variant labels is less or equal to this.
                                   Set to negative to always return variants.
    :param idna_encoder: a function used to encode a string using IDNA
    :return: a dict containing results of the evaluation.
    """
    res, lgr_actions = _get_validity(lgr, label_cplist, idna_encoder)

    if res['eligible']:
        res.update(_get_variants(lgr, label_cplist, threshold_include_vars, idna_encoder, lgr_actions))

    return res


def lgr_set_evaluate_label(lgr, script_lgr, label_cplist, set_labels,
                           threshold_include_vars=-1,
                           idna_encoder=lambda x: x.encode('idna')):
    """
    Evaluate the given `label_cplist` against the given `lgr`, which includes:
    * checking eligibility of the input label
    * determining the disposition of the input label
    * if eligible, variant labels (if any) are also generated and evaluated to determine
      their dispositions.

    :param lgr: The LGR object
    :param script_lgr: The LGR object for the script used to check label validity
    :param label_cplist: The label to test, as an array of codepoints.
    :param set_labels: The labels in the lgr set
    :param threshold_include_vars: Include variants in results if the number of variant labels is less or equal to this.
                                   Set to negative to always return variants.
    :param idna_encoder: a function used to encode a string using IDNA
    :return: a dict containing results of the evaluation.
    """
    # First, verify that a proposed label is valid by processing it with the Element LGR corresponding to the script
    # that was selected for the label in the application.
    res, script_lgr_actions = _get_validity(script_lgr, label_cplist, idna_encoder)
    res['script'] = script_lgr.name
    lgr_actions = lgr.effective_actions_xml

    # Second, process the now validated label against the common LGR to verify it does not collide with any existing
    # delegated labels (and any of their variants, whether blocked or allocatable).
    if res['eligible']:
        # TODO may need lgr_script and script_lgr_actions for variants and rules
        res.update(_get_collisions(lgr, label_cplist, set_labels, idna_encoder, lgr_actions))

    # Third, now that the label is known to be valid, and not in collision, use the appropriate element LGR to
    # generate all allocatable variants.
    if res['eligible'] and 'collision' not in res and 'collisions_error' not in res:
        # XXX if collide => eligible = False remove collision condition
        res.update(_get_variants(script_lgr, label_cplist, threshold_include_vars, idna_encoder, lgr_actions))

    return res
