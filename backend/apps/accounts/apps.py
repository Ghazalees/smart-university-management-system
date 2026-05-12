"""Django app configuration for the accounts module."""
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    """Register the accounts app used for users, roles, profiles, and RBAC data."""

    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.accounts"
    label = "accounts"
