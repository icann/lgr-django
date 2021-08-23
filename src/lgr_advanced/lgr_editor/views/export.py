#! /bin/env python
# -*- coding: utf-8 -*-
"""
export - 
"""
import logging

from django.http import HttpResponse
from django.views import View

from lgr_advanced.lgr_editor.views.mixins import LGRHandlingBaseMixin

logger = logging.getLogger(__name__)


class LGRRenderXMLView(LGRHandlingBaseMixin, View):
    """
    Display the XML of the LGR.

    Display the content of the LGR as XML. Optionally,
    set content-disposition to open download box on browser.
    """

    def setup(self, request, *args, **kwargs):
        super().setup(request, *args, **kwargs)
        self.force_download = self.kwargs.get('force_download', False)

    def get(self, request, *args, **kwargs):
        resp = HttpResponse(self.lgr_object.file, content_type='text/xml', charset='UTF-8')
        if self.force_download:
            resp['Content-disposition'] = f'attachment; filename={self.lgr_object.filename}'
        return resp
