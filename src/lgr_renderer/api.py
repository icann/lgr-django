# -*- coding: utf-8 -*-
"""
api.py - API of the LGR renderer.

Responsible for creating the proper context to render the HTML view of an LGR document.
"""
from __future__ import unicode_literals

import logging
import re
from itertools import izip, islice

from natsort import natsorted

from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html_join, format_html, mark_safe

from lgr.matcher import AnchorMatcher
from lgr.validate.lgr_stats import generate_stats
from lgr.classes import TAG_CLASSNAME_PREFIX

from lgr_editor import unidb
from lgr_editor.utils import (render_cp,
                              render_glyph,
                              render_name,
                              cp_to_slug,
                              cp_to_str)

logger = logging.getLogger(__name__)

# Number of class members to display
MAX_MEMBERS = 15


def _generate_references(references):
    """
    Generate the HTMl output from a list of references.

    :param references: List of reference's ids.
    :return: HTML string to be used in template.
    """
    if references:
        return format_html_join(", ", "<a href=#ref_{0}>[{0}]</a>", ((r,) for r in references))

    return ''


def _generate_context_metadata(metadata):
    """
    Generate the context of an LGR's metadata.

    :param metadata: The LGR's Metadata object.
    :return: Context to be used in template.
    """
    context = {}
    languages = metadata.languages
    context['main_language'] = languages[0] if len(languages) > 0 else 'not specified'

    ctx_meta = []
    context['metadata'] = ctx_meta

    if metadata.version is not None:
        ctx_meta.append((_('LGR Version'), metadata.version))
    if metadata.date is not None:
        ctx_meta.append((_('Date'), metadata.date))
    if languages:
        ctx_meta.append((_('Language(s)'), format_html_join('\n', '{}<br/>', ((l,) for l in metadata.languages))))
    if metadata.scopes:
        ctx_meta.append((_('Scope(s)'), format_html_join('\n', '{}<br/>', ((s,) for s in metadata.scopes))))
    if metadata.validity_start is not None:
        ctx_meta.append((_('Validity Start'), metadata.validity_start))
    if metadata.validity_end is not None:
        ctx_meta.append((_('Validity End'), metadata.validity_end))
    if metadata.unicode_version is not None:
        ctx_meta.append((_('Unicode Version'), metadata.unicode_version))

    if metadata.description is not None:
        context['description'] = metadata.description.value
        context['description_type'] = metadata.description.description_type

    return context


def _generate_context_char(char):
    """
    Given a char object, return the HTML string to be used in template.

    :param char: CharObject.
    :return: HTML string to be used in template.
    """
    output = ''
    if char.when is not None:
        output = format_html('when: <a href="#rule_{0}">{0}</a>', char.when)
    if char.not_when is not None:
        output = format_html('not-when: <a href="#rule_{0}">{0}</a>', char.not_when)
    return output


def _generate_context_repertoire(repertoire, variant_sets_sorted, udata):
    """
    Generate the context of an LGR's repertoire.

    :param repertoire: The LGR's repertoire object.
    :param udata: The unicode database.
    :return: Context to be used in template, List of context rules.
    """

    ctx = []
    ctx_rules = set()
    for char in repertoire:
        ctx_rules.add(char.when)
        ctx_rules.add(char.not_when)
        variant_id = ''
        for var_id, variant_set in variant_sets_sorted.items():
            if char.cp in variant_set:
                variant_id = var_id
        ctx.append({
            'cp': cp_to_slug(char.cp),
            'cp_disp': render_cp(char),
            'glyph': render_glyph(char),
            'script': udata.get_script(char.cp[0]),
            'name': render_name(char, udata),
            'context': _generate_context_char(char),
            'variant_set': variant_id,
            'tags': char.tags,
            'references': _generate_references(char.references),
            'comment': char.comment or '',
        })
    try:
        # Remove 'None' rule
        ctx_rules.remove(None)
    except KeyError:
        pass
    return ctx, ctx_rules


