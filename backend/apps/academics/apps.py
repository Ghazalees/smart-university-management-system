"""Defines Django application metadata for academic classes, enrollments, exams, grades, and progress."""

from django.apps import AppConfig


class AcademicsConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.academics"
