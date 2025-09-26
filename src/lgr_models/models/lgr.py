# -*- coding: utf-8 -*-
import hashlib
import os
from ast import literal_eval
from io import BytesIO

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import PermissionDenied
from django.core.files import File
from django.db import models
from django.urls import reverse
from django.utils.encoding import force_bytes
from lgr.core import LGR
from lgr.parser.xml_parser import LGR_NS, XMLParser
from lgr.parser.xml_serializer import serialize_lgr_xml
from lgr.utils import tag_to_language_script

from lgr_auth.models import LgrUser
from lgr_models.exceptions import LGRUnsupportedUnicodeVersionException, LGRValidationException
from lgr_models.storage import LGROverrideStorage
from lgr_utils import unidb
from lgr_utils.utils import LGR_CACHE_KEY_PREFIX

OLD_LGR_NS = 'http://www.iana.org/lgr/0.1'


def get_upload_path(instance, filename):
    base_path = 'lgr'
    # need to test on object_name because instance may not be a real object instance if called in a migration
    if instance._meta.object_name == 'RzLgr':
        return os.path.join(base_path, 'rz_lgr', filename)
    if instance._meta.object_name == 'RefLgr':
        return os.path.join(base_path, 'reference_lgr', filename)
    if instance._meta.object_name == 'RefLgrMember':
        return os.path.join(base_path, 'reference_lgr', instance.common.name, filename)
    if instance._meta.object_name == 'RzLgrMember':
        return os.path.join(base_path, 'rz_lgr', instance.common.name, filename)
    if instance._meta.object_name == 'MSR':
        return os.path.join(base_path, 'msr', filename)
    if instance._meta.object_name == 'IDNARepertoire':
        return os.path.join(base_path, 'idna', filename)

    # if you need to use other LgrBaseModel in migration, this won't work as historical models don't include method.
    # See https://docs.djangoproject.com/en/5.2/topics/migrations/#historical-models
    # If you need this in a migration, define the method in the migration and set it to the historical model.
    return os.path.join('lgr', instance.upload_path(instance, filename))


class LgrBaseModel(models.Model):
    lgr_parser = XMLParser
    lgr_cache_key = 'lgr-obj'
    cache_timeout = 3600
    force_parse = True
    allow_invalid_property = False

    file = models.FileField(upload_to=get_upload_path)
    name = models.CharField(max_length=128)
    owner = models.ForeignKey(to=LgrUser, on_delete=models.CASCADE, related_name='+')

    class Meta:
        ordering = ['name']
        abstract = True

    def __str__(self):
        return self.name

    @classmethod
    def get_object(cls, user, pk):
        query_kwargs = {'pk': pk}
        if not cls._meta.get_field('owner').null:
            if user.is_anonymous:
                raise PermissionDenied
            # only include owner in model where it is mandatory, meaning objects are private
            query_kwargs['owner'] = user
        return cls.objects.get(**query_kwargs)

    @property
    def filename(self):
        return os.path.basename(self.file.name)

    @property
    def model_name(self):
        return self.__class__.__name__

    def html_url(self):
        return reverse('lgr_render', kwargs={'model': self.model_name, 'lgr_pk': self.pk})

    def display_url(self):
        return reverse('lgr_display', kwargs={'model': self.model_name, 'lgr_pk': self.pk})

    def download_url(self):
        return reverse('lgr_download', kwargs={'model': self.model_name, 'lgr_pk': self.pk})

    @classmethod
    def from_tuple(cls, model_pk_tuple, user=None):
        """
        Get a LGR object from a tuple containing the model_name and pk
        """
        from lgr_models.utils import get_model_from_name

        if not model_pk_tuple:
            return

        if not isinstance(model_pk_tuple, tuple):
            model_pk_tuple = literal_eval(model_pk_tuple)
        model_name, pk = model_pk_tuple
        return get_model_from_name(model_name).get_object(user, pk)

    def to_tuple(self):
        return self._meta.label, self.pk

    @staticmethod
    def upload_path(instance, filename):
        return os.path.join(f'user_{instance.owner.id}', filename)

    def delete(self, *args, **kwargs):
        cache.delete(self._cache_key(self.lgr_cache_key))
        return super().delete(*args, **kwargs)

    def _cache_key(self, key):

        key = f"{key}:{self._meta.label}:{self.pk}"
        args = hashlib.md5(force_bytes(key))
        return "{}.{}".format(LGR_CACHE_KEY_PREFIX, args.hexdigest())

    def _to_cache(self, lgr: LGR):
        if not self._meta.pk:
            return
        cache.set(self._cache_key(self.lgr_cache_key), lgr, self.cache_timeout)

    def _from_cache(self) -> LGR:
        if not self._meta.pk:
            return None
        return cache.get(self._cache_key(self.lgr_cache_key))

    def to_lgr(self, validate=False, with_unidb=True, expand_ranges=False) -> LGR:
        from lgr_utils import unidb

        lgr = self._from_cache()
        if lgr is None:
            lgr = self._parse(validate, with_unidb=with_unidb)
            self._to_cache(lgr)
        else:
            # Need to manually load unicode database because it is stripped during serialization
            unicode_version = lgr.metadata.unicode_version
            lgr.unicode_database = unidb.manager.get_db_by_version(unicode_version)
        if expand_ranges:
            lgr.expand_ranges()
        return lgr

    @classmethod
    def _parse_lgr_xml(cls, lgr, validate=False):
        data = serialize_lgr_xml(lgr, pretty_print=True)
        if validate:
            parser = cls.lgr_parser(BytesIO(data), lgr.name)
            validation_result = parser.validate_document(settings.LGR_RNG_FILE)
            if validation_result is not None:
                raise LGRValidationException(validation_result)
        return data

    @classmethod
    def from_lgr(cls, owner, lgr, name=None, validate=False, **kwargs):
        name = name or lgr.name
        if name.endswith('.xml') or name.endswith('.txt'):
            name = os.path.splitext(name)[0]
        data = cls._parse_lgr_xml(lgr, validate=validate)

        file = File(BytesIO(data), name=f'{name}.xml')
        lgr_object = cls.objects.create(owner=owner,
                                        name=name,
                                        file=file,
                                        **kwargs)
        lgr_object._to_cache(lgr)
        return lgr_object

    def _parse(self, validate, with_unidb):
        self.file.seek(0)
        data = self.file.read()
        return self.parse(self.name, data, validate, with_unidb=with_unidb)

    @classmethod
    def parse(cls, name, data, validate, with_unidb=False):
        data = data.decode('utf-8').replace(OLD_LGR_NS, LGR_NS)

        # Create parser - Assume content is unicode data
        parser = cls.lgr_parser(BytesIO(data.encode('utf-8')), name, force=cls.force_parse,
                                allow_invalid_property=cls.allow_invalid_property)

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
        if validate and with_unidb:
            # Retrieve Unicode version to set appropriate Unicode database
            try:
                parser.unicode_database = unidb.manager.get_db_by_version(settings.SUPPORTED_UNICODE_VERSION)
            except KeyError as e:
                raise LGRUnsupportedUnicodeVersionException(e)
        # Actually parse document
        lgr = parser.parse_document()

        # If we did not set the actual Unicode database, do it now
        if not validate and with_unidb:
            # Retrieve Unicode version to set appropriate Unicode database
            try:
                lgr.unicode_database = unidb.manager.get_db_by_version(settings.SUPPORTED_UNICODE_VERSION)
            except KeyError as e:
                raise LGRUnsupportedUnicodeVersionException(e)
        return lgr

    def is_set(self):
        return False