def _generate_context_variant_sets(repertoire, variant_sets_sorted, udata):
    """
    Generate the context of an LGR's variant sets.

    :param repertoire: The LGR's repertoire object.
    :param udata: The unicode database.
    :return: Context to be used in template.
    """
    ctx = []

    for set_id, variant_set in variant_sets_sorted.items():
        set_ctx = {
            'id': set_id,
            'variants': []
        }
        members = set()
        for cp in variant_set:
            char = repertoire.get_char(cp)
            for var in char.get_variants():
                members.add(var.cp)
                set_ctx['variants'].append({
                    'source_cp': cp_to_slug(char.cp),
                    'source_cp_disp': render_cp(char),
                    'source_glyph': render_glyph(char),
                    'source_name': render_name(char, udata),
                    'dest_cp': cp_to_slug(var.cp),
                    'dest_cp_disp': render_cp(var),
                    'dest_glyph': render_glyph(var),
                    'dest_name': render_name(var, udata),
                    'type': var.type,
                    'references': _generate_references(var.references),
                    'comment': var.comment or ''
                })
        set_ctx['number_members'] = len(members)
        ctx.append(set_ctx)

    return ctx


def _generate_clz_definition(clz):
    """
    Generate the definition of a class.

    :param clz: The class object.
    :return: HTML string to be used in template.
    """
    if clz.from_tag is not None:
        return format_html("Tag=&nbsp;<strong>{}</strong>", clz.from_tag)
    if clz.unicode_property is not None:
        return format_html("Unicode property=&nbsp;<strong>{}</strong>", clz.unicode_property)
    if clz.by_ref is not None:
        return format_html("By Ref=&nbsp;<strong></strong>", clz.by_ref)
    if clz.implicit:
        # Implicit tag-based class
        return format_html("Tag=&nbsp;<strong>{}</strong>", clz.name)

    return ''


def _generate_context_classes(lgr, udata):
    """
    Generate the context of an LGR's classes.

    :param lgr: LGR to process.
    :param udata: The unicode database.
    :return: Context to be used in template.
    """
    ctx = []
    repertoire = udata.get_set((c.cp[0] for c in lgr.repertoire.all_repertoire(include_sequences=False)),
                               freeze=True)
    for clz_name in sorted(lgr.classes_lookup.keys(), key=lambda x: (x.startswith(TAG_CLASSNAME_PREFIX), x)):
        clz = lgr.classes_lookup[clz_name]
        if clz.implicit and clz.name in lgr.classes:
            # Class is implicit for existing named class, ignore
            continue
        clz_members = clz.get_pattern(lgr.rules_lookup, lgr.classes_lookup,
                                       udata, as_set=True) & repertoire
        clz_members_len = len(clz_members)
        clz_members_display = ' '.join(('U+' + cp_to_str(c) for c in islice(clz_members, MAX_MEMBERS)))
        if clz_members_len > MAX_MEMBERS:
            clz_members_display += ' &hellip;'
        clz_members_display = mark_safe('{' + clz_members_display + '}')

        ctx.append({
            'name': clz.name if not clz.implicit else mark_safe('<i>implicit</i>'),
            'definition': _generate_clz_definition(clz) or _generate_links(clz),
            'references': _generate_references(clz.references),
            'comment': clz.comment or '' if not clz.implicit else '',
            'members': clz_members_display,
            'members_count': clz_members_len
        })

    return ctx


def _generate_context_rules(lgr, udata, context_rules, trigger_rules):
    """
    Generate the context of an LGR's rules.

    :param lgr: LGR to process.
    :param udata: The unicode database.
    :param context_rules: List of rule names used in context (when/not-when in repertoire).
    :param trigger_rules: List of rule names used in actions.
    :return: Context to be used in template.
    """
    def _has_anchor_rule(rule):
        """Utility function that test if a rule has an anchor."""
        if isinstance(rule, AnchorMatcher):
            return True
        for r in rule.iter_children():
            if _has_anchor_rule(r):
                return True
        return False

    ctx = []
    for rule in lgr.rules_lookup.values():
        ctx.append({
            'name': rule.name,
            'regex': rule.get_pattern(lgr.rules_lookup, lgr.classes_lookup, udata),
            'readable_regex': _generate_links(rule),
            'context': rule.name in context_rules,
            'trigger': rule.name in trigger_rules,
            'anchor': _has_anchor_rule(rule),
            'comment': rule.comment,
            'references': _generate_references(rule.references),
        })

    return ctx


