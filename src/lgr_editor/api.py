# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from functools import partial
import logging
from StringIO import StringIO
import errno
import os
from uuid import uuid4

from django.http import Http404
from django.utils import six
from django.utils.text import slugify
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from lgr.core import LGR
from lgr.metadata import Metadata, Version
from lgr.parser.xml_serializer import serialize_lgr_xml
from lgr.parser.xml_parser import XMLParser, LGR_NS
from lgr.tools.merge_set import merge_lgr_set
from lgr.tools.utils import prepare_merged_lgr
from lgr_web.settings import TOOLS_OUTPUT_STORAGE_LOCATION

from .exceptions import LGRValidationException
from .repertoires import get_by_name
from . import unidb


OLD_LGR_NS = 'http://www.iana.org/lgr/0.1'
LGRS_SESSION_KEY = 'lgr'

logger = logging.getLogger(__name__)


class LGRInfo(object):
    def __init__(self, name, lgr=None, xml=None, validating_repertoire=None, lgr_set=None, set_labels=None):
        self.name = name
        self.lgr = lgr
        self.xml = xml
        self.validating_repertoire = validating_repertoire
        self.lgr_set = lgr_set
        self.set_labels = set_labels

    def update_xml(self, pretty_print=False):
        # if something was changed in `lgr`, calling this will re-generate the xml
        self.xml = serialize_lgr_xml(self.lgr, pretty_print=pretty_print)

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
    def from_dict(cls, dct, lgr_loader_func):
        name = dct.get('name', '')
        xml = dct['xml']
        validate = dct.get('validate', False)
        set_labels = dct.get('set_labels', None)
        lgr_set_dct = dct.get('lgr_set_dct', None)
        lgr_set = None
        if lgr_set_dct:
            lgr_set = []
            for lgr_dct in lgr_set_dct:
                lgr_set.append(cls.from_dict(lgr_dct, lgr_loader_func=lgr_loader_func))

        # check if xml is of unicode type
        if isinstance(xml, six.text_type):
            # convert to a str (bytes in PY3) to be consistent
            xml = xml.encode('utf-8')

        # Parse XML #
        # Replace old namespace by the new one for compatibility purpose with
        # old LGR
        xml = unicode(xml, 'utf-8').replace(OLD_LGR_NS, LGR_NS)
        # Create parser
        parser = XMLParser(StringIO(xml.encode('utf-8')), name)

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
            parser.unicode_database = unidb.manager.get_db_by_version(unicode_version)

        # Actually parse document
        lgr = parser.parse_document()

        # If we did not set the actual Unicode database, do it now
        if not validate:
            # Retrieve Unicode version to set appropriate Unicode database
            unicode_version = lgr.metadata.unicode_version
            lgr.unicode_database = unidb.manager.get_db_by_version(unicode_version)

        validating_repertoire = dct.get('validating_repertoire')
        val_lgr = lgr_loader_func(validating_repertoire) if validating_repertoire else None
        lgr_info = cls(name=name,
                       xml=xml,
                       lgr=lgr,
                       validating_repertoire=val_lgr,
                       lgr_set=lgr_set,
                       set_labels=set_labels)
        return lgr_info

    def to_dict(self):
        return {
            'name': self.name,
            'xml': self.xml,
            'validating_repertoire': self.validating_repertoire.name if self.validating_repertoire else None,
            'lgr_set_dct': map(lambda x: x.to_dict(), self.lgr_set) if self.is_set else None,
            'set_labels': self.set_labels,
            'is_set': self.is_set  # for index.html
        }

    @property
    def is_set(self):
        return self.lgr_set is not None and len(self.lgr_set) > 1


def get_builtin_or_session_repertoire(repertoire_id, request):
    """
    Load the given LGR from the set of built-in repertoires, or if not found, load it from the user's session

    :param repertoire_id: a slug identifying the LGR
    :param request: Django request object
    :return: `LGR` isntance
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


def session_list_lgr(request):
    """
    List the LGRs stored in session.

    :param request: Django request object
    :return: list of `LGRInfo` instances
    """
    known_lgrs = request.session.get(LGRS_SESSION_KEY, {})
    return sorted(known_lgrs.values(), key=lambda x: x['name'])


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
    :param set_labels: The list of labels in the LGR set
    :return: `LGRInfo`
    """
    lgr_info = LGRInfo.from_dict(
        {
            'name': lgr_id,
            'xml': lgr_xml,
            'validating_repertoire': validating_repertoire_name,
            'validate': validate,
            'lgr_set_dct': map(lambda x: x.to_dict(), lgr_set) if lgr_set else None,
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

    :param request: Django request object
    :param lgr_id: a slug identifying the LGR
    :param lgr_set_id: a slug identifying a LGR set if LGR is in a set
    :return: `LGRInfo`
    """
    known_lgrs = request.session.get(LGRS_SESSION_KEY, {})

    if lgr_set_id:
        if lgr_set_id not in known_lgrs:
            raise Http404
        lgr_dct = known_lgrs[lgr_set_id]
    else:
        if lgr_id not in known_lgrs:
            raise Http404
        lgr_dct = known_lgrs[lgr_id]
        return LGRInfo.from_dict(lgr_dct,
                                 lgr_loader_func=partial(get_builtin_or_session_repertoire, request=request))

    if not lgr_dct.get('lgr_set_dct', None):
        raise Http404

    for lgr in lgr_dct.get('lgr_set_dct'):
        if lgr['name'] == lgr_id:
            return LGRInfo.from_dict(lgr,
                                     lgr_loader_func=partial(get_builtin_or_session_repertoire, request=request))
    raise Http404


def session_save_lgr(request, lgr_info, lgr_id=None, update_xml=True):
    """
    Save the LGR object in session
    :param request: Django request object
    :param lgr_info: `LGRInfo` instance
    :param lgr_id: a slug identifying the LGR
    """
    lgr_id = lgr_id if lgr_id is not None else lgr_info.name
    if update_xml:
        lgr_info.update_xml()  # make sure we have updated XML before saving
    request.session.setdefault(LGRS_SESSION_KEY, {})[lgr_id] = lgr_info.to_dict()
    # mark session as modified because we are possibly only changing the content of a dict
    request.session.modified = True


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


def session_merge_set(request, lgr_set, lgr_set_name, set_labels_file):
    """
    Merge some LGR to build a set
    :param request: Django request object
    :param lgr_set: The list of LGRs id in the set
    :param lgr_set_name: The name of the LGR set
    :param set_labels_file: The file containing labels in the LGR set
    :return: The LGR set merge id
    """
    merged_lgr = merge_lgr_set(map(lambda x: x.lgr, lgr_set), lgr_set_name)
    merged_id = slugify(merged_lgr.name)

    _, merged_lgr_xml, set_labels = prepare_merged_lgr(merged_lgr, merged_id,
                                                       set_labels_file.read().decode('utf-8'),
                                                       unidb, validate_labels=True, do_raise=True)

    session_open_lgr(request, merged_id, merged_lgr_xml,
                     validating_repertoire_name=None,
                     validate=True, lgr_set=lgr_set, set_labels=list(set_labels))
    return merged_id


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
    return os.path.join(TOOLS_OUTPUT_STORAGE_LOCATION,
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

    return sorted(files[1])


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
