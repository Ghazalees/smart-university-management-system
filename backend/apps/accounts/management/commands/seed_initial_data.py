"""Implements seed initial data behavior for user accounts, roles, permissions, and authentication."""

import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from apps.academics.models import (
    AcademicClass,
    Course,
    CoursePrerequisite,
    Enrollment,
    ProgramRequirement,
    StudentAcademicGoal,
)
from apps.accounts.models import Department, Permission, Profile, Role, User, UserRole
from apps.documents.models import Document
from apps.documents.services import DocumentVersionService
from apps.workflows.models import WorkflowType

PERMISSIONS = {
    "dashboard.view": "View own role dashboard",
    "profile.view": "View own profile",
    "profile.update": "Update own profile",
    "users.view": "View users",
    "users.manage": "Create and update users",
    "users.assign_role": "Assign roles",
    "roles.manage": "Manage role permission matrices",
    "documents.view": "View permitted documents",
    "documents.manage": "Create and update documents",
    "questions.create": "Submit questions",
    "questions.view_own": "View own questions",
    "questions.view_all": "View all questions",
    "questions.answer": "Generate or provide answers",
    "workflows.create": "Create workflow requests",
    "workflows.view_own": "View own workflow requests",
    "workflows.view_all": "View all workflow requests",
    "workflows.review": "Review workflow requests",
    "workflows.configure": "Configure workflow types",
    "notifications.view": "View notifications",
    "notifications.broadcast": "Publish notifications",
    "academics.view": "View academic information",
    "classes.create": "Create and update own classes",
    "grades.manage": "Record grades for own classes",
    "academics.manage": "Manage all academic records",
    "reports.view_all": "View management reports",
    "audit.view": "View audit logs",
    "feedback.manage": "Manage platform feedback",
}

ROLE_PERMISSIONS = {
    Role.STUDENT: [
        "dashboard.view",
        "profile.view",
        "profile.update",
        "documents.view",
        "questions.create",
        "questions.view_own",
        "workflows.create",
        "workflows.view_own",
        "notifications.view",
        "academics.view",
    ],
    Role.PROFESSOR: [
        "dashboard.view",
        "profile.view",
        "profile.update",
        "documents.view",
        "questions.create",
        "questions.view_own",
        "workflows.create",
        "workflows.view_own",
        "notifications.view",
        "academics.view",
        "classes.create",
        "grades.manage",
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
        "workflows.create",
        "workflows.view_own",
        "workflows.view_all",
        "workflows.review",
        "notifications.view",
        "notifications.broadcast",
        "academics.view",
        "academics.manage",
        "reports.view_all",
        "feedback.manage",
    ],
    Role.PRESIDENT: list(PERMISSIONS),
}


