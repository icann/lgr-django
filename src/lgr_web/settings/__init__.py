from __future__ import print_function
from .local import *

if SECRET_KEY == 'PLEASE GENERATE ONE':
    print("default SECRET_KEY must be replaced")
    import sys
    sys.exit(99)
