import logging

from django.conf import settings
from django.core.files.storage import FileSystemStorage

logger = logging.getLogger(__name__)


class LGROverrideStorage(FileSystemStorage):
    def __init__(self, *args, **kwargs):
        if settings.STORAGES['default']['BACKEND'] != 'django.core.files.storage.FileSystemStorage':
            raise RuntimeError('Default storage has changed, please change LGROverrideStorage inheritance')
        super().__init__(*args, **kwargs)

    def get_available_name(self, name, max_length=None):
        if self.exists(name):
            self.delete(name)
        return super().get_available_name(name, max_length)
