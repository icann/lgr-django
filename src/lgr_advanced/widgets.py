#! /bin/env python
# -*- coding: utf-8 -*-
"""
widgets.py
"""
from django.forms import Select


class DataSelectWidget(Select):
    """
    Add data to select widget options
    Data is a dict with key option value containing a dict of data name with data value
    """
    allow_multiple_selected = False

    def __init__(self, *args, **kwargs):
        self.data = kwargs.pop('data', {})
        super(DataSelectWidget, self).__init__(*args, **kwargs)

    def create_option(self, name, value, label, selected, index, subindex=None, attrs=None):
        """
        Yield all "subwidgets" of this widget. Used to enable iterating
        options from a BoundField for choice widgets.
        """
        option = super(DataSelectWidget, self).create_option(name, value, label, selected, index, subindex, attrs)
        for key, val in self.data.get(value, {}).items():
            # attrs won't be displayed if val is False and will be displayed without argument if val is True
            option['attrs']['data-{}'.format(key)] = val

        return option