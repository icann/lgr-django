# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import time
from gzip import GzipFile
from io import BytesIO

from celery import shared_task
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMessage

from lgr.exceptions import LGRException
from lgr.utils import cp_to_ulabel
from lgr_advanced.lgr_editor.api import LabelInfo, LGRInfo
from lgr_advanced.lgr_editor.lgr_exceptions import lgr_exception_to_text
from lgr_advanced.lgr_editor.unidb import get_db_by_version
from lgr_advanced.lgr_tools.api import (lgr_diff_labels,
                                        lgr_collision_labels,
                                        lgr_annotate_labels,
                                        lgr_set_annotate_labels,
                                        lgr_cross_script_variants,
                                        lgr_validate_label,
                                        lgr_set_validate_label,
                                        lgr_validate_labels,
                                        lgr_basic_collision_labels)

logger = logging.getLogger(__name__)


def _lgr_tool_task(storage_path, base_filename, email_subject,
                   email_body, email_address, cb, **cb_kwargs):
    """
    Launch the tool task and send e-mail


    :param storage_path: The place where results will be stored
    :param base_filename: The filename that will be generated (.txt is added if it has no extension)
    :param email_subject: The subject for the e-mail to be sent
    :param email_body: The body of the e-mail to be sent
    :param email_address: The e-mail address where the results will be sent
    :param cb: The callback to launch the tool
    :param cb_kwargs: The argument for the callback
    """
    sio = BytesIO()
    email = EmailMessage(subject='{}'.format(email_subject),
                         to=[email_address])
    if '.' not in base_filename:
        base_filename += '.txt'

    try:
        with GzipFile(filename=base_filename,
                      fileobj=sio, mode='w') as gzf:
            for line in cb(**cb_kwargs):
                gzf.write(line.encode('utf-8'))

        filename = '{0}_{1}.gz'.format(time.strftime('%Y%m%d_%H%M%S'),
                                       base_filename)

        storage = FileSystemStorage(location=storage_path,
                                    file_permissions_mode=0o440)

        storage.save(filename, sio)
        email.body = "{body} been successfully completed.\n" \
                     "You should now be able to download it from your home " \
                     "screen under the name: '{name}'.\nPlease refresh the " \
                     "home page if you don't see the link.\n" \
                     "Best regards".format(body=email_body,
                                           name=filename)
    except LGRException as ex:
        email.body = '{body} failed with error:\n{err}\n' \
                     'Best regards'.format(body=email_body,
                                           err=lgr_exception_to_text(ex))
        logger.exception('Error in tool computation:')
    except BaseException:
        email.body = '{body} failed with unknown error.\n' \
                     'Best regards'.format(body=email_body)
        logger.exception('Error in tool computation:')
    finally:
        sio.close()
        email.send()


@shared_task
def diff_task(lgr_json_1, lgr_json_2, labels_json, email_address, collision, full_dump,
              with_rules, storage_path):
    """
    Launch difference computation for a list of labels between two LGR

    :param lgr_json_1: The first LGRInfo as a JSON object.
    :param lgr_json_2: The second LGRInfo as a JSON object.
    :param labels_json: The LabelInfo as a JSON object.
    :param email_address: The e-mail address where the results will be sent
    :param collision: Whether we also compute collisions
    :param full_dump: Whether we also output a full dump
    :param with_rules: Whether we also output rules
    :param storage_path: The place where results will be stored
    :return:
    """
    lgr1 = LGRInfo.from_dict(lgr_json_1).lgr
    lgr2 = LGRInfo.from_dict(lgr_json_2).lgr
    labels_info = LabelInfo.from_dict(labels_json)

    logger.info("Starting task 'diff' between %s and %s, for file %s",
                lgr1.name, lgr2.name, labels_info.name)

    body = "Hi,\nThe processing of diff from labels provided in the " \
           "file '{f}' between LGR '{lgr1}' and " \
           "LGR '{lgr2}' has".format(f=labels_info.name,
                                     lgr1=lgr1.name,
                                     lgr2=lgr2.name)

    _lgr_tool_task(storage_path,
                   base_filename='diff_{0}_{1}'.format(lgr1.name,
                                                       lgr2.name),
                   email_subject='LGR Toolset diff result',
                   email_body=body,
                   email_address=email_address,
                   cb=lgr_diff_labels,
                   lgr_1=lgr1, lgr_2=lgr2,
                   labels_file=labels_info.labels,
                   show_collision=collision,
                   full_dump=full_dump,
                   with_rules=with_rules)