def _generate_links(rule):
    readable_rule = '{}'.format(rule)
    # Add links in the rule
    # - links on codepoints
    for cp_match in re.finditer(r'U\+[0-9A-F]{4,}', readable_rule):
        cp = cp_match.group(0)
        ref = int(cp.lstrip('U+'), 16)
        readable_rule = readable_rule.replace(cp, format_html('<a href="#{}">{}</a>', ref, cp))
    # - links on classes references
    for match in re.finditer(r':(class|rule)-ref-([^:]+):', readable_rule):
        whole, obj, ref = match.group(0), match.group(1), match.group(2)
        readable_rule = readable_rule.replace(whole.strip(':'), format_html('<a href="#{0}_{1}">{1}</a>', obj, ref))

    return mark_safe(readable_rule)


def _generate_action_condition_rule_variant_set(action):
    """
    Given an action, generate the condition and rule/variant string.

    :param action: Action object.
    :return: (condition, rule/variant)
    """
    if action.match is not None:
        return 'if label match ', format_html('<a href="#rule_{0}">{0}</a>', action.match)
    elif action.not_match is not None:
        return 'if label does not match ', format_html('<a href="#rule_{0}">{0}</a>', action.not_match)
    elif action.any_variant is not None:
        return 'if at least one variant is in', '{' + ','.join(action.any_variant) + '}'
    elif action.all_variants is not None:
        return 'if all variants are in', '{' + ','.join(action.all_variants) + '}'
    elif action.only_variants is not None:
        return 'if only variants and variants are in', '{' + ','.join(action.only_variants) + '}'
    else:
        return 'if any label (catch-all)', ''


def _generate_context_actions(lgr):
    """
    Generate the context of an LGR's actions.

    :param lgr: LGR to process.
    :return: Context to be used in template, List of rule's names in action.
    """
    trigger_rules = set()
    ctx = []
    for action in lgr.actions:
        trigger_rules.add(action.match)
        trigger_rules.add(action.not_match)
        condition, rule_variant_set = _generate_action_condition_rule_variant_set(action)
        ctx.append({
            'condition': condition,
            'rule_variant_set': rule_variant_set,
            'disposition': action.disp,
            'references': _generate_references(action.references),
            'comment': action.comment or ''
        })

    try:
        # Remove 'None' rule
        trigger_rules.remove(None)
    except KeyError:
        pass
    return ctx, trigger_rules


def _generate_context_references(reference_manager):
    """
    Generate the context of an LGR's references.

    :param reference_manager: The reference manager.
    :return: Context to be used in template.
    """
    ctx = []
    for ref_id, ref in reference_manager.items():
        ctx.append({
            'id': ref_id,
            'value': ref['value'],
            'comment': ref.get('comment', ''),
        })

    return natsorted(ctx, key=lambda c: c['id'])


def generate_context(lgr):
    """
    Generate the context of an LGR.

    :param lgr: The LGR to generate the context for.
    :return: The context, as a dict.
    """
    context = {'name': lgr.name, 'stats': generate_stats(lgr)}

    udata = unidb.manager.get_db_by_version(lgr.metadata.unicode_version)

    variant_sets = lgr.repertoire.get_variant_sets()
    variant_sets_sorted = {idx: s for idx, s in izip(range(1, len(variant_sets) + 1), variant_sets)}

    context.update(_generate_context_metadata(lgr.metadata))
    context['repertoire'], ctxt_rules = _generate_context_repertoire(lgr.repertoire, variant_sets_sorted, udata)
    context['variant_sets'] = _generate_context_variant_sets(lgr.repertoire,
                                                             variant_sets_sorted,
                                                             udata)
    context['classes'] = _generate_context_classes(lgr, udata)
    context['actions'], trigger_rules = _generate_context_actions(lgr)
    context['rules'] = _generate_context_rules(lgr, udata, ctxt_rules, trigger_rules)
    context['references'] = _generate_context_references(lgr.reference_manager)

    return context
