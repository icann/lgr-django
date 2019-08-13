# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from django.shortcuts import render, redirect
from lgr_editor.api import session_list_lgr, session_list_storage
from lgr_editor.utils import list_built_in_lgr


ADVANCED_INTERFACE_SESSION_KEY = 'advanced'


def index(request):
    if 'advanced' in request.GET:
        # we explicitly clicked the advanced mode button
        request.session[ADVANCED_INTERFACE_SESSION_KEY] = True

    if not request.session.get(ADVANCED_INTERFACE_SESSION_KEY, False):
        return redirect('lgr_basic_mode')

    xml_files = list_built_in_lgr()
    ctx = {
        'lgr_xml': xml_files,
        'lgrs': session_list_lgr(request),
        'lgr_id': '',
        'storage': session_list_storage(request),
    }
    return render(request, 'index.html', context=ctx)
