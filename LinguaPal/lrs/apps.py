from django.apps import AppConfig


class LrsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'lrs'
    verbose_name = 'Learning Record Store'

    def ready(self):
        # Import signals when the app is ready
        try:
            import lrs.signals  # noqa: F401
        except ImportError:
            pass
