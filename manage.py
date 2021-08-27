#!/usr/bin/env python
import os
import sys


def import_pretty_traceback_dev_dep():
    try:
        import pretty_traceback
        pretty_traceback.install()
    except ImportError:
        pass  # no need to fail because of missing dev dependency


if __name__ == "__main__":
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "lgr_web.settings")

    import_pretty_traceback_dev_dep()

    # add "src" dir to sys.path
    src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), 'src'))
    sys.path.insert(0, src_path)
    # add it to env too so that it survives forks (only if no PYTHONPATH set)
    os.environ.setdefault("PYTHONPATH", src_path)

    from django.core.management import execute_from_command_line

    execute_from_command_line(sys.argv)
