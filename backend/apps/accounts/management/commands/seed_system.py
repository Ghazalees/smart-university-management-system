"""Implements seed system behavior for user accounts, roles, permissions, and authentication."""

from .seed_initial_data import Command as SeedInitialDataCommand


class Command(SeedInitialDataCommand):
    help = "Idempotently seed the canonical system roles and permissions"

    def handle(self, *args, **options):
        options["system_only"] = True
        return super().handle(*args, **options)
