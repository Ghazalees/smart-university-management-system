"""Defines Django application metadata for shared platform infrastructure and cross-cutting utilities."""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
