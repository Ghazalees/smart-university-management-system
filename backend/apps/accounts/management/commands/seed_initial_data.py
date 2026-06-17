from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Department, Permission, Profile, Role, User, UserRole


class Command(BaseCommand):
    @transaction.atomic
    def handle(self, *args, **options):
        permissions = self._seed_permissions()
        self._seed_roles(permissions)

        department, _ = Department.objects.update_or_create(
            code="CE",
            defaults={"name": "Computer Engineering", "is_active": True},
        )

        self._create_user(
            email="student@university.local",
            username="student",
            password="Student123!",
            role_name=Role.STUDENT,
            full_name="Demo Student",
            department=department,
            student_number="S-1001",
        )
        self._create_user(
            email="professor@university.local",
            username="professor",
            password="Professor123!",
            role_name=Role.PROFESSOR,
            full_name="Demo Professor",
            department=department,
            employee_number="P-2001",
        )
        self._create_user(
            email="staff@university.local",
            username="staff",
            password="Staff123!",
            role_name=Role.ADMIN_STAFF,
            full_name="Demo Staff",
            department=department,
            employee_number="A-3001",
            is_staff=True,
        )
        self._create_user(
            email="president@university.local",
            username="president",
            password="President123!",
            role_name=Role.PRESIDENT,
            full_name="Demo President",
            department=department,
            employee_number="M-4001",
            is_staff=True,
        )

        self.stdout.write(self.style.SUCCESS("initial data seeded successfully."))

    def _seed_permissions(self):
        definitions = [
            ("dashboard.view", "View own role dashboard"),
            ("profile.view", "View own profile"),
            ("profile.update", "Update own profile"),
            ("users.view", "View users"),
            ("users.manage", "Create and update users"),
            ("users.assign_role", "Assign roles"),
            ("documents.view", "View permitted documents"),
            ("documents.manage", "Create and update documents"),
            ("questions.create", "Submit questions"),
            ("questions.view_own", "View own questions"),
            ("questions.view_all", "View all questions"),
            ("questions.answer", "Generate answers"),
        ]

        result = {}
        for code, name in definitions:
            permission, _ = Permission.objects.update_or_create(
                code=code,
                defaults={"name": name},
            )
            result[code] = permission
        return result

    def _seed_roles(self, permissions):
        role_permissions = {
            Role.STUDENT: [
                "dashboard.view",
                "profile.view",
                "profile.update",
                "documents.view",
                "questions.create",
                "questions.view_own",
            ],
            Role.PROFESSOR: [
                "dashboard.view",
                "profile.view",
                "profile.update",
                "documents.view",
                "questions.create",
                "questions.view_own",
                "questions.view_all",
                "questions.answer",
            ],
            Role.ADMIN_STAFF: [
                "dashboard.view",
                "profile.view",
                "profile.update",
                "users.view",
                "users.manage",
                "users.assign_role",
                "documents.view",
                "documents.manage",
                "questions.create",
                "questions.view_own",
                "questions.view_all",
                "questions.answer",
            ],
            Role.PRESIDENT: list(permissions.keys()),
        }

        for role_name, permission_codes in role_permissions.items():
            role, _ = Role.objects.update_or_create(
                name=role_name,
                defaults={
                    "description": f"Default {role_name} role",
                    "is_system": True,
                },
            )
            role.permissions.set([permissions[code] for code in permission_codes])

    def _create_user(
        self,
        email,
        username,
        password,
        role_name,
        full_name,
        department,
        student_number="",
        employee_number="",
        is_staff=False,
    ):
        name_parts = full_name.split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        user, _ = User.objects.update_or_create(
            email=email,
            defaults={
                "username": username,
                "first_name": first_name,
                "last_name": last_name,
                "department": department,
                "is_active": True,
                "is_staff": is_staff,
            },
        )
        user.set_password(password)
        user.save()

        role = Role.objects.get(name=role_name)
        UserRole.objects.get_or_create(user=user, role=role)

        profile, _ = Profile.objects.get_or_create(user=user)
        profile.student_number = student_number
        profile.employee_number = employee_number
        profile.save(update_fields=["student_number", "employee_number", "updated_at"])
