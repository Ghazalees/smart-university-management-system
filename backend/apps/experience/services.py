"""Contains reusable business logic for user experience preferences, feedback, search, and calendar features."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime, timedelta

from django.db.models import Q
from django.utils import timezone

from apps.academics.models import AcademicClass, Exam
from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.documents.models import Document
from apps.workflows.models import WorkflowRequest


@dataclass(frozen=True)
class SearchResult:
    result_type: str
    identifier: int
    title: str
    subtitle: str
    url: str
    metadata: dict


class SearchProvider(ABC):
    @abstractmethod
    def search(self, user, query, limit): ...


class DocumentSearchProvider(SearchProvider):
    def search(self, user, query, limit):
        from apps.documents.repositories import DocumentRepositoryFactory

        qs = DocumentRepositoryFactory.create().search(user, query)[:limit]
        return [
            SearchResult(
                "document",
                item.pk,
                item.title,
                f"{item.get_document_type_display()} · {item.get_status_display()}",
                f"/documents/{item.pk}",
                {"status": item.status, "updated_at": item.updated_at.isoformat()},
            )
            for item in qs
        ]


class AcademicSearchProvider(SearchProvider):
    def search(self, user, query, limit):
        qs = AcademicClass.objects.select_related("course", "professor").filter(
            Q(course__code__icontains=query)
            | Q(course__title__icontains=query)
            | Q(location__icontains=query)
        )
        if user.has_system_permission("academics.manage"):
            pass
        elif user.has_role("Professor"):
            qs = qs.filter(professor=user)
        else:
            qs = qs.filter(enrollments__student=user)
        return [
            SearchResult(
                "class",
                item.pk,
                f"{item.course.code} · {item.course.title}",
                f"{item.term} · {item.get_weekday_display()} · {item.location}",
                "/academics/classes",
                {"term": item.term, "section": item.section},
            )
            for item in qs.distinct()[:limit]
        ]


class WorkflowSearchProvider(SearchProvider):
    def search(self, user, query, limit):
        qs = WorkflowRequest.objects.select_related("request_type", "requester").filter(
            Q(request_number__icontains=query)
            | Q(title__icontains=query)
            | Q(description__icontains=query)
        )
        if not user.has_system_permission("workflows.view_all"):
            qs = qs.filter(Q(requester=user) | Q(assigned_to=user))
        return [
            SearchResult(
                "workflow",
                item.pk,
                item.title,
                f"{item.request_number} · {item.get_status_display()}",
                f"/workflows/{item.pk}",
                {"status": item.status, "version": item.version},
            )
            for item in qs[:limit]
        ]


class UserSearchProvider(SearchProvider):
    def search(self, user, query, limit):
        if not user.has_system_permission("users.view"):
            return []
        qs = User.objects.filter(is_active=True).filter(
            Q(username__icontains=query)
            | Q(email__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
        )
        return [
            SearchResult(
                "user",
                item.pk,
                item.get_full_name() or item.username,
                item.email,
                "/admin/users",
                {"roles": item.role_names},
            )
            for item in qs[:limit]
        ]


class GlobalSearchRepository:
    """Repository/facade combining authorized providers without leaking records."""

    def __init__(self, providers=None):
        self.providers = providers or [
            DocumentSearchProvider(),
            AcademicSearchProvider(),
            WorkflowSearchProvider(),
            UserSearchProvider(),
        ]

    def search(self, user, query, limit=6):
        results = []
        for provider in self.providers:
            results.extend(provider.search(user, query, limit))
        return sorted(results, key=lambda item: (item.result_type, item.title.lower()))[
            : limit * 3
        ]


class CalendarBuilder:
    """Builder that composes role-aware academic, workflow and governance events."""

    def __init__(self, user, start, end):
        self.user = user
        self.start = start
        self.end = end
        self.events = []

    def add_classes(self):
        classes = AcademicClass.objects.select_related("course", "professor").filter(
            is_active=True
        )
        if self.user.has_system_permission("academics.manage"):
            pass
        elif self.user.has_role("Professor"):
            classes = classes.filter(professor=self.user)
        else:
            classes = classes.filter(enrollments__student=self.user)
        current = self.start.date()
        while current <= self.end.date():
            weekday = current.isoweekday()
            for item in classes.filter(weekday=weekday).distinct():
                starts = timezone.make_aware(datetime.combine(current, item.start_time))
                ends = timezone.make_aware(datetime.combine(current, item.end_time))
                if starts <= self.end and ends >= self.start:
                    self.events.append(
                        {
                            "id": f"class-{item.pk}-{current.isoformat()}",
                            "type": "class",
                            "title": f"{item.course.code} · {item.course.title}",
                            "start": starts.isoformat(),
                            "end": ends.isoformat(),
                            "location": item.location,
                            "url": "/academics/classes",
                            "status": "scheduled",
                        }
                    )
            current += timedelta(days=1)
        return self

    def add_exams(self):
        exams = Exam.objects.select_related("academic_class__course").filter(
            scheduled_at__range=(self.start, self.end)
        )
        if self.user.has_system_permission("academics.manage"):
            pass
        elif self.user.has_role("Professor"):
            exams = exams.filter(academic_class__professor=self.user)
        else:
            exams = exams.filter(academic_class__enrollments__student=self.user)
        for item in exams.distinct():
            self.events.append(
                {
                    "id": f"exam-{item.pk}",
                    "type": "exam",
                    "title": item.title,
                    "subtitle": item.academic_class.course.title,
                    "start": item.scheduled_at.isoformat(),
                    "end": (
                        item.scheduled_at + timedelta(minutes=item.duration_minutes)
                    ).isoformat(),
                    "location": item.location,
                    "url": "/academics/exams",
                    "status": "scheduled",
                }
            )
        return self

    def add_workflows(self):
        qs = WorkflowRequest.objects.filter(
            requester=self.user,
            updated_at__range=(self.start, self.end),
        )
        for item in qs:
            self.events.append(
                {
                    "id": f"workflow-{item.pk}",
                    "type": "workflow",
                    "title": item.title,
                    "start": item.updated_at.isoformat(),
                    "end": item.updated_at.isoformat(),
                    "url": f"/workflows/{item.pk}",
                    "status": item.status,
                }
            )
        return self

    def add_document_reviews(self):
        if not self.user.has_system_permission("documents.manage"):
            return self
        qs = Document.objects.filter(review_due_at__range=(self.start, self.end))
        for item in qs:
            self.events.append(
                {
                    "id": f"document-review-{item.pk}",
                    "type": "review",
                    "title": f"Review: {item.title}",
                    "start": item.review_due_at.isoformat(),
                    "end": item.review_due_at.isoformat(),
                    "url": f"/documents/{item.pk}",
                    "status": "due",
                }
            )
        return self

    def build(self):
        return sorted(self.events, key=lambda item: item["start"])


class ActivityFeedService:
    @staticmethod
    def for_user(user, limit=30):
        qs = AuditLog.objects.select_related("actor")
        if not user.has_system_permission("reports.view_all"):
            qs = qs.filter(actor=user)
        return [
            {
                "id": item.pk,
                "action": item.action,
                "entity_type": item.entity_type,
                "entity_id": item.entity_id,
                "actor": (
                    item.actor.get_full_name() or item.actor.username
                    if item.actor
                    else "System"
                ),
                "metadata": item.metadata,
                "created_at": item.created_at.isoformat(),
            }
            for item in qs[:limit]
        ]
