"""
lgr_web URL Configuration

The `urlpatterns` list routes URLs to views. For more information, please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
"""
from django.conf.urls import include
from django.urls import path, register_converter

from lgr_utils.converters import LgrModelConverter
from lgr_web.converters import (
    ActionIndexConverter,
    CodePointSlugConverter,
    FileNameConverter,
    ReferenceIdConverter,
    StorageTypeConverter,
    TagSlugConverter,
    VarSlugConverter)
from lgr_web.views import (
    LGRAboutView,
    LGRHelpView,
    LGRModesView,
    LabelFileFormsView,
    LabelFormsView,
    LanguageAutocomplete)

# Once set, a converter cannot be overwritten or duplicated.
# They must be set only once.
register_converter(ActionIndexConverter, 'action')
register_converter(CodePointSlugConverter, 'cp')
register_converter(FileNameConverter, 'filename')
register_converter(ReferenceIdConverter, 'ref')
register_converter(StorageTypeConverter, 'storage')
register_converter(TagSlugConverter, 'tag')
register_converter(VarSlugConverter, 'var')
register_converter(LgrModelConverter, 'lgr_model')

urlpatterns = [
    path('a/', include('lgr_advanced.urls')),
    path('b/', include('lgr_basic.urls')),
    path('r/', include('lgr_idn_table_review.urls')),
    path('m/', include('lgr_manage.urls')),
    path('auth/', include('lgr_auth.urls')),
    path('storage/', include('lgr_session.urls')),
    path('render/', include('lgr_renderer.urls')),
    path('tasks/', include('lgr_tasks.urls')),
    path('u/', include('lgr_utils.urls')),

    # Autocompletion
    path('language-autocomplete/', LanguageAutocomplete.as_view(), name='language-autocomplete'),

    path('i18n/', include('django.conf.urls.i18n')),

    path('about/', LGRAboutView.as_view(), name='about'),
    path('help/', LGRHelpView.as_view(), name='help'),
    path('label_forms/', LabelFormsView.as_view(), name='lgr_label_forms'),
    path('label_file_forms/', LabelFileFormsView.as_view(), name='lgr_label_file_forms'),

    path('', LGRModesView.as_view(), name='lgr_home'),
]
