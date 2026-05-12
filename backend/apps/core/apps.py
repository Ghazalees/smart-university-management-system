from django.apps import AppConfig


class CoreConfig(AppConfig):
    """Configure shared core app for health-check and common API utilities."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