@shared_task
def collision_task(lgr_json, labels_json, tld_json, email_address, full_dump,
                   with_rules, storage_path):
    """
    Compute collision between labels in an LGR

    :param lgr_json: The LGRInfo as a JSON object.
    :param labels_json: The LabelInfo as a JSON object containing labels to check for coliision.
    :param tld_json: The LabelInfo as a JSON object containing TLDs.
    :param email_address: The e-mail address where the results will be sent
    :param full_dump: Whether we also output a full dump
    :param with_rules: Whether we also output rules
    :param storage_path: The place where results will be stored
    """
    lgr = LGRInfo.from_dict(lgr_json).lgr
    labels_info = LabelInfo.from_dict(labels_json)
    tlds_info = LabelInfo.from_dict(tld_json) if tld_json else None

    logger.info("Starting task 'collision' for %s, for file %s",
                lgr.name, labels_info.name)

    body = "Hi,\nThe processing of collisions from labels provided in {input} in LGR '{lgr}' has".format(
        input="the file '{}'".format(labels_info.name) if labels_info.name else 'ICANN tlds',
        lgr=lgr.name)
    _lgr_tool_task(storage_path,
                   base_filename='collisions_{0}'.format(lgr.name),
                   email_subject='LGR Toolset collisions result',
                   email_body=body,
                   email_address=email_address,
                   cb=lgr_collision_labels,
                   lgr=lgr,
                   labels_file=labels_info.labels,
                   tlds_file=tlds_info.labels if tld_json else None,
                   full_dump=full_dump,
                   with_rules=with_rules)


@shared_task
def basic_collision_task(lgr_json, labels_json, tld_json, email_address, storage_path, annotate=False):
    """
    Compute collision between labels in an LGR

    :param lgr_json: The LGRInfo as a JSON object.
    :param labels_json: The LabelInfo as a JSON object containing labels to check for coliision.
    :param tld_json: The LabelInfo as a JSON object containing TLDs.
    :param email_address: The e-mail address where the results will be sent
    :param storage_path: The place where results will be stored
    :param annotate: Whether the labels should also be annotated
    """
    lgr = LGRInfo.from_dict(lgr_json).lgr
    labels_info = LabelInfo.from_dict(labels_json)
    tlds_info = LabelInfo.from_dict(tld_json) if tld_json else None
    task_name = "collisions"
    if annotate:
        task_name += " and annotations"

    logger.info("Starting task 'basic %s' for %s, for file %s",
                task_name, lgr.name, labels_info.name)

    body = "Hi,\nThe processing of {name} from labels provided in {input} in LGR '{lgr}' has".format(
        name=task_name,
        input="the file '{}'".format(labels_info.name) if labels_info.name else 'ICANN tlds',
        lgr=lgr.name)
    _lgr_tool_task(storage_path,
                   base_filename='{}_{}'.format(task_name.replace(" ", "_"), lgr.name),
                   email_subject='LGR Toolset {} result'.format(task_name),
                   email_body=body,
                   email_address=email_address,
                   cb=lgr_basic_collision_labels,
                   lgr=lgr,
                   labels_file=labels_info.labels,
                   tlds_file=tlds_info.labels if tld_json else None,
                   with_annotate=annotate)