class Command(BaseCommand):
    help = "Seed roles, permissions and optional development demonstration data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--system-only",
            action="store_true",
            help="Only create permissions and roles; do not create demonstration data.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        permissions = self._seed_permissions()
        roles = self._seed_roles(permissions)
        if options["system_only"]:
            self.stdout.write(
                self.style.SUCCESS("System roles and permissions seeded.")
            )
            return
        if not settings.DEBUG and os.getenv("ALLOW_DEMO_SEED", "0") != "1":
            raise CommandError(
                "Demo data seeding is disabled outside DEBUG. Set ALLOW_DEMO_SEED=1 explicitly."
            )
        self._seed_demo_data(roles)
        self.stdout.write(self.style.SUCCESS("Development demonstration data seeded."))

    def _seed_permissions(self):
        result = {}
        for code, name in PERMISSIONS.items():
            result[code], _ = Permission.objects.update_or_create(
                code=code, defaults={"name": name}
            )
        return result

    def _seed_roles(self, permissions):
        result = {}
        for role_name, permission_codes in ROLE_PERMISSIONS.items():
            role, _ = Role.objects.update_or_create(
                name=role_name,
                defaults={
                    "description": f"System role for {role_name}",
                    "is_system": True,
                },
            )
            role.permissions.set([permissions[code] for code in permission_codes])
            result[role_name] = role
        return result

    def _seed_demo_data(self, roles):
        department, _ = Department.objects.update_or_create(
            code="CE",
            defaults={"name": "Computer Engineering", "is_active": True},
        )
        student = self._create_user(
            "student@university.local",
            "student",
            os.getenv("DEMO_STUDENT_PASSWORD", "Student123!"),
            roles[Role.STUDENT],
            "Demo",
            "Student",
            department,
            student_number="S-1001",
        )
        professor = self._create_user(
            "professor@university.local",
            "professor",
            os.getenv("DEMO_PROFESSOR_PASSWORD", "Professor123!"),
            roles[Role.PROFESSOR],
            "Demo",
            "Professor",
            department,
            employee_number="P-2001",
        )
        staff = self._create_user(
            "staff@university.local",
            "staff",
            os.getenv("DEMO_STAFF_PASSWORD", "Staff123!"),
            roles[Role.ADMIN_STAFF],
            "Demo",
            "Staff",
            department,
            employee_number="A-3001",
            is_staff=True,
        )
        self._create_user(
            "president@university.local",
            "president",
            os.getenv("DEMO_PRESIDENT_PASSWORD", "President123!"),
            roles[Role.PRESIDENT],
            "Demo",
            "President",
            department,
            employee_number="M-4001",
            is_staff=True,
        )

        leave, _ = WorkflowType.objects.update_or_create(
            code="leave-request",
            defaults={
                "name": "Leave request",
                "description": "Academic or employment leave request.",
                "schema": {
                    "required": ["start_date", "end_date", "reason"],
                    "start_date": {
                        "type": "date",
                        "label": "Start date",
                        "required": True,
                    },
                    "end_date": {
                        "type": "date",
                        "label": "End date",
                        "required": True,
                        "visible_when": {
                            "field": "start_date",
                            "operator": "not_empty",
                        },
                    },
                    "reason": {
                        "type": "textarea",
                        "label": "Reason",
                        "required": True,
                        "help": "Explain the academic or employment impact.",
                    },
                    "medical": {"type": "checkbox", "label": "Medical reason"},
                    "supporting_document": {
                        "type": "text",
                        "label": "Supporting document reference",
                        "visible_when": {"field": "medical", "equals": True},
                    },
                },
            },
        )
        certificate, _ = WorkflowType.objects.update_or_create(
            code="certificate-request",
            defaults={
                "name": "Certificate request",
                "description": "Request an official university certificate.",
                "schema": {
                    "required": ["certificate_type", "delivery_method"],
                    "certificate_type": {
                        "type": "select",
                        "label": "Certificate type",
                        "required": True,
                        "options": ["Enrollment", "Graduation", "Transcript"],
                    },
                    "delivery_method": {
                        "type": "select",
                        "label": "Delivery method",
                        "required": True,
                        "options": ["Digital", "Campus pickup", "Postal mail"],
                    },
                    "postal_address": {
                        "type": "textarea",
                        "label": "Postal address",
                        "visible_when": {
                            "field": "delivery_method",
                            "equals": "Postal mail",
                        },
                    },
                },
            },
        )
        leave.allowed_roles.set([roles[Role.STUDENT], roles[Role.PROFESSOR]])
        certificate.allowed_roles.set([roles[Role.STUDENT]])

        policy, _ = Document.objects.update_or_create(
            title="Student Leave Policy",
            defaults={
                "document_type": Document.Type.POLICY,
                "content": (
                    "Students may request academic leave through the university portal. "
                    "A request must include the requested dates and a reason. The request "
                    "is reviewed by administrative staff before approval."
                ),
                "access_level": Document.AccessLevel.AUTHENTICATED,
                "status": Document.Status.PUBLISHED,
                "knowledge_enabled": True,
                "created_by": staff,
                "last_updated_by": staff,
                "published_at": timezone.now(),
            },
        )
        policy.mark_indexed()
        if not policy.versions.exists():
            DocumentVersionService.snapshot(policy, staff, "Seeded policy")

        course, _ = Course.objects.update_or_create(
            code="SE401",
            defaults={
                "title": "Advanced Software Engineering",
                "credits": 3,
                "department": department,
            },
        )
        academic_class, _ = AcademicClass.objects.update_or_create(
            course=course,
            term="Spring 2026",
            section="01",
            defaults={
                "professor": professor,
                "weekday": AcademicClass.Weekday.MONDAY,
                "start_time": "09:00",
                "end_time": "10:30",
                "location": "Engineering 204",
                "capacity": 30,
            },
        )
        Enrollment.objects.get_or_create(academic_class=academic_class, student=student)

        intro, _ = Course.objects.update_or_create(
            code="CS101",
            defaults={
                "title": "Introduction to Programming",
                "credits": 3,
                "department": department,
            },
        )
        algorithms, _ = Course.objects.update_or_create(
            code="CS202",
            defaults={
                "title": "Algorithms and Data Structures",
                "credits": 3,
                "department": department,
            },
        )
        ai_course, _ = Course.objects.update_or_create(
            code="AI410",
            defaults={
                "title": "Applied Artificial Intelligence",
                "credits": 3,
                "department": department,
            },
        )
        for index, required_course in enumerate(
            [intro, algorithms, course, ai_course], start=1
        ):
            ProgramRequirement.objects.update_or_create(
                department=department,
                course=required_course,
                defaults={
                    "category": ProgramRequirement.Category.CORE
                    if index < 4
                    else ProgramRequirement.Category.SPECIALIZED,
                    "minimum_score": 50,
                    "is_required": True,
                    "recommended_term": index,
                },
            )
        CoursePrerequisite.objects.update_or_create(
            course=algorithms, prerequisite=intro, defaults={"minimum_score": 50}
        )
        CoursePrerequisite.objects.update_or_create(
            course=ai_course, prerequisite=algorithms, defaults={"minimum_score": 55}
        )
        StudentAcademicGoal.objects.update_or_create(
            student=student,
            defaults={
                "target_gpa": 82,
                "target_graduation_term": "Spring 2027",
                "preferred_max_credits": 15,
            },
        )

    def _create_user(
        self,
        email,
        username,
        password,
        role,
        first_name,
        last_name,
        department,
        student_number="",
        employee_number="",
        is_staff=False,
    ):
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
        UserRole.objects.get_or_create(user=user, role=role)
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.student_number = student_number
        profile.employee_number = employee_number
        profile.save()
        return user
