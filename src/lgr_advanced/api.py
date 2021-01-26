#! /bin/env python
# -*- coding: utf-8 -*-
# Author: Viagénie
"""
api - 
"""
import base64
import errno
import logging
import os
from functools import partial
from uuid import uuid4

from django.conf import settings
from django.core.cache import cache
from django.core.files.storage import FileSystemStorage
from django.http import Http404
from django.utils import six

from lgr.core import LGR
from lgr.metadata import Metadata, Version
from lgr.parser.xml_parser import XMLParser, LGR_NS
from lgr.parser.xml_serializer import serialize_lgr_xml
from lgr_advanced import unidb
from lgr_advanced.exceptions import LGRValidationException
from lgr_advanced.lgr_editor.repertoires import get_by_name
from lgr_advanced.utils import (list_root_zones,
                                make_lgr_session_key,
                                clean_repertoire_cache,
                                LGR_CACHE_TIMEOUT,
                                LGR_OBJECT_CACHE_KEY)

logger = logging.getLogger(__name__)

OLD_LGR_NS = 'http://www.iana.org/lgr/0.1'
LGRS_SESSION_KEY = 'lgr'


class LGRInfo(object):
    def __init__(self, name, lgr=None, xml=None, validating_repertoire=None, lgr_set=None, set_labels_info=None):
        self.name = name
        self.lgr = lgr
        self.xml = xml
        self.validating_repertoire = validating_repertoire
        self.lgr_set = lgr_set
        self.set_labels_info = set_labels_info  # List of labels defined for the LGR set, optional

    def update_xml(self, pretty_print=False, validate=False):
        # if something was changed in `lgr`, calling this will re-generate the xml
        new_xml = serialize_lgr_xml(self.lgr, pretty_print=pretty_print)
        if validate:
            parser = XMLParser(six.BytesIO(new_xml), self.name)

            validation_result = parser.validate_document(settings.LGR_RNG_FILE)
            if validation_result is not None:
                raise LGRValidationException(validation_result)

        self.xml = new_xml

    @classmethod
    def create(cls, name, unicode_version, validating_repertoire_name):
        metadata = Metadata()
        metadata.version = Version('1')
        metadata.set_unicode_version(unicode_version)
        lgr = LGR(name, metadata=metadata)
        lgr.unicode_database = unidb.manager.get_db_by_version(unicode_version)
        validating_repertoire = get_by_name(validating_repertoire_name) if validating_repertoire_name else None
        lgr_info = cls(name, lgr=lgr, validating_repertoire=validating_repertoire)
        return lgr_info

    @classmethod
    def _parse_lgr(cls, name, xml, validate):
        # Create parser - Assume xml is unicode data
        parser = XMLParser(six.BytesIO(xml.encode('utf-8')), name)

        # Do we need to validate the schema?
        if validate:
            validation_result = parser.validate_document(settings.LGR_RNG_FILE)
            if validation_result is not None:
                raise LGRValidationException(validation_result)

        # Some explanations: Parsing the document with an Unicode database takes
        # more time since there are some Unicode-related checks performed
        # (IDNA validity, script checking)
        # Doing these checks for each parsing of the LGR (ie. for each request)
        # is not really useful.
        # So we do the following:
        # - For the first import of the LGR ("validate_cp" is True),
        # do a full-fledged parsing, enabling all checks.
        # This will filter out IDNA-invalid codepoints, issue warnings
        # about out-of script codepoints, etc.
        # - Otherwise, meaning the LGR is already in the user's session,
        # we do not set the Unicode database for parsing. However, the database
        # is still set AFTER the parsing is done in order to validate
        # user's input (add codepoint, validation of LGR).

        # Do we need to validate against Unicode?
        if validate:
            # Retrieve Unicode version to set appropriate Unicode database
            unicode_version = parser.unicode_version()
            parser.unicode_database = unidb.manager.get_db_by_version(
                unicode_version)

        # Actually parse document
        lgr = parser.parse_document()

        # If we did not set the actual Unicode database, do it now
        if not validate:
            # Retrieve Unicode version to set appropriate Unicode database
            unicode_version = lgr.metadata.unicode_version
            lgr.unicode_database = unidb.manager.get_db_by_version(
                unicode_version)
        return lgr

    @classmethod
    def from_dict(cls, dct, lgr_loader_func=None, request=None):
        name = dct.get('name', '')
        set_labels_info = None
        if 'set_labels_info' in dct:
            set_labels_info = LabelInfo.from_dict(dct['set_labels_info'])
        lgr_set_dct = dct.get('lgr_set_dct', None)
        lgr_set = None
        if lgr_set_dct:
            lgr_set = []
            for lgr_dct in lgr_set_dct:
                lgr_set.append(cls.from_dict(lgr_dct,
                                             lgr_loader_func=lgr_loader_func,
                                             request=request))

        xml = dct['xml']
        if not isinstance(xml, six.text_type):
            xml = six.text_type(xml, 'utf-8')

        # Parse XML #
        # Replace old namespace by the new one for compatibility purpose with old LGR
        xml = xml.replace(OLD_LGR_NS, LGR_NS)

        if request is None:
            lgr = cls._parse_lgr(name, xml, dct.get('validate', False))
        else:
            lgr = cache.get(make_lgr_session_key(LGR_OBJECT_CACHE_KEY,
                                                 request,
                                                 name))
            if lgr is None:
                lgr = cls._parse_lgr(name, xml, dct.get('validate', False))
                cache.set(make_lgr_session_key(LGR_OBJECT_CACHE_KEY,
                                               request,
                                               name),
                          lgr,
                          LGR_CACHE_TIMEOUT)
            else:
                # Need to manually load unicode database because
                # it is stripped during serialization
                unicode_version = lgr.metadata.unicode_version
                lgr.unicode_database = unidb.manager.get_db_by_version(unicode_version)

        validating_repertoire = dct.get('validating_repertoire')
        val_lgr = lgr_loader_func(validating_repertoire) if (validating_repertoire and lgr_loader_func is not None) else None
        lgr_info = cls(name=name,
                       xml=xml,
                       lgr=lgr,
                       validating_repertoire=val_lgr,
                       lgr_set=lgr_set,
                       set_labels_info=set_labels_info)
        return lgr_info

    def to_dict(self, request=None):
        if not isinstance(self.xml, six.text_type):
            self.xml = six.text_type(self.xml, 'utf-8')

        dct = {
            'name': self.name,
            'xml': self.xml,
            'validating_repertoire': self.validating_repertoire.name if self.validating_repertoire else None,
            'lgr_set_dct': [l.to_dict(request) for l in self.lgr_set] if self.is_set else None,
            'is_set': self.is_set  # for index.html
        }
        if self.set_labels_info is not None:
            dct['set_labels_info'] = self.set_labels_info.to_dict()

        if request is not None:
            cache.set(make_lgr_session_key(LGR_OBJECT_CACHE_KEY,
                                           request,
                                           self.name),
                      self.lgr,
                      LGR_CACHE_TIMEOUT)

        return dct

    @property
    def is_set(self):
        return self.lgr_set is not None and len(self.lgr_set) > 1


