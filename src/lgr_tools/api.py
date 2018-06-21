# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import time

from django.utils.text import slugify

from lgr_editor.exceptions import LGRValidationException
from lgr.tools.compare import union_lgrs, intersect_lgrs, diff_lgrs, diff_lgr_sets
from lgr.tools.annotate import annotate, lgr_set_annotate
from lgr.tools.diff_collisions import diff, collision
from lgr.tools.cross_script_variants import cross_script_variants
from lgr.tools.harmonize import harmonize

from lgr_editor.api import LGRInfo, session_open_lgr, session_save_lgr
from lgr_validator.api import lgr_set_evaluate_label, evaluate_label, validation_results_to_csv


class LGRCompInvalidException(LGRValidationException):
    """
    Raised when the XML validation against schema fails and contains the
    invalid XML.
    """
    def __init__(self, content, error):
        self.content = content
        self.error = error


def lgr_intersect_union(request, lgr_info_1, lgr_info_2, action):
    """
    Compare 2 LGRs for union/intersection.

    :param request: The request object.
    :param lgr_info_1: The first LGR info object.
    :param lgr_info_2: The second LGR info object.
    :param action: One of "UNION", "INTERSECTION".
    :return: LGR id of generated LGR. If there is a validation error,
             LGRCompInvalidException is raised and contains the resulting XML
    """
    result_lgr = None
    if action == 'INTERSECTION':
        result_lgr = intersect_lgrs(lgr_info_1.lgr, lgr_info_2.lgr)
    elif action == 'UNION':
        result_lgr = union_lgrs(lgr_info_1.lgr, lgr_info_2.lgr)

    # Generate new slug (LGR id)
    lgr_id = slugify(result_lgr.name)

    lgr_info = LGRInfo(name=lgr_id,
                       lgr=result_lgr)
    lgr_info.update_xml(pretty_print=True)
    try:
        session_open_lgr(request, lgr_id, lgr_info.xml,
                         validating_repertoire_name=None,
                         validate=True)
    except LGRValidationException as e:
        raise LGRCompInvalidException(lgr_info.xml, e.args[0])

    return lgr_id


def lgr_comp_diff(request, lgr_info_1, lgr_info_2, full_dump=True):
    """
    Compare 2 LGRs with textual output.

    :param request: The request object.
    :param lgr_info_1: The first LGR info object.
    :param lgr_info_2: The second LGR info object.
    :param full_dump: Whether identical char should return something or not.
    :return: Text log to be displayed.
    """
    # if lgr_info_1 is a set then lgr_info_2 also and reciprocally
    if not lgr_info_1.is_set:
        content = diff_lgrs(lgr_info_1.lgr, lgr_info_2.lgr,
                            show_same=full_dump)
    else:
        content = diff_lgr_sets(lgr_info_1.lgr, lgr_info_2.lgr,
                                [lgr.lgr for lgr in lgr_info_1.lgr_set],
                                [lgr.lgr for lgr in lgr_info_2.lgr_set],
                                show_same=full_dump)

    return content


def lgr_diff_labels(lgr_1, lgr_2, labels_file,
                    show_collision,
                    full_dump,
                    with_rules):
    """
    Show difference between two LGR for a list of labels

    :param lgr_1: The first LGR.
    :param lgr_2: The second LGR.
    :param labels_file: The file containing the list of labels
    :param show_collision: Whether we output collisions as well
    :param full_dump: Whether we output a full dump
    :param with_rules: Whether we also output rules
    :return: Text log to be displayed
    """
    return diff(lgr_1, lgr_2, labels_file,
                show_collision, full_dump, not with_rules)


def lgr_collision_labels(lgr, labels_file, full_dump, with_rules):
    """
    Show difference between two LGR for a list of labels

    :param lgr: The LGR object.
    :param labels_file: The file containing the list of labels
    :param full_dump: Whether we output a full dump
    :param with_rules: Whether we also output rules
    :return: Text log to be displayed
    """
    return collision(lgr, labels_file, full_dump, not with_rules)


def lgr_annotate_labels(lgr, labels_file):
    """
    Compute disposition of a list of labels in a LGR.

    :param lgr: The LGR object.
    :param labels_file: The file containing the list of labels
    :return: Text log to be displayed
    """
    return annotate(lgr, labels_file)


def lgr_set_annotate_labels(lgr, script_lgr, set_labels, labels_file):
    """
    Compute disposition of a list of labels in a LGR.

    :param lgr: The LGR object.
    :param script_lgr: The LGR fo the script used to check label validity
    :param set_labels: The label of the LGR set
    :param labels_file: The file containing the list of labels
    :return: Text log to be displayed
    """
    return lgr_set_annotate(lgr, script_lgr, set_labels, labels_file)


def lgr_cross_script_variants(lgr, labels_file):
    """
    Compute cross-script variants of a list of labels in a LGR.

    :param lgr: The LGR to use for variant generation.
    :param labels_file: The file containing the list of labels
    :return: Text log to be displayed
    """
    return cross_script_variants(lgr, labels_file)


def lgr_harmonization(request, lgr_1, lgr_2, rz_lgr, script):
    """
    Perform variant harmonization between 2 LGRs

    :param request: The request object.
    :param lgr_1: First LGR.
    :param lgr_2: Second LGR.
    :param rz_lgr: Optional related Rootzone LGR.
    :param script: Optional script to consider in `rz_lgr`.
    """
    h_lgr_1, h_lgr_2, cp_review = harmonize(lgr_1, lgr_2, rz_lgr, script)

    def _save_resulting_lgr(l):
        # Generate new slug (LGR id)
        lgr_id = slugify("{}_harmonized_{}".format(l.name, time.strftime('%Y%m%d_%H%M%S')))

        lgr_info = LGRInfo(name=lgr_id,
                           lgr=l)
        lgr_info.update_xml(pretty_print=True)
        session_save_lgr(request, lgr_info)
        return lgr_id

    (h_lgr_1_id, h_lgr_2_id) = (_save_resulting_lgr(l) for l in (h_lgr_1, h_lgr_2))
    return h_lgr_1_id, h_lgr_2_id, cp_review


def _validate_label_task_helper(value):
    """
    Helper method for validate label tasks.

    Convert results to CSV format.

    :param value: Result of label validation.
    :return: A CSV as a string.
    """
    # Define some py2/3 compat stuff
    import sys
    if sys.version_info.major > 2:
        from io import StringIO
        outIO = StringIO
        out_fn = lambda x: x
    else:
        from io import BytesIO
        outIO = BytesIO
        out_fn = lambda x: x.decode('utf-8')

    out = outIO()
    validation_results_to_csv(value, out)
    return out_fn(out.getvalue())


def lgr_validate_label(lgr, label, udata):
    """
    Validate a label for an LGR.

    :param lgr: The LGR to use for variant generation.
    :param label: Label to validate.
    :param udata: The associated Unicode database.
    :return: CSV containing the label validation output.
    """
    return _validate_label_task_helper(evaluate_label(lgr, label,
                                                      -1, udata.idna_encode_label))


def lgr_set_validate_label(lgr, script_lgr, set_labels, label, udata):
    """
        Validate a label for an LGR set.

        :param lgr: The LGR to use for variant generation.
        :param label: Label to validate.
        :param script_lgr: The LGR fo the script used to check label validity
        :param set_labels: The label of the LGR set
        :param udata: The associated Unicode database.
        :return: CSV containing the label validation output.
        """
    return _validate_label_task_helper(lgr_set_evaluate_label(lgr, script_lgr, label, set_labels,
                                                              -1, udata.idna_encode_label))
