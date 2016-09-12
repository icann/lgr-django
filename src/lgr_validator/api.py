# -*- coding: utf-8 -*-
from django.utils.safestring import mark_safe


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
    label_u = u''.join([unichr(c) for c in label_cplist])
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
    res = {
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
    }
    if eligible:
        var_results = []
        summary, label_dispositions = lgr.compute_label_disposition_summary(label_cplist, include_invalid=True)
        res['summary'] = summary
        res['num_variants'] = len(label_dispositions)
        res['threshold_include_vars'] = threshold_include_vars
        if threshold_include_vars < 0 or len(label_dispositions) <= threshold_include_vars:
            for (variant_cp, var_disp, action_idx, disp_set, logs) in label_dispositions:
                variant_u = ''.join([unichr(c) for c in variant_cp])
                variant_display = u' '.join(u"U+{:04X} ({})".format(cp, unichr(cp)) for cp in variant_cp)
                variant_input = u' '.join(u"U+{:04X}".format(cp) for cp in variant_cp)
                variant_a = idna_encoder(variant_u)

                var_results.append({
                    'u_label': variant_u,
                    'a_label': variant_a,
                    'cp_display_html': variant_display,  # html version is identical to text, but just for consistency
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
