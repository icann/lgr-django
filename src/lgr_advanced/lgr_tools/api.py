# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging
import time
from io import StringIO

from lgr.core import LGR
from lgr.parser.xml_serializer import serialize_lgr_xml
from lgr.tools.annotate import annotate, lgr_set_annotate
from lgr.tools.compare import union_lgrs, intersect_lgrs, diff_lgrs, diff_lgr_sets
from lgr.tools.diff_collisions import diff, collision, basic_collision
from lgr.tools.harmonize import harmonize
from lgr.tools.utils import read_labels
from lgr_advanced.lgr_validator.api import lgr_set_evaluate_label, evaluate_label, validation_results_to_csv
from lgr_advanced.models import LgrModel
from lgr_auth.models import LgrUser
from lgr_models.exceptions import LGRValidationException
from lgr_models.models.lgr import RzLgr

logger = logging.getLogger(__name__)


class LGRCompInvalidException(LGRValidationException):
    """
    Raised when the XML validation against schema fails and contains the
    invalid XML.
    """

    def __init__(self, content, error):
        self.content = content
        self.error = error


def lgr_intersect_union(user: LgrUser, lgr_object_1: LgrModel, lgr_object_2: LgrModel, action):
    """
    Compare 2 LGRs for union/intersection.

    :param user: The logged in user.
    :param lgr_object_1: The first LGR object.
    :param lgr_object_2: The second info object.
    :param action: One of "UNION", "INTERSECTION".
    :return: LGR id of generated LGR. If there is a validation error,
             LGRCompInvalidException is raised and contains the resulting XML
    """
    result_lgr = None
    if action == 'INTERSECTION':
        result_lgr = intersect_lgrs(lgr_object_1.to_lgr(), lgr_object_2.to_lgr())
    elif action == 'UNION':
        result_lgr = union_lgrs(lgr_object_1.to_lgr(), lgr_object_2.to_lgr())

    try:
        result_lgr_object = LgrModel.from_lgr(user, result_lgr, validate=True)
    except LGRValidationException as e:
        xml = serialize_lgr_xml(result_lgr, pretty_print=True)
        raise LGRCompInvalidException(xml, e.args[0])

    return result_lgr_object


def lgr_comp_diff(lgr_object_1: LgrModel, lgr_object_2: LgrModel, full_dump=True):
    """
    Compare 2 LGRs with textual output.

    :param lgr_object_1: The first LGR object.
    :param lgr_object_2: The second info object.
    :param full_dump: Whether identical char should return something or not.
    :return: Text log to be displayed.
    """
    # if lgr_info_1 is a set then lgr_info_2 also and reciprocally
    if not lgr_object_1.is_set():
        content = diff_lgrs(lgr_object_1.to_lgr(), lgr_object_2.to_lgr(),
                            show_same=full_dump)
    else:
        content = diff_lgr_sets(lgr_object_1.to_lgr(), lgr_object_2.to_lgr(),
                                [lgr_obj.to_lgr() for lgr_obj in lgr_object_1.embedded_lgrs()],
                                [lgr_obj.to_lgr() for lgr_obj in lgr_object_2.embedded_lgrs()],
                                show_same=full_dump)

    return content


