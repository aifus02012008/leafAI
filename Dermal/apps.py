from django.apps import AppConfig


class DermalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'Dermal'

    def ready(self):
        import Dermal.signals  # Register signal handlers
