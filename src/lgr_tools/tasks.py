# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import time
from gzip import GzipFile
from cStringIO import StringIO
from codecs import iterdecode
import logging

from celery import shared_task

from django.core.mail import EmailMessage
from django.core.files.storage import FileSystemStorage

from lgr.exceptions import LGRException
from lgr.parser.xml_parser import XMLParser
from lgr_tools.api import lgr_diff_labels, lgr_collision_labels, lgr_annotate_labels
from lgr_editor.api import unidb
from lgr_editor.lgr_exceptions import lgr_exception_to_text

logger = logging.getLogger(__name__)


def _lgr_tool_task(labels_info, storage_path, base_filename, email_subject,
                   email_body, email_address, cb, **cb_kwargs):
    """
    Launch the tool task and send e-mail


    :param labels_info: The labels useful data
    :param storage_path: The place where results will be stored
    :param base_filename: The beginning of the filename that will be generated
    :param email_subject: The subject for the e-mail to be sent
    :param email_body: The body of the e-mail to be sent
    :param email_address: The e-mail address where the results will be sent
    :param cb: The callback to launch the tool
    :param cb_kwargs: The argument for the callback

    :return:
    """
    sio = StringIO()
    email = EmailMessage(subject='{}'.format(email_subject),
                         to=[email_address])
    email.attach(labels_info['name'], labels_info['data'], 'text/plain')

    try:
        with GzipFile(filename='{}.txt'.format(base_filename),
                      fileobj=sio, mode='w') as gzf:
            for line in cb(**cb_kwargs):
                gzf.write(line.encode('utf-8'))

        filename = '{0}_{1}.txt.gz'.format(base_filename,
                                           time.strftime('%Y%m%d_%H%M%S'))

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
def diff_task(lgr_1, lgr_2, labels_info, email_address, collision, full_dump,
              with_rules, storage_path):
    """
    Launch difference computation for a list of labels between two LGR

    :param lgr_1: The first LGR useful elements
    :param lgr_2: The second LGR useful elements
    :param labels_info: The labels useful data
    :param email_address: The e-mail address where the results will be sent
    :param collision: Whether we also compute collisions
    :param full_dump: Whether we also output a full dump
    :param with_rules: Whether we also output rules
    :param storage_path: The place where results will be stored
    :return:
    """
    lgr1_parser = XMLParser(StringIO(lgr_1['xml'].encode('utf-8')),
                            lgr_1['name'])
    lgr2_parser = XMLParser(StringIO(lgr_2['xml'].encode('utf-8')),
                            lgr_2['name'])
    lgr1 = lgr1_parser.parse_document()
    lgr2 = lgr2_parser.parse_document()
    lgr1.unicode_database = unidb.manager.get_db_by_version(
        lgr1.metadata.unicode_version)
    lgr2.unicode_database = unidb.manager.get_db_by_version(
        lgr2.metadata.unicode_version)
    labels = iterdecode(StringIO(labels_info['data'].encode('utf-8')), 'utf-8')

    body = "Hi,\nThe processing of diff from labels provided in the attached " \
           "file '{f}' between LGR '{lgr1}' and " \
           "LGR '{lgr2}' has".format(f=labels_info['name'],
                                     lgr1=lgr1.name,
                                     lgr2=lgr2.name)

    _lgr_tool_task(labels_info, storage_path,
                   base_filename='diff_{0}_{1}'.format(lgr1.name,
                                                       lgr2.name),
                   email_subject='LGR Toolset diff result',
                   email_body=body,
                   email_address=email_address,
                   cb=lgr_diff_labels,
                   lgr_1=lgr1, lgr_2=lgr2,
                   labels_file=labels,
                   show_collision=collision,
                   full_dump=full_dump,
                   with_rules=with_rules)


@shared_task
def collision_task(lgr_info, labels_info, email_address, full_dump,
                   with_rules, storage_path):
    """
    Compute collision between labels in an LGR

    :param lgr_info: The second LGR useful elements
    :param labels_info: The labels useful data
    :param email_address: The e-mail address where the results will be sent
    :param full_dump: Whether we also output a full dump
    :param with_rules: Whether we also output rules
    :param storage_path: The place where results will be stored
    :return:
    """
    lgr_parser = XMLParser(StringIO(lgr_info['xml'].encode('utf-8')),
                           lgr_info['name'])
    lgr = lgr_parser.parse_document()
    lgr.unicode_database = unidb.manager.get_db_by_version(
        lgr.metadata.unicode_version)
    labels = iterdecode(StringIO(labels_info['data'].encode('utf-8')), 'utf-8')

    body = "Hi,\nThe processing of collisions from labels provided in the " \
           "attached file '{f}' in LGR '{lgr}' has".format(f=labels_info['name'],
                                                           lgr=lgr.name)
    _lgr_tool_task(labels_info, storage_path,
                   base_filename='collisions_{0}'.format(lgr.name),
                   email_subject='LGR Toolset collisions result',
                   email_body=body,
                   email_address=email_address,
                   cb=lgr_collision_labels,
                   lgr=lgr,
                   labels_file=labels,
                   full_dump=full_dump,
                   with_rules=with_rules)


@shared_task
def annotate_task(lgr_info, labels_info, email_address, storage_path):
    """
    Compute dispositions of labels in a LGR.

    :param lgr_info: The LGR to use.
    :param labels_info: The labels useful data
    :param email_address: The e-mail address where the results will be sent
    :param storage_path: The place where results will be stored
    """
    lgr_parser = XMLParser(StringIO(lgr_info['xml'].encode('utf-8')),
                           lgr_info['name'])
    lgr = lgr_parser.parse_document()
    lgr.unicode_database = unidb.manager.get_db_by_version(
        lgr.metadata.unicode_version)
    labels = iterdecode(StringIO(labels_info['data'].encode('utf-8')), 'utf-8')

    body = "Hi,\nThe processing of annotation from labels provided in the " \
           "attached file '{f}' in LGR '{lgr}' has".format(f=labels_info['name'],
                                                           lgr=lgr.name)

    _lgr_tool_task(labels_info, storage_path,
                   base_filename='annotation_{0}'.format(lgr.name),
                   email_subject='LGR Toolset annotation result',
                   email_body=body,
                   email_address=email_address,
                   cb=lgr_annotate_labels,
                   lgr=lgr,
                   labels_file=labels)
