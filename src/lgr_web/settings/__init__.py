#TODO: Have a better way to handle the import of settings when using
# something else than local
try:
    from .test import *
except ImportError:
    from .local import *

if SECRET_KEY == 'PLEASE GENERATE ONE':
    print("default SECRET_KEY must be replaced")
    import sys
    sys.exit(99)
