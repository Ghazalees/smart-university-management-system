"""Implements authenticated API endpoints for role-aware dashboards and operational reports."""

from collections import Counter
from datetime import timedelta

from django.db.models import Avg, Count, Q
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.academics.models import AcademicClass, Exam, Grade
from apps.academics.services import AcademicRecommendationService
from apps.accounts.models import User
from apps.core.models import AuditLog
from apps.core.pagination import PaginationMixin
from apps.core.responses import success
from apps.documents.models import Document
from apps.notifications.models import Notification
from apps.qa.models import Question, QuestionResponse
from apps.workflows.models import WorkflowRequest

from .serializers import AuditLogSerializer


def _daily_counts(queryset, days=7):
    today = timezone.localdate()
    output = []
    for offset in range(days - 1, -1, -1):
        day = today - timedelta(days=offset)
        output.append(
            {
                "date": day.isoformat(),
                "value": queryset.filter(created_at__date=day).count(),
            }
        )
    return output


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        common = {
            "unread_notifications": Notification.objects.filter(
                recipient=user, read_at__isnull=True
            ).count(),
            "my_questions": Question.objects.filter(user=user).count(),
            "my_requests": WorkflowRequest.objects.filter(requester=user).count(),
            "generated_at": timezone.now(),
        }
        if user.has_system_permission("reports.view_all"):
            question_counts = dict(
                Question.objects.values_list("status").annotate(total=Count("id"))
            )
            workflow_counts = dict(
                WorkflowRequest.objects.values_list("status").annotate(
                    total=Count("id")
                )
            )
            active_users = User.objects.filter(is_active=True)
            published_docs = Document.objects.filter(
                status__in=[Document.Status.PUBLISHED, Document.Status.ACTIVE]
            )
            data = {
                **common,
                "scope": "management",
                "headline": "University operations at a glance",
                "users": active_users.count(),
                "users_by_role": list(
                    active_users.values("roles__name")
                    .annotate(total=Count("id", distinct=True))
                    .order_by("roles__name")
                ),
                "documents": published_docs.count(),
                "document_governance": {
                    "expired": published_docs.filter(
                        expires_at__lte=timezone.now()
                    ).count(),
                    "review_due": published_docs.filter(
                        review_due_at__lte=timezone.now()
                    ).count(),
                    "unindexed": published_docs.filter(indexed_at__isnull=True).count(),
                },
                "question_counts": question_counts,
                "workflow_counts": workflow_counts,
                "average_ai_confidence": QuestionResponse.objects.aggregate(
                    value=Avg("confidence")
                )["value"],
                "pending_workflows": WorkflowRequest.objects.filter(
                    status__in=[
                        WorkflowRequest.Status.PENDING,
                        WorkflowRequest.Status.UNDER_REVIEW,
                    ]
                ).count(),
                "trends": {
                    "users": _daily_counts(User.objects.all()),
                    "questions": _daily_counts(Question.objects.all()),
                    "requests": _daily_counts(WorkflowRequest.objects.all()),
                },
                "attention": [
                    {
                        "label": "Pending workflows",
                        "value": WorkflowRequest.objects.filter(
                            status__in=[
                                WorkflowRequest.Status.PENDING,
                                WorkflowRequest.Status.UNDER_REVIEW,
                            ]
                        ).count(),
                        "severity": "warning",
                        "url": "/workflows",
                    },
                    {
                        "label": "Escalated AI questions",
                        "value": Question.objects.filter(
                            status=Question.Status.ESCALATED
                        ).count(),
                        "severity": "danger",
                        "url": "/questions",
                    },
                    {
                        "label": "Documents due for review",
                        "value": published_docs.filter(
                            review_due_at__lte=timezone.now() + timedelta(days=14)
                        ).count(),
                        "severity": "info",
                        "url": "/documents",
                    },
                ],
            }
        elif user.has_role("Professor"):
            classes = AcademicClass.objects.filter(
                professor=user, is_active=True
            ).select_related("course")
            today_classes = classes.filter(weekday=timezone.localdate().isoweekday())
            enrolled = classes.aggregate(value=Count("enrollments"))["value"] or 0
            graded_students = (
                Grade.objects.filter(academic_class__professor=user)
                .values("academic_class", "student")
                .count()
            )
            data = {
                **common,
                "scope": "professor",
                "headline": "Teaching workspace",
                "classes": classes.count(),
                "upcoming_exams": Exam.objects.filter(
                    academic_class__professor=user, scheduled_at__gte=timezone.now()
                ).count(),
                "grades_recorded": Grade.objects.filter(
                    academic_class__professor=user
                ).count(),
                "students": enrolled,
                "ungraded": max(enrolled - graded_students, 0),
                "today": [
                    {
                        "id": item.pk,
                        "code": item.course.code,
                        "title": item.course.title,
                        "start_time": item.start_time,
                        "end_time": item.end_time,
                        "location": item.location,
                    }
                    for item in today_classes
                ],
                "class_performance": [
                    {
                        "id": item["academic_class"],
                        "course": item["academic_class__course__code"],
                        "average": float(item["average"])
                        if item["average"] is not None
                        else None,
                        "graded": item["graded"],
                    }
                    for item in Grade.objects.filter(academic_class__professor=user)
                    .values("academic_class", "academic_class__course__code")
                    .annotate(average=Avg("score"), graded=Count("id"))
                ],
            }
        else:
            classes = (
                AcademicClass.objects.filter(enrollments__student=user, is_active=True)
                .distinct()
                .select_related("course")
            )
            progress, recommendations = AcademicRecommendationService().build(user)
            grade_trend = [
                {
                    "course": item.academic_class.course.code,
                    "score": float(item.score),
                    "updated_at": item.updated_at,
                }
                for item in Grade.objects.filter(student=user)
                .select_related("academic_class__course")
                .order_by("updated_at")
            ]
            data = {
                **common,
                "scope": "student",
                "headline": "Your academic momentum",
                "classes": classes.count(),
                "upcoming_exams": Exam.objects.filter(
                    academic_class__enrollments__student=user,
                    scheduled_at__gte=timezone.now(),
                )
                .distinct()
                .count(),
                "grades": Grade.objects.filter(student=user).count(),
                "degree_progress": progress,
                "recommendations": recommendations[:4],
                "grade_trend": grade_trend,
                "today": [
                    {
                        "id": item.pk,
                        "code": item.course.code,
                        "title": item.course.title,
                        "start_time": item.start_time,
                        "end_time": item.end_time,
                        "location": item.location,
                    }
                    for item in classes.filter(
                        weekday=timezone.localdate().isoweekday()
                    )
                ],
            }
        return success(data)


class AIAnalyticsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_system_permission("reports.view_all"):
            raise PermissionDenied()
        total = Question.objects.count()
        responses = QuestionResponse.objects.select_related(
            "question"
        ).prefetch_related("sources")
        documented = responses.filter(is_documented=True).count()
        escalated = Question.objects.filter(status=Question.Status.ESCALATED).count()
        source_counts = Counter()
        for response in responses:
            for document in response.sources.all():
                source_counts[(document.pk, document.title)] += 1
        categories = dict(
            Question.objects.values_list("category").annotate(total=Count("id"))
        )
        confidence_bands = {
            "high": responses.filter(confidence__gte=0.8).count(),
            "medium": responses.filter(
                confidence__gte=0.55, confidence__lt=0.8
            ).count(),
            "low": responses.filter(confidence__lt=0.55).count(),
        }
        return success(
            {
                "total_questions": total,
                "answered": Question.objects.filter(
                    status=Question.Status.ANSWERED
                ).count(),
                "escalated": escalated,
                "failed": Question.objects.filter(
                    status=Question.Status.FAILED
                ).count(),
                "documented_rate": round(documented / responses.count() * 100, 1)
                if responses.count()
                else 0,
                "escalation_rate": round(escalated / total * 100, 1) if total else 0,
                "average_confidence": responses.aggregate(value=Avg("confidence"))[
                    "value"
                ],
                "confidence_bands": confidence_bands,
                "categories": categories,
                "top_sources": [
                    {"document_id": key[0], "title": key[1], "uses": value}
                    for key, value in source_counts.most_common(8)
                ],
                "trend": _daily_counts(Question.objects.all(), 14),
            }
        )


class AuditLogListView(PaginationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        if not request.user.has_system_permission("audit.view"):
            raise PermissionDenied()
        qs = AuditLog.objects.select_related("actor")
        action = request.query_params.get("action")
        actor = request.query_params.get("actor")
        entity_type = request.query_params.get("entity_type")
        if action:
            qs = qs.filter(action__icontains=action)
        if actor:
            qs = qs.filter(
                Q(actor__username__icontains=actor) | Q(actor__email__icontains=actor)
            )
        if entity_type:
            qs = qs.filter(entity_type__iexact=entity_type)
        return self.paginate(request, qs, AuditLogSerializer)
