# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import time

from django.utils.text import slugify

from lgr.tools.annotate import annotate, lgr_set_annotate
from lgr.tools.compare import union_lgrs, intersect_lgrs, diff_lgrs, diff_lgr_sets
from lgr.tools.cross_script_variants import cross_script_variants
from lgr.tools.diff_collisions import diff, collision, basic_collision
from lgr.tools.harmonize import harmonize
from lgr.tools.utils import read_labels
from lgr_advanced.api import LGRInfo
from lgr_advanced.exceptions import LGRValidationException
from lgr_advanced.lgr_validator.api import lgr_set_evaluate_label, evaluate_label, validation_results_to_csv

logger = logging.getLogger(__name__)


class LGRCompInvalidException(LGRValidationException):
    """
    Raised when the XML validation against schema fails and contains the
    invalid XML.
    """

    def __init__(self, content, error):
        self.content = content
        self.error = error


def lgr_intersect_union(session, lgr_info_1, lgr_info_2, action):
    """
    Compare 2 LGRs for union/intersection.

    :param session: The LGRSession object.
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
        session.open_lgr(lgr_id, lgr_info.xml,
                         validating_repertoire=None,
                         validate=True)
    except LGRValidationException as e:
        raise LGRCompInvalidException(lgr_info.xml, e.args[0])

    return lgr_id


def lgr_comp_diff(lgr_info_1, lgr_info_2, full_dump=True):
    """
    Compare 2 LGRs with textual output.

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


def lgr_collision_labels(lgr, labels_file, tlds_file, full_dump, with_rules):
    """
    Show difference between two LGR for a list of labels

    :param lgr: The LGR object.
    :param labels_file: The file containing the list of labels
    :param tlds_file: The file containing the TLDs
    :param full_dump: Whether we output a full dump
    :param with_rules: Whether we also output rules
    :return: Text log to be displayed
    """
    return collision(lgr, labels_file, tlds_file, full_dump, not with_rules)


def lgr_basic_collision_labels(lgr, labels_file, tlds_file, with_annotate):
    """
    Show difference between two LGR for a list of labels

    :param lgr: The LGR object.
    :param labels_file: The file containing the list of labels
    :param tlds_file: The file containing the TLDs
    :param with_annotate: Whether we annotate labels
    :return: Text log to be displayed
    """
    return basic_collision(lgr, labels_file, tlds_file, with_annotate)


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


def lgr_harmonization(session, lgr_1, lgr_2, rz_lgr):
    """
    Perform variant harmonization between 2 LGRs

    :param session: The LGRSession object.
    :param lgr_1: First LGR.
    :param lgr_2: Second LGR.
    :param rz_lgr: Optional related Rootzone LGR.
    """
    h_lgr_1, h_lgr_2, cp_review = harmonize(lgr_1, lgr_2, rz_lgr)

    def _save_resulting_lgr(l):
        # Generate new slug (LGR id)
        lgr_id = slugify("{}_harmonized_{}".format(l.name, time.strftime('%Y%m%d_%H%M%S')))

        lgr_info = LGRInfo(name=lgr_id,
                           lgr=l)
        lgr_info.update_xml(pretty_print=True)
        session.save_lgr(lgr_info)
        return lgr_id

    (h_lgr_1_id, h_lgr_2_id) = (_save_resulting_lgr(l) for l in (h_lgr_1, h_lgr_2))
    return h_lgr_1_id, h_lgr_2_id, cp_review


def _validate_label_task_helper(value, with_header=True):
    """
    Helper method for validate label tasks.

    Convert results to CSV format.

    :param value:       Result of label validation.
    :param with_header: Whether CSV the output is returned with header or not
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
    validation_results_to_csv(value, out, with_header=with_header)
    return out_fn(out.getvalue())


def lgr_validate_label(lgr, label, udata):
    """
    Validate a label for an LGR.

    :param lgr: The LGR to use for variant generation.
    :param label: Label to validate.
    :param udata: The associated Unicode database.
    :return: CSV containing the label validation output.
    """
    return _validate_label_task_helper(evaluate_label(lgr, label, -1, udata.idna_encode_label))


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


def lgr_validate_labels(lgr, labels_file, udata):
    """
    Validate labels for an LGR.

    :param lgr: The LGR to use for variant generation.
    :param labels_file: The file containing the list of labels
    :param udata: The associated Unicode database.
    :return: CSV containing the labels validation output.
    """
    it = 0
    for label, _, _ in read_labels(labels_file, lgr.unicode_database):
        label_cp = tuple([ord(c) for c in label])
        try:
            yield _validate_label_task_helper(evaluate_label(lgr, label_cp, -1, udata.idna_encode_label),
                                              with_header=not it)
            it += 1
        except Exception as ex:
            logger.error("Failed to process label %s: %s", label, ex)
            yield "\nError processing label {}\n".format(label)
