"""
signal.py - Signal used to handle folder deletion when a file is removed with django-cleanup
"""
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


def delete_parent_folder(sender, **kwargs):
    try:
        os.rmdir(os.path.dirname(Path(kwargs['file'].storage.location) / kwargs['file_name']))
    except OSError:
        # The directory is not empty
        pass
    except (Exception, BaseException) as e:
        logger.warning(f'Could not delete folder: {e}')
        pass