@shared_task
def annotate_task(lgr_json, labels_json, email_address, storage_path):
    """
    Compute dispositions of labels in a LGR.

    :param lgr_json: The LGRInfo as a JSON object.
    :param labels_json: The LabelInfo as a JSON object.
    :param email_address: The e-mail address where the results will be sent
    :param storage_path: The place where results will be stored
    """
    lgr = LGRInfo.from_dict(lgr_json).lgr
    labels_info = LabelInfo.from_dict(labels_json)

    logger.info("Starting task 'annotate' for %s, for file %s",
                lgr.name, labels_info.name)

    body = "Hi,\nThe processing of annotation from labels provided in the " \
           "file '{f}' in LGR '{lgr}' has".format(f=labels_info.name,
                                                  lgr=lgr.name)

    _lgr_tool_task(storage_path,
                   base_filename='annotation_{0}'.format(lgr.name),
                   email_subject='LGR Toolset annotation result',
                   email_body=body,
                   email_address=email_address,
                   cb=lgr_annotate_labels,
                   lgr=lgr,
                   labels_file=labels_info.labels)


@shared_task
def lgr_set_annotate_task(lgr_json, script_lgr_json, labels_json, email_address, storage_path):
    """
    Compute dispositions of labels in a LGR.

    :param lgr_json: The LGRInfo as a JSON object.
    :param script_lgr_json: The LGRinfo for the script used to check label validity as a JSON object.
    :param labels_json: The LabelInfo as a JSON object.
    :param email_address: The e-mail address where the results will be sent
    :param storage_path: The place where results will be stored
    """
    lgr_info = LGRInfo.from_dict(lgr_json)
    script_lgr = LGRInfo.from_dict(script_lgr_json).lgr
    labels_info = LabelInfo.from_dict(labels_json)
    set_labels_info = lgr_info.set_labels_info
    if set_labels_info is None:
        set_labels_info = LabelInfo(name='None', labels=[])

    logger.info("Starting task 'annotate' for LGR set %s, with set labels %s, for file %s",
                lgr_info.name, set_labels_info.name, labels_info.name)

    body = "Hi,\nThe processing of annotation from labels provided in the " \
           "file '{f}' in LGR set '{lgr}' with script '{script}' has".format(f=labels_info.name,
                                                                             lgr=lgr_info.lgr.name,
                                                                             script=script_lgr.name)

    _lgr_tool_task(storage_path,
                   base_filename='annotation_{0}'.format(lgr_info.lgr.name),
                   email_subject='LGR Toolset annotation result',
                   email_body=body,
                   email_address=email_address,
                   cb=lgr_set_annotate_labels,
                   lgr=lgr_info.lgr,
                   script_lgr=script_lgr,
                   set_labels=set_labels_info.labels,
                   labels_file=labels_info.labels)


@shared_task
def cross_script_variants_task(lgr_json, labels_json, email_address, storage_path):
    """
    Compute cross-script variants of labels in a LGR.

    :param lgr_json: The LGRInfo as a JSON object.
    :param labels_json: The LabelInfo as a JSON object.
    :param email_address: The e-mail address where the results will be sent
    :param storage_path: The place where results will be stored
    """
    lgr_info = LGRInfo.from_dict(lgr_json)
    labels_info = LabelInfo.from_dict(labels_json)

    logger.info("Starting task 'cross-script variants' for %s, for file %s",
                lgr_info.name, labels_info.name)

    body = "Hi,\nThe processing of cross-script variants from labels provided in the " \
           "file '{f}' in LGR '{lgr}' has".format(f=labels_info.name,
                                                  lgr=lgr_info.name)

    _lgr_tool_task(storage_path,
                   base_filename='cross_script_variants_{0}'.format(lgr_info.name),
                   email_subject='LGR Toolset cross-script variants result',
                   email_body=body,
                   email_address=email_address,
                   cb=lgr_cross_script_variants,
                   lgr=lgr_info.lgr,
                   labels_file=labels_info.labels)


