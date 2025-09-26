from django.urls import path

from lgr_advanced.lgr_validator.views import (
    ValidateLabelCSVView,
    ValidateLabelJsonView,
    ValidateLabelNoFrameView,
    ValidateLabelView)

urlpatterns = [
    path('eval/<lgr_model:model>/<int:lgr_pk>/json/', ValidateLabelJsonView.as_view(), name='lgr_validate_json'),
    path('eval/<lgr_model:model>/<int:lgr_pk>/csv/', ValidateLabelCSVView.as_view(), name='lgr_validate_csv'),
    path('eval/<lgr_model:model>/<int:lgr_pk>/validate/', ValidateLabelView.as_view(), name='lgr_validate_label'),
    path('eval/<lgr_model:model>/<int:lgr_pk>/validate-nf/', ValidateLabelNoFrameView.as_view(),
         name='lgr_validate_label_noframe'),
]
