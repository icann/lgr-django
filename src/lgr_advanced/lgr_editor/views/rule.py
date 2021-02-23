#! /bin/env python
# -*- coding: utf-8 -*-
"""
rule - 
"""
import logging

from django.http import JsonResponse
from django.utils.encoding import force_text
from django.utils.translation import ugettext_lazy as _
from django.views import View
from django.views.generic import TemplateView
from lxml.etree import XMLSyntaxError

from lgr.exceptions import LGRException
from lgr.parser.xml_parser import LGR_NS
from lgr_advanced.api import LGRInfo
from lgr_advanced.lgr_editor.views.mixins import LGRHandlingBaseMixin, LGREditMixin
from lgr_advanced.lgr_exceptions import lgr_exception_to_text

logger = logging.getLogger(__name__)

NEW_ELEMENT_NAME_PARAM = '__new__'

# In `LGR_SKEL` below, the content preceding `{xml}` should be on a single line, so that the line
# number reported in error messages can be more consistent.
LGR_SKEL = '''<lgr xmlns="{ns}"><meta /><rules>
{xml}
</rules></lgr>'''
CLASS_SKEL = '''<class name="{}" comment="EXAMPLE - last letter of the English alphabet">007A</class>'''
RULE_SKEL = '''<rule name="{}" comment="EXAMPLE - must be the start of label">
  <start/>
</rule>'''
ACTION_SKEL = '''<action disp="blocked" comment="EXAMPLE - disallowed"/>'''


class ListRuleSimpleView(LGRHandlingBaseMixin, TemplateView):
    """
    Display a verbatim view of the <rules> section.
    """
    template_name = 'lgr_editor/rules.html'

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        rules = {
            'classes': '\n\n'.join(self.lgr_info.lgr.classes_xml),
            'rules': '\n\n'.join(self.lgr_info.lgr.rules_xml),
            'actions': '\n\n'.join(self.lgr_info.lgr.actions_xml),
        }
        ctx.update({
            'rules': rules,
            'lgr': self.lgr_info.lgr,
            'lgr_id': self.lgr_id,
            'is_set': self.lgr_info.is_set or self.lgr_set_id is not None
        })
        if self.lgr_set_id:
            lgr_set_info = self.session.select_lgr(self.lgr_set_id)
            ctx['lgr_set'] = lgr_set_info.lgr
            ctx['lgr_set_id'] = self.lgr_set_id

        return ctx


class ListRuleView(LGRHandlingBaseMixin, TemplateView):
    """
    Edit rules
    """
    template_name = 'lgr_editor/rules_edit.html'

    def get(self, request, *args, **kwargs):
        # set
        if self.lgr_info.is_set or self.lgr_set_id is not None:
            return ListRuleSimpleView.as_view()(request, *args, **kwargs)

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)

        lgr = self.lgr_info.lgr
        rules = {
            'classes': [{'name': cls_name, 'content': cls_xml} for cls_name, cls_xml in
                        zip(lgr.classes, lgr.classes_xml)],
            'rules': [{'name': rule_name, 'content': rule_xml} for rule_name, rule_xml in
                      zip(lgr.rules, lgr.rules_xml)],
            'actions': [{'name': action_idx, 'content': action_xml} for action_idx, action_xml in
                        enumerate(lgr.actions_xml)],
        }

        # try to suggest a non-clashing class name, but a clash should not be catastrophic
        for i in range(20):
            new_class_name = 'untitled-class-{}'.format(i)
            if new_class_name not in self.lgr_info.lgr.classes_lookup:
                break

        for i in range(20):
            new_rule_name = 'untitled-rule-{}'.format(i)
            if new_rule_name not in self.lgr_info.lgr.rules_lookup:
                break

        ctx.update({
            'rules': rules,
            'class_skeleton': CLASS_SKEL.format(new_class_name),
            'rule_skeleton': RULE_SKEL.format(new_rule_name),
            'action_skeleton': ACTION_SKEL,
            'lgr': self.lgr_info.lgr,
            'lgr_id': self.lgr_id,
            'NEW_ELEMENT_NAME_PARAM': NEW_ELEMENT_NAME_PARAM,
            'is_set': False
        })

        return ctx


