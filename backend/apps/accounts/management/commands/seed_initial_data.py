from django.core.management.base import BaseCommand
from django.db import transaction

from apps.accounts.models import Department, Permission, Profile, Role, User, UserRole


class Command(BaseCommand):
    """Seed core roles, permissions, departments, and demo users."""

    @transaction.atomic
    def handle(self, *args, **options):
        """Run the seed process."""
        permissions = self._seed_permissions()
        self._seed_roles(permissions)
        department, _ = Department.objects.get_or_create(
            name="Computer Engineering", code="CE"
        )
        self._create_user(
            "student@university.local",
            "student",
            "Student123!",
            Role.STUDENT,
            "Demo Student",
            department,
            student_number="S-1001",
        )
        self._create_user(
            "professor@university.local",
            "professor",
            "Professor123!",
            Role.PROFESSOR,
            "Demo Professor",
            department,
            employee_number="P-2001",
        )
        self._create_user(
            "staff@university.local",
            "staff",
            "Staff123!",
            Role.ADMINISTRATIVE_STAFF,
            "Demo Staff",
            department,
            employee_number="A-3001",
        )
        self._create_user(
            "president@university.local",
            "president",
            "President123!",
            Role.UNIVERSITY_PRESIDENT,
            "Demo President",
            department,
            employee_number="M-4001",
        )
        self.stdout.write(self.style.SUCCESS("initial data seeded successfully."))

    def _seed_permissions(self):
        """Create the initial permission set used by the four core roles."""
        definitions = [
            ("auth.login", "Login to system"),
            ("dashboard.view", "View own role dashboard"),
            ("profile.view", "View own profile"),
            ("profile.update", "Update own profile"),
            ("question.submit", "Submit questions"),
            ("request.submit", "Submit workflow requests"),
            ("user.read", "Read user accounts"),
            ("user.manage", "Manage user accounts"),
            ("role.manage", "Manage roles and permissions"),
            ("question.read", "Read authorized questions"),
            ("question.answer", "Answer authorized questions"),
            ("audit.read", "Read audit logs"),
            ("report.view", "View management reports"),
            ("system.manage", "Manage system settings"),
        ]
        result = {}
        for code, name in definitions:
            permission, _ = Permission.objects.get_or_create(
                code=code, defaults={"name": name}
            )
            result[code] = permission
        return result

    def _seed_roles(self, permissions):
        """Create the four initial system roles and assign their base permissions."""
        role_permissions = {
            Role.STUDENT: [
                "auth.login",
                "dashboard.view",
                "profile.view",
                "profile.update",
                "question.submit",
                "request.submit",
            ],
            Role.PROFESSOR: [
                "auth.login",
                "dashboard.view",
                "profile.view",
                "profile.update",
                "question.submit",
                "question.read",
                "question.answer",
            ],
            Role.ADMINISTRATIVE_STAFF: [
                "auth.login",
                "dashboard.view",
                "profile.view",
                "profile.update",
                "user.read",
                "user.manage",
                "question.read",
                "question.answer",
                "audit.read",
            ],
            Role.UNIVERSITY_PRESIDENT: list(permissions.keys()),
        }
        for role_name, permission_codes in role_permissions.items():
            role, _ = Role.objects.get_or_create(
                name=role_name, defaults={"description": f"Default {role_name} role"}
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
    ):
        """Create a demo user with profile and role when it does not exist."""
        user, created = User.objects.get_or_create(
            email=email, defaults={"username": username, "is_active": True}
        )
        if created:
            user.set_password(password)
            user.save()
        role = Role.objects.get(name=role_name)
        UserRole.objects.get_or_create(user=user, role=role)
        Profile.objects.get_or_create(
            user=user,
            defaults={
                "full_name": full_name,
                "department": department,
                "student_number": student_number,
                "employee_number": employee_number,
            },
        )
