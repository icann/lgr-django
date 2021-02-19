#! /bin/env python
# -*- coding: utf-8 -*-
"""
api - 
"""
import logging

from django.http import HttpResponse

logger = logging.getLogger('api')


def _prepare_validation_html_file_response(name, out):
    response = HttpResponse(content_type='text/html')
    cd = f'attachment; filename="{name}-validation-results.html"'
    response['Content-Disposition'] = cd

    response.write(out)

    return response