class TemporaryLgrBase(LgrBaseModel):
    """Allow to use the parsing methods of LgrBaseModel"""
    class Meta:
        managed = False


class ManagedLgrBase(LgrBaseModel):
    # make name unique and owner nullable
    name = models.CharField(max_length=128, unique=True)
    owner = models.ForeignKey(to=LgrUser, blank=True, null=True, on_delete=models.CASCADE, related_name='+')

    class Meta:
        ordering = ['name']
        abstract = True


class ManagedLgrBaseMember(LgrBaseModel):
    # override existing files
    file = models.FileField(upload_to=get_upload_path, storage=LGROverrideStorage)
    # make owner nullable
    owner = models.ForeignKey(to=LgrUser, blank=True, null=True, on_delete=models.CASCADE, related_name='+')

    class Meta:
        ordering = ['name']
        abstract = True
        unique_together = ('name', 'common',)


class RzLgr(ManagedLgrBase):
    active = models.BooleanField(default=False)


class RefLgr(ManagedLgrBase):
    active = models.BooleanField(default=False)


class RefLgrMember(ManagedLgrBaseMember):
    common = models.ForeignKey(to=RefLgr, on_delete=models.CASCADE, related_name='repository')
    language_script = models.CharField(max_length=32)
    language = models.CharField(max_length=8, blank=True)
    script = models.CharField(max_length=8, blank=True)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        self.language, self.script = tag_to_language_script(self.language_script)
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


class RzLgrMember(ManagedLgrBaseMember):
    common = models.ForeignKey(to=RzLgr, on_delete=models.CASCADE, related_name='repository')
    language = models.CharField(max_length=8)
    script = models.CharField(max_length=8)

    def save(self, force_insert=False, force_update=False, using=None, update_fields=None):
        lgr_parser = XMLParser(self.file)
        self.file.seek(0)
        lgr = lgr_parser.parse_document()
        try:
            self.language, self.script = tag_to_language_script(lgr.metadata.languages[0])
        except:
            pass
        super().save(force_insert=force_insert, force_update=force_update, using=using, update_fields=update_fields)


class MSR(ManagedLgrBase):
    active = models.BooleanField(default=False)


class IDNARepertoire(ManagedLgrBase):
    active = models.BooleanField(default=False)
