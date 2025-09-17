import logging

from django.apps import apps
from django.db.models import Model
from django.http import Http404

from lgr_models.models.lgr import LgrBaseModel

logger = logging.getLogger(__name__)

ALL_LGR_MODELS = {}


def get_model_from_name(model_name_or_model: str | Model) -> Model:
    model = model_name_or_model
    if isinstance(model_name_or_model, str):
        model = apps.get_model(model_name_or_model)
    return model


def get_model_from_url_name(model_name: str) -> Model:
    global ALL_LGR_MODELS

    if not ALL_LGR_MODELS:
        for model in apps.get_models():
            if issubclass(model, LgrBaseModel):
                # XXX this may lead to conflicts if some different apps have the same model name
                ALL_LGR_MODELS[model._meta.label.lower().replace('model', '').rsplit('.', 1)[-1]] = model
    if model_name.lower() in ALL_LGR_MODELS:
        return ALL_LGR_MODELS[model_name.lower()]
    raise Http404
