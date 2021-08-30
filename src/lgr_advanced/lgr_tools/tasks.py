# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import logging
import time
from gzip import GzipFile
from io import BytesIO

from celery import shared_task
from django.core.mail import EmailMessage

from lgr.exceptions import LGRException
from lgr.utils import cp_to_ulabel
from lgr_advanced.api import LabelInfo, LGRToolStorage
from lgr_advanced.lgr_exceptions import lgr_exception_to_text
from lgr_advanced.lgr_tools.api import (lgr_diff_labels,
                                        lgr_collision_labels,
                                        lgr_annotate_labels,
                                        lgr_set_annotate_labels,
                                        lgr_cross_script_variants,
                                        lgr_validate_label,
                                        lgr_set_validate_label,
                                        lgr_validate_labels,
                                        lgr_basic_collision_labels)
from lgr_advanced.models import LgrModel, SetLgrModel
from lgr_auth.models import LgrUser
from lgr_models.utils import get_model_from_name
from lgr_utils.unidb import get_db_by_version

logger = logging.getLogger(__name__)


def _lgr_tool_task(user, base_filename, email_subject,
                   email_body, cb, **cb_kwargs):
    """
    Launch the tool task and send e-mail

    :param user: The user that will receive the email and own the report
    :param storage_path: The place where results will be stored
    :param base_filename: The filename that will be generated (.txt is added if it has no extension)
    :param email_subject: The subject for the e-mail to be sent
    :param email_body: The body of the e-mail to be sent
    :param cb: The callback to launch the tool
    :param cb_kwargs: The argument for the callback
    """
    sio = BytesIO()
    email = EmailMessage(subject=email_subject, to=[user.email])
    if '.' not in base_filename:
        base_filename += '.txt'

    try:
        with GzipFile(filename=base_filename,
                      fileobj=sio, mode='w') as gzf:
            for line in cb(**cb_kwargs):
                gzf.write(line.encode('utf-8'))

        filename = '{0}_{1}.gz'.format(time.strftime('%Y%m%d_%H%M%S'),
                                       base_filename)

        lgr_storage = LGRToolStorage(user)

        report = lgr_storage.storage_save_report_file(filename, sio)
        email.body = f"{email_body} been successfully completed.\n" \
                     f"You should now be able to download it from your home screen under the name: " \
                     f"'{report.report_id}'.\nPlease refresh the home page if you don't see the link.\nBest regards"
    except LGRException as ex:
        email.body = f'{email_body} failed with error:\n{lgr_exception_to_text(ex)}\nBest regards'
        logger.exception('Error in tool computation:')
    except BaseException:
        email.body = f'{email_body} failed with unknown error.\nBest regards'
        logger.exception('Error in tool computation:')
    finally:
        sio.close()
        email.send()

@shared_task
def diff_task(user_pk, lgr_pk_1, lgr_pk_2, labels_json, collision, full_dump,
              with_rules):
    """
    Launch difference computation for a list of labels between two LGR

    :param user_pk: The user primary key
    :param lgr_pk_1: The first LGR primary key
    :param lgr_pk_2: The second LGR primary key
    :param labels_json: The LabelInfo as a JSON object.
    :param collision: Whether we also compute collisions
    :param full_dump: Whether we also output a full dump
    :param with_rules: Whether we also output rules
    :return:
    """
    user = LgrUser.objects.get(pk=user_pk)
    lgr1 = LgrModel.get_object(user, lgr_pk_1).to_lgr()
    lgr2 = LgrModel.get_object(user, lgr_pk_2).to_lgr()
    labels_info = LabelInfo.from_dict(labels_json)

    logger.info("Starting task 'diff' between %s and %s, for file %s",
                lgr1.name, lgr2.name, labels_info.name)

    body = "Hi,\nThe processing of diff from labels provided in the " \
           "file '{f}' between LGR '{lgr1}' and " \
           "LGR '{lgr2}' has".format(f=labels_info.name,
                                     lgr1=lgr1.name,
                                     lgr2=lgr2.name)

    _lgr_tool_task(user=user,
                   base_filename='diff_{0}_{1}'.format(lgr1.name,
                                                       lgr2.name),
                   email_subject='LGR Toolset diff result',
                   email_body=body,
                   cb=lgr_diff_labels,
                   lgr_1=lgr1, lgr_2=lgr2,
                   labels_file=labels_info.labels,
                   show_collision=collision,
                   full_dump=full_dump,
                   with_rules=with_rules)


