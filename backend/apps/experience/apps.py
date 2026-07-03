"""Defines Django application metadata for user experience preferences, feedback, search, and calendar features."""

from django.apps import AppConfig


class ExperienceConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.experience"
    verbose_name = "Digital Experience"
