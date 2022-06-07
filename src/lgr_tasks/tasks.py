# -*- coding: utf-8 -*-
import hashlib
import logging

from celery import shared_task
from django.conf import settings
from django.utils.encoding import force_bytes

from lgr.exceptions import NotInLGR
from lgr.tools.utils import download_file, read_labels
from lgr_advanced.api import LabelInfo
from lgr_models.models.lgr import RzLgr
from lgr_utils.utils import LGR_CACHE_KEY_PREFIX
from django.core.cache import cache

logger = logging.getLogger(__name__)

VARIANT_LABELS_INDEXES_CACHE_KEY = 'indexes'
INDEX_CACHE_TIMEOUT = settings.INDEX_REFRESH_FREQUENCY + 3600


@shared_task
def calculate_index_variant_labels_tlds():
    """
    Calcul the index variant labels of the existing TLDs against the selected RZ LGR
    """
    tlds_raw = download_file(settings.ICANN_TLDS)[1].read().lower()
    tlds = LabelInfo.from_form('TLDs', tlds_raw).labels
    rz_lgr_object: RzLgr = RzLgr.objects.filter(active=True).first()  # there should be only one
    rz_lgr = rz_lgr_object.to_lgr()
    lgr_model, lgr_pk = rz_lgr_object.to_tuple()
    for label, valid, error in read_labels(tlds, rz_lgr.unicode_database):
        if not valid:
            cache.set(_cache_key(label, lgr_model, lgr_pk), f'ERROR: {error}', INDEX_CACHE_TIMEOUT)
            continue
        try:
            label_cp = tuple([ord(c) for c in label])
            index = rz_lgr.generate_index_label(label_cp)
            cache.set(_cache_key(label, lgr_model, lgr_pk), index, INDEX_CACHE_TIMEOUT)
        except NotInLGR:
            cache.set(_cache_key(label, lgr_model, lgr_pk), 'NotInLGR', INDEX_CACHE_TIMEOUT)


def _cache_key(label, lgr_model, lgr_pk):
    # XXX: if indexes for multiple LGRs are computed for the same label may investigate if using
    #      HGET/HSET (label lgr index) would be better or not
    key = f'{VARIANT_LABELS_INDEXES_CACHE_KEY}:{label}:{lgr_model}:{lgr_pk}'
    args = hashlib.md5(force_bytes(key))
    return "{}.{}".format(LGR_CACHE_KEY_PREFIX, args.hexdigest())