class LabelInfo(object):

    def __init__(self, name, labels=None, data=None):
        self.name = name
        self.labels = labels
        self.data = data

    @classmethod
    def from_dict(cls, dct):
        return cls(dct['name'],
                   six.StringIO(base64.b64decode(dct['data']).decode('utf-8')),
                   dct['data'])

    @classmethod
    def from_form(cls, name, label_input):
        data = label_input.decode('utf-8')
        labels = six.StringIO(data)
        b64data = base64.b64encode(label_input).decode('utf-8')

        return cls(name, labels, b64data)

    @classmethod
    def from_list(cls, name, labels):
        data = '\n'.join(labels)
        labels = six.StringIO(data)
        b64data = base64.b64encode(data.encode('utf-8')).decode('utf-8')

        return cls(name, labels, b64data)

    def to_dict(self):
        return {
            'name': self.name,
            'data': self.data
        }


def session_list_lgr(request):
    """
    List the LGRs stored in session.

    :param request: Django request object
    :return: list of `LGRInfo` instances
    """
    known_lgrs = request.session.get(LGRS_SESSION_KEY, {})
    return sorted(known_lgrs.values(), key=lambda x: x['name'])


def session_open_lgr(request, lgr_id, lgr_xml,
                     validating_repertoire_name=None,
                     validate=False, from_set=False,
                     lgr_set=None, set_labels=None):
    """
    Parse the given LGR in XML format, and save it in session.

    :param request: Django request object
    :param lgr_id: a slug identifying the LGR
    :param lgr_xml: a string with the xml
    :param validating_repertoire_name: optional name of a validating repertoire
    :param validate: if True, ensure the XML is valid LGR XML
    :param from_set: Whether the LGR belongs to a set or not
    :param lgr_set: The list of LGRInfo in the set if this is a merged LGR from a set
    :return: `LGRInfo`
    """
    lgr_info = LGRInfo.from_dict(
        {
            'name': lgr_id,
            'xml': lgr_xml,
            'validating_repertoire': validating_repertoire_name,
            'validate': validate,
            'lgr_set_dct': [lgr.to_dict() for lgr in lgr_set] if lgr_set else None,
            'set_labels': set_labels
        },
        lgr_loader_func=partial(get_builtin_or_session_repertoire, request=request)
    )
    if not from_set:
        # do not save lgr in session, it will be kept in set
        session_save_lgr(request, lgr_info)
    else:
        lgr_info.update_xml()

    return lgr_info


