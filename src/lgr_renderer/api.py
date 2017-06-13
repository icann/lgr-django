# -*- coding: utf-8 -*-
"""
api.py - API of the LGR renderer.

Responsible for creating the proper context to render the HTML view of an LGR document.
"""
from __future__ import unicode_literals
import logging

from django.utils.translation import ugettext_lazy as _
from django.utils.text import mark_safe
from django.utils.html import format_html_join

from lgr_editor import unidb
from lgr_editor.utils import render_cp, render_glyph, render_name, cp_to_slug

logger = logging.getLogger(__name__)


def _generate_references(references):
    """
    Generate the HTMl output from a list of references.

    :param references: List of reference's ids.
    :return: HTML string to be used in template.
    """
    return format_html_join(", ", "<a href=#ref_{0}>[{0}]</a>", ((r,) for r in references))


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
        ctx_meta.append((_('Language(s)'), '<br/>'.join(metadata.languages)))
    if metadata.scopes:
        ctx_meta.append((_('Scope(s)'), metadata.scopes))
    if metadata.validity_start is not None:
        ctx_meta.append((_('Validity Start'), metadata.validity_start))
    if metadata.validity_end is not None:
        ctx_meta.append((_('Validity End'), metadata.validity_end))
    if metadata.unicode_version is not None:
        ctx_meta.append((_('Unicode Version'), metadata.unicode_version))

    if metadata.description is not None:
        context['description'] = metadata.description.value

    return context


def _generate_context_repertoire(repertoire, udata):
    """
    Generate the context of an LGR's repertoire.

    :param repertoire: The LGR's repertoire object.
    :param udata: The unicode database.
    :return: Context to be used in template.
    """

    ctx = []
    for char in repertoire:
        ctx.append({
            'cp': cp_to_slug(char.cp),
            'cp_disp': render_cp(char),
            'glyph': render_glyph(char),
            'script': udata.get_script(char.cp[0]),
            'name': render_name(char, udata),
            'tags': char.tags,
            'references': _generate_references(char.references),
            'comment': char.comment or '',
        })
    return ctx


def _generate_context_variant_sets(repertoire, udata):
    """
    Generate the context of an LGR's variant sets.

    :param repertoire: The LGR's repertoire object.
    :param udata: The unicode database.
    :return: Context to be used in template.
    """
    ctx = []

    for variant_set in repertoire.get_variant_sets():
        set_ctx = []
        for cp in variant_set:
            char = repertoire.get_char(cp)
            for var in char.get_variants():
                set_ctx.append({
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
        ctx.append(set_ctx)

    return ctx


def _generate_clz_definition(clz):
    """
    Generate the definition of a class.

    :param clz: The class object.
    :return: HTML string to be used in template.
    """
    if clz.from_tag is not None:
        return mark_safe("Tag=&nbsp;<strong>{}</strong>".format(clz.from_tag))
    if clz.unicode_property is not None:
        return mark_safe("Unicode property=&nbsp;<strong>{}</strong>".format(clz.unicode_property))
    if clz.by_ref is not None:
        return mark_safe("By Ref=&nbsp;<strong></strong>".format(clz.by_ref))

    return ''


def _generate_context_classes(lgr, udata):
    """
    Generate the context of an LGR's classes.

    :param lgr: LGR to process.
    :param udata: The unicode database.
    :return: Context to be used in template.
    """
    ctx = []
    for clz in lgr.classes_lookup.values():
        ctx.append({
            'name': clz.name,
            'definition': _generate_clz_definition(clz),
            'references': _generate_references(clz.ref),
            'members': clz.get_pattern(lgr.rules_lookup, lgr.classes_lookup, udata, as_set=True)
        })

    return ctx


def _generate_context_rules(lgr, udata):
    """
    Generate the context of an LGR's rules.

    :param lgr: LGR to process.
    :param udata: The unicode database.
    :return: Context to be used in template.
    """
    ctx = []
    for rule in lgr.rules_lookup.values():
        ctx.append({
            'name': rule.name,
            'regex': rule.get_pattern(lgr.rules_lookup, lgr.classes_lookup, udata),
            'comment': rule.comment,
        })

    return ctx


def _generate_action_condition_rule_variant_set(action):
    """
    Given an action, generate the condition and rule/variant string.

    :param action: Action object.
    :return: (condition, rule/variant)
    """
    if action.match is not None:
        return 'if label match ', mark_safe('<a href="#rule_{0}">{0}</a>'.format(action.match))
    elif action.not_match is not None:
        return 'if label does not match ', mark_safe('<a href="#rule_{0}">{0}</a>'.format(action.not_match))
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
    :return: Context to be used in template.
    """
    ctx = []
    for action in lgr.actions:
        condition, rule_variant_set = _generate_action_condition_rule_variant_set(action)
        ctx.append({
            'condition': condition,
            'rule_variant_set': rule_variant_set,
            'disposition': action.disp,
            'references': _generate_references([]),
            'comment': action.comment or ''
        })

    return ctx


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

    return ctx


def generate_context(lgr):
    """
    Generate the context of an LGR.

    :param lgr: The LGR to generate the context for.
    :return: The context, as a dict.
    """
    context = {}

    udata = unidb.manager.get_db_by_version(lgr.metadata.unicode_version)

    context.update(_generate_context_metadata(lgr.metadata))
    context['repertoire'] = _generate_context_repertoire(lgr.repertoire, udata)
    context['variant_sets'] = _generate_context_variant_sets(lgr.repertoire, udata)
    context['classes'] = _generate_context_classes(lgr, udata)
    context['rules'] = _generate_context_rules(lgr, udata)
    context['actions'] = _generate_context_actions(lgr)
    context['references'] = _generate_context_references(lgr.reference_manager)

    return context
