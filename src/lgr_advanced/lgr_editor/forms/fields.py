# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import hashlib
import logging
from itertools import chain
from typing import List

from django.core.cache import cache
from django.utils.encoding import force_bytes
from django.utils.translation import ugettext_lazy as _

from lgr_models.models.lgr import LgrBaseModel, RzLgr, MSR
from lgr_utils.utils import LGR_CACHE_KEY_PREFIX

FILE_FIELD_ENCODING_HELP = _('File must be encoded in UTF-8 and using 0x0A line ending.')

logger = logging.getLogger(__name__)


class ValidatingRepertoire:
    REPERTOIRE_CACHE_KEY = 'validating-repertoire'
    SCRIPTS_CACHE_KEY = 'scripts'
    CACHE_TIMEOUT = 3600 * 24 * 30

    @classmethod
    def list(cls) -> List[LgrBaseModel]:
        return sorted(list(chain(RzLgr.objects.filter(active=True), MSR.objects.filter(active=True))), key=lambda l: l.name)

    @classmethod
    def choices(cls):
        return tuple((v.to_tuple(), v.name) for v in cls.list())

    @classmethod
    def default_choice(cls):
        return '', ''

    @classmethod
    def _cache_key(cls, unicode_database, vr_model, vr_pk):
        key = f'{cls.SCRIPTS_CACHE_KEY}:{unicode_database.get_unicode_version()}:{vr_model}:{vr_pk}'
        args = hashlib.md5(force_bytes(key))
        return "{}.{}".format(LGR_CACHE_KEY_PREFIX, args.hexdigest())

    @classmethod
    def scripts(cls, unicode_database):
        logger.debug("Get scripts for Unicode %s", unicode_database.get_unicode_version())
        scripts = dict()
        for validating_repertoire_object in cls.list():
            vr_model, vr_pk = validating_repertoire_object.to_tuple()
            scripts_cache_key = cls._cache_key(unicode_database, vr_model, vr_pk)
            vr_scripts = cache.get(scripts_cache_key)
            if not vr_scripts:
                vr_scripts = set()
                logger.info(f'Scripts for {validating_repertoire_object.name} not in cache')
                validating_repertoire = validating_repertoire_object.to_lgr(with_unidb=False, expand_ranges=True)
                for char in validating_repertoire.repertoire.all_repertoire():
                    for cp in char.cp:
                        try:
                            # XXX: unicode version here may be different than validating repertoire one
                            vr_scripts.add(unicode_database.get_script(cp, alpha4=True))
                        except Exception as e:
                            logger.error(
                                'Get script failed for cp %s (validating repertoire: %s, unicode_database: %s) (%s)',
                                cp, validating_repertoire,
                                unicode_database.get_unicode_version(),
                                e)

                cache.set(scripts_cache_key, vr_scripts, cls.CACHE_TIMEOUT)

            scripts[(vr_model, vr_pk)] = vr_scripts

        return scripts
