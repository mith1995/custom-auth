from django.apps import AppConfig

class AuthnestConfig(AppConfig):
    name = "authnest"
    default_auto_field = "django.db.models.BigAutoField"
    verbose_name = "Authnest"

    def ready(self):
        from .conf import authnest_settings
        authnest_settings.validate()