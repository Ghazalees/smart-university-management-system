"""Defines Django application metadata for grounded question answering, retrieval, and AI orchestration."""

from django.apps import AppConfig


class QaConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.qa"
