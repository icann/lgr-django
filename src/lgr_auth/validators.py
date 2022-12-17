# -*- coding: utf-8 -*-
import re

from django.core import validators


class UAEmailValidator(validators.EmailValidator):
    # same Email Validator class with unicode characters instead of a-z0-9
    # this is a lazy validation as we should check for IDNA 2008 compliance but email is only used as login
    user_regex = validators._lazy_re_compile(
        r"(^[-!#$%&'*+/=?^`{}|~\w]+(\.[-!#$%&'*+/=?^`{}|~\w]+)*\Z"  # dot-atom
        r'|^"([\001-\010\013\014\016-\037!#-\[\]-\177]|\\[\001-\011\013\014\016-\177])*"\Z)',  # quoted-string
        re.IGNORECASE)


ua_validate_email = UAEmailValidator()