@shared_task
def collision_task(user_pk, lgr_pk, labels_json, tld_json, full_dump, with_rules):
    """
    Compute collision between labels in an LGR

    :param user_pk: The user primary key
    :param lgr_pk: The LGR primary key
    :param labels_json: The LabelInfo as a JSON object containing labels to check for coliision.
    :param tld_json: The LabelInfo as a JSON object containing TLDs.
    :param full_dump: Whether we also output a full dump
    :param with_rules: Whether we also output rules
    """
    user = LgrUser.objects.get(pk=user_pk)
    lgr = LgrModel.get_object(user, lgr_pk).to_lgr()
    labels_info = LabelInfo.from_dict(labels_json)
    tlds_info = LabelInfo.from_dict(tld_json) if tld_json else None

    logger.info("Starting task 'collision' for %s, for file %s",
                lgr.name, labels_info.name)

    body = "Hi,\nThe processing of collisions from labels provided in {input} in LGR '{lgr}' has".format(
        input="the file '{}'".format(labels_info.name) if labels_info.name else 'ICANN tlds',
        lgr=lgr.name)
    _lgr_tool_task(user=user,
                   base_filename='collisions_{0}'.format(lgr.name),
                   email_subject='LGR Toolset collisions result',
                   email_body=body,
                   cb=lgr_collision_labels,
                   lgr=lgr,
                   labels_file=labels_info.labels,
                   tlds_file=tlds_info.labels if tld_json else None,
                   full_dump=full_dump,
                   with_rules=with_rules)


@shared_task
def basic_collision_task(user_pk, lgr_pk, labels_json, tld_json, annotate=False, lgr_model=LgrModel):
    """
    Compute collision between labels in an LGR

    :param user_pk: The user primary key
    :param lgr_pk: The LGR primary key
    :param labels_json: The LabelInfo as a JSON object containing labels to check for coliision.
    :param tld_json: The LabelInfo as a JSON object containing TLDs.
    :param annotate: Whether the labels should also be annotated
    :param lgr_model: The model of the LGR in database
    """
    user = LgrUser.objects.get(pk=user_pk)
    lgr_model = get_model_from_name(lgr_model)
    lgr = lgr_model.get_object(user, lgr_pk).to_lgr()
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
    _lgr_tool_task(user=user,
                   base_filename='{}_{}'.format(task_name.replace(" ", "_"), lgr.name),
                   email_subject='LGR Toolset {} result'.format(task_name),
                   email_body=body,
                   cb=lgr_basic_collision_labels,
                   lgr=lgr,
                   labels_file=labels_info.labels,
                   tlds_file=tlds_info.labels if tld_json else None,
                   with_annotate=annotate)


@shared_task
def annotate_task(user_pk, lgr_pk, labels_json, lgr_model=LgrModel):
    """
    Compute dispositions of labels in a LGR.

    :param user_pk: The user primary key
    :param lgr_pk: The LGR primary key
    :param labels_json: The LabelInfo as a JSON object.
    :param lgr_model: The model of the LGR in database
    """
    user = LgrUser.objects.get(pk=user_pk)
    lgr_model = get_model_from_name(lgr_model)
    lgr = lgr_model.get_object(user, lgr_pk).to_lgr()
    labels_info = LabelInfo.from_dict(labels_json)

    logger.info("Starting task 'annotate' for %s, for file %s",
                lgr.name, labels_info.name)

    body = "Hi,\nThe processing of annotation from labels provided in the " \
           "file '{f}' in LGR '{lgr}' has".format(f=labels_info.name,
                                                  lgr=lgr.name)

    _lgr_tool_task(user=user,
                   base_filename='annotation_{0}'.format(lgr.name),
                   email_subject='LGR Toolset annotation result',
                   email_body=body,
                   cb=lgr_annotate_labels,
                   lgr=lgr,
                   labels_file=labels_info.labels)


@shared_task
def lgr_set_annotate_task(user_pk, lgr_pk, labels_json, set_labels_json, script_lgr_pk):
    """
    Compute dispositions of labels in a LGR.

    :param user_pk: The user primary key
    :param lgr_pk: The LGR primary key
    :param labels_json: The LabelInfo as a JSON object.
    :param set_labels_json: The LabelInfo allocated in set as a JSON object.
    :param script_lgr_pk: The LGR primary key for the script used to check label validity.
    """
    user = LgrUser.objects.get(pk=user_pk)
    lgr = LgrModel.get_object(user, lgr_pk).to_lgr()
    script_lgr = SetLgrModel.get_object(user, script_lgr_pk).to_lgr()
    labels_info = LabelInfo.from_dict(labels_json)
    set_labels_info = LabelInfo.from_dict(set_labels_json)

    logger.info("Starting task 'annotate' for LGR set %s, with set labels %s, for file %s",
                lgr.name, set_labels_info.name, labels_info.name)

    body = "Hi,\nThe processing of annotation from labels provided in the " \
           "file '{f}' in LGR set '{lgr}' with script '{script}' has".format(f=labels_info.name,
                                                                             lgr=lgr.name,
                                                                             script=script_lgr.name)

    _lgr_tool_task(user=user,
                   base_filename='annotation_{0}'.format(lgr.name),
                   email_subject='LGR Toolset annotation result',
                   email_body=body,
                   cb=lgr_set_annotate_labels,
                   lgr=lgr,
                   script_lgr=script_lgr,
                   set_labels=set_labels_info.labels,
                   labels_file=labels_info.labels)


