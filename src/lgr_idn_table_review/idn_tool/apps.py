from django.apps import AppConfig
from django_cleanup.signals import cleanup_post_delete


class ToolConfig(AppConfig):
    name = 'lgr_idn_table_review.idn_tool'

    def ready(self):
        # FIXME: this is not working
        import lgr_models.signals
        cleanup_post_delete.connect(lgr_models.signals.delete_parent_folder)
