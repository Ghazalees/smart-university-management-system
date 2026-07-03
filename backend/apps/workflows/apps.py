"""Defines Django application metadata for university requests, assignments, statuses, and revisions."""

from django.apps import AppConfig


class WorkflowsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.workflows"