@shared_task
def cross_script_variants_task(user_pk, lgr_pk, in_set, labels_json):
    """
    Compute cross-script variants of labels in a LGR.

    :param user_pk: The user primary key
    :param lgr_pk: The LGR primary key
    :param in_set: Whether the LGR is embedded in a LGR set
    :param labels_json: The LabelInfo as a JSON object.
    """
    user = LgrUser.objects.get(pk=user_pk)
    lgr_model = SetLgrModel if in_set else LgrModel
    lgr = lgr_model.get_object(user, lgr_pk).to_lgr()
    labels_info = LabelInfo.from_dict(labels_json)

    logger.info("Starting task 'cross-script variants' for %s, for file %s",
                lgr.name, labels_info.name)

    body = "Hi,\nThe processing of cross-script variants from labels provided in the " \
           "file '{f}' in LGR '{lgr}' has".format(f=labels_info.name,
                                                  lgr=lgr.name)

    _lgr_tool_task(user=user,
                   base_filename='cross_script_variants_{0}'.format(lgr.name),
                   email_subject='LGR Toolset cross-script variants result',
                   email_body=body,
                   cb=lgr_cross_script_variants,
                   lgr=lgr,
                   labels_file=labels_info.labels)


@shared_task
def validate_label_task(user_pk, lgr_pk, label, lgr_model=LgrModel):
    """
    Compute label validation variants of labels in a LGR.

    :param user_pk: The user primary key
    :param lgr_pk: The LGR primary key
    :param label: The label to validate, as a list of code points.
    :param lgr_model: The model of the LGR in database
    """
    user = LgrUser.objects.get(pk=user_pk)
    lgr_model = get_model_from_name(lgr_model)
    lgr = lgr_model.get_object(user, lgr_pk).to_lgr()
    udata = get_db_by_version(lgr.metadata.unicode_version)

    logger.info("Starting task 'validate label' for %s, for input label '%s'",
                lgr.name, label)

    u_label = cp_to_ulabel(label)
    body = "Hi,\nThe processing of label validation for label '{label}' in LGR '{lgr}' has".format(label=u_label,
                                                                                                   lgr=lgr.name)

    _lgr_tool_task(user=user,
                   base_filename='label_validation_{0}.csv'.format(lgr.name),
                   email_subject='LGR Toolset label validation result',
                   email_body=body,
                   cb=lgr_validate_label,
                   lgr=lgr,
                   label=label,
                   udata=udata)


@shared_task
def lgr_set_validate_label_task(user_pk, lgr_pk, script_lgr_pk, label, set_labels_json):
    """
    Compute label validation variants of labels in a LGR.

    :param user_pk: The user primary key
    :param lgr_pk: The LGR primary key
    :param script_lgr_pk: The LGR primary key for the script used to check label validity
    :param label: The label to validate, as a list of code points.
    :param set_labels_json: The LabelInfo allocated in set as a JSON object.
    """
    user = LgrUser.objects.get(pk=user_pk)
    lgr = LgrModel.get_object(user, lgr_pk).to_lgr()
    udata = get_db_by_version(lgr.metadata.unicode_version)
    script_lgr = SetLgrModel.get_object(user, script_lgr_pk).to_lgr()
    set_labels_info = LabelInfo.from_dict(set_labels_json)

    logger.info("Starting task 'validate label' for %s, for input label '%s'", lgr.name, label)

    u_label = cp_to_ulabel(label)
    body = "Hi,\nThe processing of label validation for label '{label}'" \
           " in LGR set '{lgr}' with script '{script}' has".format(label=u_label,
                                                                   lgr=lgr.name,
                                                                   script=script_lgr.name)

    _lgr_tool_task(user=user,
                   base_filename='label_validation_{0}.csv'.format(lgr.name),
                   email_subject='LGR Toolset label validation result',
                   email_body=body,
                   user_pk=user_pk,
                   cb=lgr_set_validate_label,
                   lgr=lgr,
                   script_lgr=script_lgr,
                   set_labels=set_labels_info.labels,
                   label=label,
                   udata=udata)


@shared_task
def validate_labels_task(user_pk, lgr_pk, labels_json):
    """
    Compute multiple labels validation variants of labels in a LGR.

    :param user_pk: The user primary key
    :param lgr_pk: The LGR primary key
    :param labels_json: The LabelInfo as a JSON object.
    """
    user = LgrUser.objects.get(pk=user_pk)
    lgr = LgrModel.get_object(user, lgr_pk).to_lgr()
    labels_info = LabelInfo.from_dict(labels_json)
    udata = get_db_by_version(lgr.metadata.unicode_version)

    logger.info("Starting task 'validate label' for %s, for file '%s'",
                lgr.name, labels_info.name)

    body = "Hi,\nThe processing of variant computation for file '{f}' in LGR '{lgr}' has".format(f=labels_info.name,
                                                                                                 lgr=lgr.name)

    _lgr_tool_task(user=user,
                   base_filename='labels_variants_{0}.csv'.format(lgr.name),
                   email_subject='LGR Toolset variants computation result',
                   email_body=body,
                   cb=lgr_validate_labels,
                   lgr=lgr,
                   labels_file=labels_info.labels,
                   udata=udata)
