from typing import List

from django import template
from django.db.models import QuerySet

from lgr_advanced.models import LgrModel

register = template.Library()


@register.filter
def sort_by_is_set(lgrs: QuerySet[LgrModel]) -> List[LgrModel]:
    for instance in lgrs:
        instance.group_key = instance.is_set()

    return sorted(lgrs, key=lambda lgr: lgr.group_key)
