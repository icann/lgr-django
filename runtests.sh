#!/bin/sh

# Small helper to execute all tests.
# TODO: replace by something more pythonic...

export PYTHONPATH=$(dirname $0)

echo Run doctests
python2 -m doctest src/lgr_editor/utils.py
