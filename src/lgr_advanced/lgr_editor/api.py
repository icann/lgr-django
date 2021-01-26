# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.core.files.storage import FileSystemStorage
from django.http import Http404
from django.utils.text import slugify

from lgr.parser.xml_serializer import serialize_lgr_xml
from lgr.tools.merge_set import merge_lgr_set
from ..utils import clean_repertoire_cache
from ..api import LGRInfo, session_open_lgr, session_save_lgr, session_get_storage

logger = logging.getLogger(__name__)


def session_new_lgr(request, lgr_id, unicode_version, validating_repertoire_name):
    """
    Create a new, blank LGR, and save it in session.

    :param request: Django request object
    :param lgr_id: a slug identifying the LGR
    :param unicode_version: version of Unicode applicable to this LGR
    :param validating_repertoire_name: name of a validating repertoire
    :return: `LGRInfo`
    """
    lgr_info = LGRInfo.create(name=lgr_id,
                              unicode_version=unicode_version,
                              validating_repertoire_name=validating_repertoire_name)
    session_save_lgr(request, lgr_info)
    return lgr_info


def session_delete_lgr(request, lgr_id):
    """
    Delete the LGR object from session
    :param request: Django request object
    :param lgr_id: a slug identifying the LGR
    """
    try:
        del request.session['lgr'][lgr_id]
    except KeyError:
        raise Http404
    # mark session as modified because we are possibly only changing the content of a dict
    request.session.modified = True
    # Remove cached repertoire
    clean_repertoire_cache(request, lgr_id)


def session_merge_set(request, lgr_info_set, lgr_set_name):
    """
    Merge some LGR to build a set.

    :param request: Django request object
    :param lgr_info_set: The list of LGRInfo objects in the set
    :param lgr_set_name: The name of the LGR set
    :return: The LGR set merge id
    """
    merged_lgr = merge_lgr_set([l.lgr for l in lgr_info_set], lgr_set_name)
    merged_id = slugify(merged_lgr.name)

    merged_lgr_xml = serialize_lgr_xml(merged_lgr)

    session_open_lgr(request, merged_id, merged_lgr_xml,
                     validating_repertoire_name=None,
                     validate=True, lgr_set=lgr_info_set)
    return merged_id


def session_get_file(request, filename):
    """
    Get a file in the storage

    :param request: Django request object
    :param filename: The name of the file to be returned
    :return: A 2-tuple containing the File object and the file size
    """
    storage = FileSystemStorage(location=session_get_storage(request))
    return storage.open(filename, 'rb'), storage.size(filename)


def session_delete_file(request, filename):
    """
    Delete a file from the storage

    :param request: Django request object
    :param filename: The name of the file to delete
    """
    storage = FileSystemStorage(location=session_get_storage(request))
    try:
        storage.delete(filename)
    except NotImplementedError:
        # should not happen
        pass