# TODO - warn if the LGR already has duplicate classes or rules, we cannot reliably work on them
# TODO - prevent class or rule from being deleted if it is being referenced
# TODO - convert functional views into into CBV


def _json_response(success, error_msg=None):
    rv = {'success': success}
    if error_msg:
        rv['message'] = force_text(error_msg)
    return JsonResponse(rv, charset='UTF-8')


class RuleEditAjaxView(LGREditMixin, View):

    class RuleEditException(BaseException):

        def __init__(self, msg):
            self.message = msg

    def process_request(self, delete_action, body):
        raise NotImplementedError

    def post(self, request, *args, **kwargs):
        delete_action = request.POST.get('delete')
        body = request.POST.get('body')

        try:
            msg = self.process_request(delete_action, body)
        except RuleEditAjaxView.RuleEditException as e:
            return _json_response(False, e.message)

        try:
            self.session.save_lgr(self.lgr_info)
        except LGRException as e:
            return _json_response(False, lgr_exception_to_text(e))
        except XMLSyntaxError as e:
            return _json_response(False, _('Encountered XML syntax error: %s (line number may be wrong, '
                                           'try subtracting one from the reported line number)') % (e,))
        except Exception:
            return _json_response(False, _('Your XML is not valid'))
        return _json_response(True, msg)


def _del_class(lgr, clsname):
    del lgr.classes_lookup[clsname]
    i = lgr.classes.index(clsname)
    del lgr.classes[i]
    del lgr.classes_xml[i]


def _update_class(lgr, clsname, cls, body):
    if clsname in lgr.classes_lookup:
        del lgr.classes_lookup[clsname]  # `clsname` is the existing class name, `cls.name` is new (could be different)
        lgr.classes_lookup[cls.name] = cls
        i = lgr.classes.index(clsname)
        lgr.classes[i] = clsname
        lgr.classes_xml[i] = body
    else:
        lgr.add_class(cls)
        lgr.classes_xml.append(body)


def _parse_class(xml):
    lgr_xml = LGR_SKEL.format(ns=LGR_NS, xml=xml).encode('utf-8')
    lgr_info = LGRInfo.from_dict(
        {
            'xml': lgr_xml,
            'validate': False,
        },
        lgr_loader_func=None
    )
    if lgr_info.lgr.classes_lookup:
        return list(lgr_info.lgr.classes_lookup.values())[0]
    else:
        return None


class RuleEditClassAjaxView(RuleEditAjaxView):
    def process_request(self, delete_action, body):
        if not delete_action and not body:
            raise self.RuleEditException(_('No body specified'))

        lgr = self.lgr_info.lgr

        clsname = self.kwargs['clsname']
        if clsname not in lgr.classes_lookup and clsname != NEW_ELEMENT_NAME_PARAM:
            raise self.RuleEditException(_('Class "%s" does not exist') % clsname)

        if delete_action:
            _del_class(lgr, clsname)
            msg = _('Class "%s" deleted.') % clsname
        else:
            try:
                cls = _parse_class(body)
                if not cls:
                    raise self.RuleEditException(_('No class element found'))
                if cls.name is None:
                    raise self.RuleEditException(_('Name attribute must be present'))
            except LGRException as e:
                raise self.RuleEditException(lgr_exception_to_text(e))
            except XMLSyntaxError as e:
                raise self.RuleEditException(_('Encountered XML syntax error: %s (line number may be wrong, '
                                               'try subtracting one from the reported line number)') % (e,))
            except Exception:
                raise self.RuleEditException(_('Your XML is not valid'))

            if clsname != cls.name:
                # user has renamed the class, check that there is no dupe
                if cls.name in lgr.classes_lookup:
                    raise self.RuleEditException(_('Class "%s" already exists') % cls.name)
            _update_class(lgr, clsname, cls, body)
            msg = _('Class "%s" saved.') % cls.name

        return msg


def _del_rule(lgr, rule_name):
    del lgr.rules_lookup[rule_name]
    i = lgr.rules.index(rule_name)
    del lgr.rules[i]
    del lgr.rules_xml[i]


def _update_rule(lgr, rule_name, rule, body):
    if rule_name in lgr.rules_lookup:
        del lgr.rules_lookup[
            rule_name]  # `rule_name` is the existing rule name, `rule.name` is new (could be different)
        lgr.rules_lookup[rule.name] = rule
        i = lgr.rules.index(rule_name)
        lgr.rules[i] = rule_name
        lgr.rules_xml[i] = body
    else:
        lgr.add_rule(rule)
        lgr.rules_xml.append(body)