def session_select_lgr(request, lgr_id, lgr_set_id=None):
    """
    Find the LGR identified by `lgr_id` in the session.
    Can also retrieve a root zone LGR.

    :param request: Django request object
    :param lgr_id: a slug identifying the LGR
    :param lgr_set_id: a slug identifying a LGR set if LGR is in a set
    :return: `LGRInfo`
    """
    known_lgrs = request.session.get(LGRS_SESSION_KEY, {})

    # handle RZ LGR selection
    if lgr_id not in known_lgrs and lgr_id in list_root_zones():
        return LGRInfo(lgr_id, lgr=get_by_name(lgr_id, with_unidb=True))

    if lgr_set_id:
        if lgr_set_id not in known_lgrs:
            raise Http404
        lgr_dct = known_lgrs[lgr_set_id]
    else:
        if lgr_id not in known_lgrs:
            raise Http404
        lgr_dct = known_lgrs[lgr_id]
        return LGRInfo.from_dict(lgr_dct,
                                 lgr_loader_func=partial(get_builtin_or_session_repertoire, request=request),
                                 request=request)

    if not lgr_dct.get('lgr_set_dct', None):
        raise Http404

    for lgr in lgr_dct.get('lgr_set_dct'):
        if lgr['name'] == lgr_id:
            return LGRInfo.from_dict(lgr,
                                     lgr_loader_func=partial(get_builtin_or_session_repertoire, request=request),
                                     request=request)
    raise Http404


def session_save_lgr(request, lgr_info, lgr_id=None):
    """
    Save the LGR object in session
    :param request: Django request object
    :param lgr_info: `LGRInfo` instance
    :param lgr_id: a slug identifying the LGR
    """
    lgr_id = lgr_id if lgr_id is not None else lgr_info.name
    lgr_info.update_xml()  # make sure we have updated XML before saving
    request.session.setdefault(LGRS_SESSION_KEY, {})[lgr_id] = lgr_info.to_dict(request)
    # mark session as modified because we are possibly only changing the content of a dict
    request.session.modified = True
    # As LGR has been modified, need to invalidate the template repertoire cache
    clean_repertoire_cache(request, lgr_id)


def session_get_storage(request):
    """
    Get the storage path for the session

    :param request: Django request object
    :return: the storage location
    """
    # get or create a key for storage in the session,
    try:
        storage_key = request.session['storage']
    except KeyError:
        # generate a random key
        storage_key = uuid4().hex
        request.session['storage'] = storage_key
    # the storage may still not be created here but now it has a path for
    #  this session
    return os.path.join(settings.TOOLS_OUTPUT_STORAGE_LOCATION,
                        storage_key)


def session_list_storage(request):
    """
    List files in the storage

    :param request: Django request object
    :return: the list of files in storage
    """
    storage = FileSystemStorage(location=session_get_storage(request))
    try:
        files = storage.listdir('.')
    except OSError:
        return []

    return sorted(files[1], reverse=True)


def get_builtin_or_session_repertoire(repertoire_id, request):
    """
    Load the given LGR from the set of built-in repertoires, or if not found, load it from the user's session

    :param repertoire_id: a slug identifying the LGR
    :param request: Django request object
    :return: `LGR` instance
    """
    try:
        return get_by_name(repertoire_id)
    except IOError as e:
        if e.errno == errno.ENOENT:  # not found
            # try session
            session_lgr_info = session_select_lgr(request, repertoire_id)
            return session_lgr_info.lgr
        else:
            raise  # don't deal with any other errors