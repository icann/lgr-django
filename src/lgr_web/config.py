from django.db import OperationalError

from lgr_models.models.settings import LGRSettings

LGR_SETTINGS = None

def get_lgr_settings() -> LGRSettings | None:
    global LGR_SETTINGS
    if LGR_SETTINGS is None:
        try:
            LGR_SETTINGS = LGRSettings.objects.get(pk=1)
        except (OperationalError, LGRSettings.DoesNotExist):
            pass
    return LGR_SETTINGS