def _parse_rule(xml):
    lgr_xml = LGR_SKEL.format(ns=LGR_NS, xml=xml).encode('utf-8')
    lgr_info = LGRInfo.from_dict(
        {
            'xml': lgr_xml,
            'validate': False
        },
        lgr_loader_func=None
    )
    if lgr_info.lgr.rules_lookup:
        return list(lgr_info.lgr.rules_lookup.values())[0]
    else:
        return None


class RuleEditRuleAjaxView(RuleEditAjaxView):
    def process_request(self, delete_action, body):
        if not delete_action and not body:
            raise self.RuleEditException(_('No body specified'))

        lgr = self.lgr_info.lgr

        rulename = self.kwargs['rulename']
        if rulename not in lgr.rules_lookup and rulename != NEW_ELEMENT_NAME_PARAM:
            raise self.RuleEditException(_('Rule "%s" does not exist') % rulename)

        if delete_action:
            _del_rule(lgr, rulename)
            msg = _('Rule "%s" deleted.') % rulename
        else:
            try:
                rule = _parse_rule(body)
                if not rule:
                    raise self.RuleEditException(_('No rule element found'))
                if rule.name is None:
                    raise self.RuleEditException(_('Name attribute must be present'))

                if rulename != rule.name:
                    # user has renamed the rule, check that there is no dupe
                    if rule.name in lgr.rules_lookup:
                        raise self.RuleEditException(_('Rule "%s" already exists') % rule.name)

                _update_rule(lgr, rulename, rule, body)

                self.lgr_info.update_xml(validate=True)
            except LGRException as e:
                raise self.RuleEditException(lgr_exception_to_text(e))
            except XMLSyntaxError as e:
                raise self.RuleEditException(_('Encountered XML syntax error: %s (line number may be wrong, '
                                               'try subtracting one from the reported line number)') % (e,))
            except Exception:
                raise self.RuleEditException(_('Your XML is not valid'))
            msg = _('Rule "%s" saved.') % rule.name

        return msg


def _del_action(lgr, idx):
    del lgr.actions[idx]
    action_xml = lgr.actions_xml.pop(idx)
    logger.debug('deleted action[%d]: %s', idx, action_xml)


def _update_action(lgr, idx, action, body):
    if 0 <= idx < len(lgr.actions):
        lgr.actions[idx] = action
        lgr.actions_xml[idx] = body
    else:
        lgr.add_action(action)
        lgr.actions_xml.append(body)


def _parse_action(xml):
    lgr_xml = LGR_SKEL.format(ns=LGR_NS, xml=xml).encode('utf-8')
    lgr_info = LGRInfo.from_dict(
        {
            'xml': lgr_xml,
            'validate': False
        },
        lgr_loader_func=None
    )
    if lgr_info.lgr.actions:
        return lgr_info.lgr.actions[0]
    else:
        return None


class RuleEditActionAjaxView(RuleEditAjaxView):
    def process_request(self, delete_action, body):
        if not delete_action and not body:
            raise self.RuleEditException(_('No body specified'))

        lgr = self.lgr_info.lgr

        action_idx = self.kwargs['action_idx']
        action_idx = int(action_idx)  # 0-based
        # negative action_idx means to add new
        if action_idx + 1 > len(lgr.actions):
            raise self.RuleEditException(_('Action "%s" does not exist') % action_idx)

        if delete_action:
            _del_action(lgr, action_idx)
            msg = _('Action "%s" deleted.') % action_idx
        else:
            try:
                action = _parse_action(body)
                if not action:
                    raise self.RuleEditException(_('No action element found'))
            except LGRException as e:
                raise self.RuleEditException(lgr_exception_to_text(e))
            except XMLSyntaxError as e:
                raise self.RuleEditException(_('Encountered XML syntax error: %s (line number may be wrong, '
                                               'try subtracting one from the reported line number)') % (e,))
            except Exception:
                raise self.RuleEditException(_('Your XML is not valid'))

            _update_action(lgr, action_idx, action, body)
            msg = _('Action saved.')

        return msg