@shared_task
def validate_label_task(lgr_json, label, email_address, storage_path):
    """
    Compute label validation variants of labels in a LGR.

    :param lgr_json: The LGRInfo as a JSON object.
    :param label: The label to validate, as a list of code points.
    :param email_address: The e-mail address where the results will be sent
    :param storage_path: The place where results will be stored
    """
    lgr_info = LGRInfo.from_dict(lgr_json)
    udata = get_db_by_version(lgr_info.lgr.metadata.unicode_version)

    logger.info("Starting task 'validate label' for %s, for input label '%s'",
                lgr_info.name, label)

    u_label = cp_to_ulabel(label)
    body = "Hi,\nThe processing of label validation for label '{label}' in LGR '{lgr}' has".format(label=u_label,
                                                                                                   lgr=lgr_info.name)

    _lgr_tool_task(storage_path,
                   base_filename='label_validation_{0}.csv'.format(lgr_info.name),
                   email_subject='LGR Toolset label validation result',
                   email_body=body,
                   email_address=email_address,
                   cb=lgr_validate_label,
                   lgr=lgr_info.lgr,
                   label=label,
                   udata=udata)


@shared_task
def lgr_set_validate_label_task(lgr_json, script_lgr_json, label, email_address, storage_path):
    """
    Compute label validation variants of labels in a LGR.

    :param lgr_json: The LGRInfo as a JSON object.
    :param script_lgr_json: The LGRInfo for the script used to check label validity as a JSON object.
    :param label: The label to validate, as a list of code points.
    :param email_address: The e-mail address where the results will be sent
    :param storage_path: The place where results will be stored
    """
    lgr_info = LGRInfo.from_dict(lgr_json)
    udata = get_db_by_version(lgr_info.lgr.metadata.unicode_version)
    script_lgr = LGRInfo.from_dict(script_lgr_json).lgr
    set_labels_info = lgr_info.set_labels_info
    if set_labels_info is None:
        set_labels_info = LabelInfo(name='None', labels=[])

    logger.info("Starting task 'validate label' for %s, for input label '%s'",
                lgr_info.name, label)

    u_label = cp_to_ulabel(label)
    body = "Hi,\nThe processing of label validation for label '{label}'" \
           " in LGR set '{lgr}' with script '{script}' has".format(label=u_label,
                                                                   lgr=lgr_info.lgr.name,
                                                                   script=script_lgr.name)

    _lgr_tool_task(storage_path,
                   base_filename='label_validation_{0}.csv'.format(lgr_info.name),
                   email_subject='LGR Toolset label validation result',
                   email_body=body,
                   email_address=email_address,
                   cb=lgr_set_validate_label,
                   lgr=lgr_info.lgr,
                   script_lgr=script_lgr,
                   set_labels=set_labels_info.labels,
                   label=label,
                   udata=udata)


@shared_task
def validate_labels_task(lgr_json, labels_json, email_address, storage_path):
    """
    Compute multiple labels validation variants of labels in a LGR.

    :param lgr_json: The LGRInfo as a JSON object.
    :param labels_json: The LabelInfo as a JSON object.
    :param email_address: The e-mail address where the results will be sent
    :param storage_path: The place where results will be stored
    """
    lgr_info = LGRInfo.from_dict(lgr_json)
    labels_info = LabelInfo.from_dict(labels_json)
    udata = get_db_by_version(lgr_info.lgr.metadata.unicode_version)

    logger.info("Starting task 'validate label' for %s, for file '%s'",
                lgr_info.name, labels_info.name)

    body = "Hi,\nThe processing of variant computation for file '{f}' in LGR '{lgr}' has".format(f=labels_info.name,
                                                                                                 lgr=lgr_info.name)

    _lgr_tool_task(storage_path,
                   base_filename='labels_variants_{0}.csv'.format(lgr_info.name),
                   email_subject='LGR Toolset variants computation result',
                   email_body=body,
                   email_address=email_address,
                   cb=lgr_validate_labels,
                   lgr=lgr_info.lgr,
                   labels_file=labels_info.labels,
                   udata=udata)