def lgr_diff_labels(lgr_1: LGR, lgr_2: LGR, labels_file,
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


def lgr_collision_labels(lgr: LGR, labels_file, tlds_file, full_dump):
    """
    Show difference between two LGR for a list of labels

    :param lgr: The LGR.
    :param labels_file: The file containing the list of labels
    :param tlds_file: The file containing the TLDs
    :param full_dump: Whether we output a full dump
    :return: Text log to be displayed
    """
    return collision(lgr, labels_file, tlds_file, full_dump)


def lgr_basic_collision_labels(lgr: LGR, labels_file, tlds_file, with_annotate):
    """
    Show difference between two LGR for a list of labels

    :param lgr: The LGR.
    :param labels_file: The file containing the list of labels
    :param tlds_file: The file containing the TLDs
    :param with_annotate: Whether we annotate labels
    :return: Text log to be displayed
    """
    return basic_collision(lgr, labels_file, tlds_file, with_annotate)


def lgr_annotate_labels(lgr: LGR, labels_file):
    """
    Compute disposition of a list of labels in a LGR.

    :param lgr: The LGR.
    :param labels_file: The file containing the list of labels
    :return: Text log to be displayed
    """
    return annotate(lgr, labels_file)


def lgr_set_annotate_labels(lgr: LGR, script_lgr, set_labels, labels_file):
    """
    Compute disposition of a list of labels in a LGR.

    :param lgr: The LGR.
    :param script_lgr: The LGR fo the script used to check label validity
    :param set_labels: The label of the LGR set
    :param labels_file: The file containing the list of labels
    :return: Text log to be displayed
    """
    return lgr_set_annotate(lgr, script_lgr, set_labels, labels_file)


def lgr_harmonization(user: LgrUser, lgr_object_1: LgrModel, lgr_object_2: LgrModel, rz_lgr_object: RzLgr):
    """
    Perform variant harmonization between 2 LGRs

    :param user: The logged in user.
    :param lgr_object_1: First LGR object.
    :param lgr_object_2: Second LGR object.
    :param rz_lgr_object: Optional related Rootzone LGR object.
    """
    h_lgr_1, h_lgr_2, cp_review = harmonize(lgr_object_1.to_lgr(), lgr_object_2.to_lgr(),
                                            rz_lgr_object.to_lgr() if rz_lgr_object else None)

    def _save_resulting_lgr(l):
        # Generate new slug (LGR id)
        lgr_name = "{}_harmonized_{}".format(l.name, time.strftime('%Y%m%d_%H%M%S'))

        lgr_object = LgrModel.from_lgr(user, l, name=lgr_name)
        return lgr_object

    (h_lgr_1_object, h_lgr_2_object) = (_save_resulting_lgr(l) for l in (h_lgr_1, h_lgr_2))
    return h_lgr_1_object, h_lgr_2_object, cp_review


def _validate_label_task_helper(value, with_header=True):
    """
    Helper method for validate label tasks.

    Convert results to CSV format.

    :param value:       Result of label validation.
    :param with_header: Whether CSV the output is returned with header or not
    :return: A CSV as a string.
    """
    out = StringIO()
    validation_results_to_csv(value, out, with_header=with_header)
    return out.getvalue()


def lgr_validate_label(lgr: LGR, label, udata, hide_mixed_script_variants=False):
    """
    Validate a label for an LGR.

    :param lgr: The LGR to use for variant generation.
    :param label: Label to validate.
    :param udata: The associated Unicode database.
    :param hide_mixed_script_variants: Whether we hide mixed scripts variants.
    :return: CSV containing the label validation output.
    """
    return _validate_label_task_helper(evaluate_label(lgr, label,
                                                      ignore_thresholds=True,
                                                      idna_encoder=udata.idna_encode_label,
                                                      hide_mixed_script_variants=hide_mixed_script_variants))


def lgr_set_validate_label(lgr: LGR, script_lgr: LGR, set_labels, label, udata, hide_mixed_script_variants=False):
    """
    Validate a label for an LGR set.

    :param lgr: The LGR to use for variant generation.
    :param label: Label to validate.
    :param script_lgr: The LGR fo the script used to check label validity
    :param set_labels: The label of the LGR set
    :param udata: The associated Unicode database.
    :param hide_mixed_script_variants: Whether we hide mixed scripts variants.
    :return: CSV containing the label validation output.
    """
    return _validate_label_task_helper(lgr_set_evaluate_label(lgr, script_lgr, label, set_labels,
                                                              ignore_thresholds=True,
                                                              idna_encoder=udata.idna_encode_label,
                                                              hide_mixed_script_variants=hide_mixed_script_variants))


def lgr_validate_labels(lgr: LGR, labels_file, udata, hide_mixed_script_variants=False):
    """
    Validate labels for an LGR.

    :param lgr: The LGR to use for variant generation.
    :param labels_file: The file containing the list of labels
    :param udata: The associated Unicode database.
    :param hide_mixed_script_variants: Whether we hide mixed scripts variants.
    :return: CSV containing the labels validation output.
    """
    it = 0
    for __, label, __, __ in read_labels(labels_file, lgr.unicode_database):
        label_cp = tuple([ord(c) for c in label])
        try:
            yield _validate_label_task_helper(
                evaluate_label(lgr, label_cp,
                               ignore_thresholds=True,
                               idna_encoder=udata.idna_encode_label,
                               hide_mixed_script_variants=hide_mixed_script_variants),
                with_header=not it)
            it += 1
        except Exception as ex:
            logger.error("Failed to process label %s: %s", label, ex)
            yield "\nError processing label {}\n".format(label)
