# -*- coding: utf-8 -*-
import codecs
import csv
import datetime
import hashlib
import logging
from io import StringIO

from celery import shared_task, current_task
from django.conf import settings
from django.core.cache import cache
from django.utils import timezone
from django.utils.encoding import force_bytes

from lgr.exceptions import NotInLGR
from lgr.tools.utils import download_file, read_labels
from lgr.utils import cp_to_ulabel
from lgr_advanced.api import LabelInfo
from lgr_auth.models import LgrUser
from lgr_manage.api import LGRAdminReportStorage
from lgr_models.models.lgr import RzLgr
from lgr_models.models.report import LGRReport
from lgr_tasks.models import LgrTaskModel
from lgr_utils.utils import LGR_CACHE_KEY_PREFIX
from lgr_web.config import lgr_settings

logger = logging.getLogger(__name__)

VARIANT_LABELS_INDEXES_CACHE_KEY = 'indexes'
INDEX_CACHE_TIMEOUT = settings.TASK_REFRESH_FREQUENCY + 3600


@shared_task
def clean_reports():
    """
    Clean user reports after a certain amount of time
    """
    logger.info('Cleaning reports older than %d days' % lgr_settings.report_expiration_delay)
    # set the last run in the settings data
    lgr_settings.report_expiration_last_run = timezone.now()
    lgr_settings.save()
    nbr, __ = LGRReport.objects.filter(
        created_at__lt=datetime.datetime.now() - datetime.timedelta(days=lgr_settings.report_expiration_delay)
    ).delete()
    logger.info('%d reports removed' % nbr)


@shared_task
def calculate_index_variant_labels_tlds(user_pk=None):
    """
    Calculate the index variant labels of the existing TLDs against the selected RZ LGR
    """
    logger.info('Calculate the index variant labels of the existing TLDs against the default RZ LGR')
    tlds_raw = download_file(settings.ICANN_TLDS)[1].read().lower()
    tlds = LabelInfo.from_form('TLDs', tlds_raw).labels
    rz_lgr_object: RzLgr = RzLgr.objects.filter(active=True).first()  # there should be only one
    rz_lgr = rz_lgr_object.to_lgr()
    indexes = {}
    out = StringIO()
    # write BOM at the beginning to allow Excel decoding UTF-8
    out.write(codecs.BOM_UTF8.decode('utf-8'))
    writer = csv.writer(out)
    writer.writerow(['Label', 'Index'])

    for __, label, valid, error in read_labels(tlds, rz_lgr.unicode_database):
        if not valid:
            logger.warning(f'{label} is invalid: {error}')
            indexes[label] = 'ERROR'
            writer.writerow([label, 'ERROR'])
            continue
        try:
            label_cp = tuple([ord(c) for c in label])
            index = rz_lgr.generate_index_label(label_cp)
            indexes[label] = index
            writer.writerow([label, ''.join(cp_to_ulabel(c) for c in index)])
        except NotInLGR:
            logger.warning(f'{label} is not in LGR')
            indexes[label] = 'NotInLGR'
            writer.writerow([label, 'NotInLGR'])

    cache.set(_index_cache_key(rz_lgr_object), indexes, INDEX_CACHE_TIMEOUT)

    return _save_report(user_pk, out)


def _save_report(user_pk, data):
    # save indexes as report
    user = None
    if user_pk:
        user = LgrUser.objects.get(pk=user_pk)
    storage = LGRAdminReportStorage(user)
    if not user:
        # remove old reports automatically launched
        storage.list_storage(exclude={'owner__isnull': False}).delete()
    filename = f"tlds-indexes-{timezone.now().strftime('%Y-%m-%d-%H%M%S.%f')}.csv"
    report = storage.storage_save_report_file(filename, data)
    if isinstance(current_task.request.id, int):
        try:
            LgrTaskModel.objects.filter(pk=current_task.request.id).update(report=report)
        except LgrTaskModel.DoesNotExist:
            # the task has been launched automatically
            pass
    return filename


def _index_cache_key(rz_lgr_object):
    lgr_model, lgr_pk = rz_lgr_object.to_tuple()
    key = f'{VARIANT_LABELS_INDEXES_CACHE_KEY}:{lgr_model}:{lgr_pk}'
    args = hashlib.md5(force_bytes(key))
    return "{}.{}".format(LGR_CACHE_KEY_PREFIX, args.hexdigest())
