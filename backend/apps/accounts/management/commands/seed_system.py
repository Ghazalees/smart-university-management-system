from django.core.management.base import BaseCommand
from django.db import transaction
from apps.accounts.models import Permission, Role

PERMISSIONS = {
    "users.view": "View users",
    "users.manage": "Create and update users",
    "users.assign_role": "Assign roles",
    "documents.view": "View permitted documents",
    "documents.manage": "Create and update documents",
    "questions.create": "Submit questions",
    "questions.view_own": "View own questions",
    "questions.view_all": "View all questions",
    "questions.answer": "Generate answers",
}
ROLE_PERMISSIONS = {
    Role.STUDENT: ["documents.view", "questions.create", "questions.view_own"],
    Role.PROFESSOR: ["documents.view", "questions.create", "questions.view_own"],
    Role.ADMIN_STAFF: list(PERMISSIONS),
    Role.PRESIDENT: list(PERMISSIONS),
}

class Command(BaseCommand):
    help = "Idempotently seed system roles and permissions"

    @transaction.atomic
    def handle(self, *args, **options):
        permissions = {}
        for code, name in PERMISSIONS.items():
            permissions[code], _ = Permission.objects.update_or_create(code=code, defaults={"name": name})
        for role_name, codes in ROLE_PERMISSIONS.items():
            role, _ = Role.objects.update_or_create(name=role_name, defaults={"is_system": True})
            role.permissions.set([permissions[code] for code in codes])
        self.stdout.write(self.style.SUCCESS("System roles and permissions seeded."))
