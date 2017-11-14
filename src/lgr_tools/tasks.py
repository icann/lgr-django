# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import time
from cStringIO import StringIO
from gzip import GzipFile

from celery import shared_task
from django.core.files.storage import FileSystemStorage
from django.core.mail import EmailMessage

from lgr.exceptions import LGRException

from lgr_editor.api import LabelInfo, LGRInfo
from lgr_editor.lgr_exceptions import lgr_exception_to_text
from lgr_tools.api import lgr_diff_labels, lgr_collision_labels, lgr_annotate_labels, lgr_set_annotate_labels, lgr_cross_script_variants

logger = logging.getLogger(__name__)


def _lgr_tool_task(storage_path, base_filename, email_subject,
                   email_body, email_address, cb, **cb_kwargs):
    """
    Launch the tool task and send e-mail


    :param storage_path: The place where results will be stored
    :param base_filename: The beginning of the filename that will be generated
    :param email_subject: The subject for the e-mail to be sent
    :param email_body: The body of the e-mail to be sent
    :param email_address: The e-mail address where the results will be sent
    :param cb: The callback to launch the tool
    :param cb_kwargs: The argument for the callback
    """
    sio = StringIO()
    email = EmailMessage(subject='{}'.format(email_subject),
                         to=[email_address])

    try:
        with GzipFile(filename='{}.txt'.format(base_filename),
                      fileobj=sio, mode='w') as gzf:
            for line in cb(**cb_kwargs):
                gzf.write(line.encode('utf-8'))

        filename = '{0}_{1}.txt.gz'.format(time.strftime('%Y%m%d_%H%M%S'),
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
def collision_task(lgr_json, labels_json, email_address, full_dump,
                   with_rules, storage_path):
    """
    Compute collision between labels in an LGR

    :param lgr_json: The LGRInfo as a JSON object.
    :param labels_json: The LabelInfo as a JSON object.
    :param email_address: The e-mail address where the results will be sent
    :param full_dump: Whether we also output a full dump
    :param with_rules: Whether we also output rules
    :param storage_path: The place where results will be stored
    :return:
    """
    lgr = LGRInfo.from_dict(lgr_json).lgr
    labels_info = LabelInfo.from_dict(labels_json)

    logger.info("Starting task 'collision' for %s, for file %s",
                lgr.name, labels_info.name)

    body = "Hi,\nThe processing of collisions from labels provided in the " \
           "file '{f}' in LGR '{lgr}' has".format(f=labels_info.name,
                                                  lgr=lgr.name)
    _lgr_tool_task(storage_path,
                   base_filename='collisions_{0}'.format(lgr.name),
                   email_subject='LGR Toolset collisions result',
                   email_body=body,
                   email_address=email_address,
                   cb=lgr_collision_labels,
                   lgr=lgr,
                   labels_file=labels_info.labels,
                   full_dump=full_dump,
                   with_rules=with_rules)


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
