"""Defines Django application metadata for knowledge documents, versions, extraction, and governance."""

from django.apps import AppConfig


class DocumentsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.documents"
