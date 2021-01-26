# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import os
import time

from django.core.management.base import BaseCommand
from django.core import management
from django.contrib.sessions.models import Session
from django.conf import settings


class Command(BaseCommand):
    help = (
        "Can be run as a cronjob or directly to clean the users' storage and "
        "sessions."
        "This command will call clearsessions as well."
    )

    def handle(self, **options):
        sessions = Session.objects.filter()

        if 2 * settings.STORAGE_DURATION > settings.SESSION_COOKIE_AGE:
            self.stderr.write("Warning: Your storage duration should be "
                              "less than half the session duration "
                              "or you may get uncleaned files or folders.")

        for session in sessions:
            session_data = session.get_decoded()
            if 'storage' not in session_data:
                continue
            storage_path = os.path.join(settings.TOOLS_OUTPUT_STORAGE_LOCATION,
                                        session_data['storage'])
            if not os.path.exists(storage_path):
                continue

            # remove empty folders
            # To avoid removing folders that may just have been created or
            # accessed, check last modification date and add a margin.
            if os.path.getmtime(storage_path) + settings.STORAGE_DURATION < time.time():
                try:
                    os.rmdir(storage_path)
                except OSError:
                    # not empty
                    pass
                else:
                    self.stdout.write("Remove folder '{}'".format(storage_path))
                    continue

            # remove files that are too old
            for out_fname in os.listdir(storage_path):
                out_fpath = os.path.join(storage_path, out_fname)
                if os.path.getctime(out_fpath) + settings.STORAGE_DURATION < time.time():
                    self.stdout.write("Remove file '{}'".format(out_fname))
                    os.remove(out_fpath)

        management.call_command('clearsessions')
