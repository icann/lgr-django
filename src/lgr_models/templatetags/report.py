# -*- coding: utf-8 -*-
from datetime import datetime

from django import template
from django.template.defaultfilters import pluralize
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _

from lgr_models.models.report import LGRReport
from lgr_web.config import lgr_settings

register = template.Library()


@register.filter
def display_expiration(report: LGRReport):
    if not report:
        return ''
    created_since = datetime.now() - report.created_at.replace(tzinfo=None)
    expiration_in = lgr_settings.report_expiration_delay - created_since.days
    label = 'info'
    if expiration_in < 5:
        label = 'warning'
    if expiration_in < 2:
        label = 'danger'
    expiration = f"{_('Expires in')} <i class=\"label label-{label}\">{expiration_in} " \
                 f"{_('day')}{pluralize(expiration_in)}</i>"
    return mark_safe(expiration)


@register.simple_tag
def expiration_warning():
    return f"{_('These files would be cleaned up after')} {lgr_settings.report_expiration_delay} " \
           f"{_('day')}{pluralize(lgr_settings.report_expiration_delay)}"
