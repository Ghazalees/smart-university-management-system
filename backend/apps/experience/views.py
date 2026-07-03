"""Implements authenticated API endpoints for user experience preferences, feedback, search, and calendar features."""

from datetime import timedelta

from django.utils import timezone
from django.utils.dateparse import parse_datetime
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import HasSystemPermission
from apps.core.pagination import PaginationMixin
from apps.core.responses import success
from apps.core.services import AuditEvent, AuditService

from .models import Feedback, UserExperiencePreference
from .serializers import (
    FeedbackManageSerializer,
    FeedbackSerializer,
    UserExperiencePreferenceSerializer,
)
from .services import ActivityFeedService, CalendarBuilder, GlobalSearchRepository


class PreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, user):
        obj, _ = UserExperiencePreference.objects.get_or_create(user=user)
        return obj

    def get(self, request):
        return success(
            UserExperiencePreferenceSerializer(self.get_object(request.user)).data
        )

    def patch(self, request):
        obj = self.get_object(request.user)
        serializer = UserExperiencePreferenceSerializer(
            obj, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditService.record(
            AuditEvent("experience.preferences_updated", "User", request.user.pk),
            actor=request.user,
            request=request,
        )
        return success(serializer.data, "Experience preferences updated")


class GlobalSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "").strip()
        if len(query) < 2:
            raise ValidationError({"q": "Enter at least two characters."})
        try:
            limit = min(max(int(request.query_params.get("limit", 6)), 1), 20)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                {"limit": "Limit must be an integer between 1 and 20."}
            ) from exc
        results = GlobalSearchRepository().search(request.user, query, limit)
        return success({"query": query, "results": [item.__dict__ for item in results]})


class CalendarView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        now = timezone.now()
        start_value = request.query_params.get("start")
        end_value = request.query_params.get("end")
        start = parse_datetime(start_value) if start_value else now - timedelta(days=7)
        end = parse_datetime(end_value) if end_value else now + timedelta(days=45)
        if start_value and start is None:
            raise ValidationError(
                {"start": "Use a valid ISO-8601 date and URL-encode timezone offsets."}
            )
        if end_value and end is None:
            raise ValidationError(
                {"end": "Use a valid ISO-8601 date and URL-encode timezone offsets."}
            )
        if timezone.is_naive(start):
            start = timezone.make_aware(start)
        if timezone.is_naive(end):
            end = timezone.make_aware(end)
        if end <= start or end - start > timedelta(days=180):
            raise ValidationError(
                "Calendar range must be positive and at most 180 days."
            )
        events = (
            CalendarBuilder(request.user, start, end)
            .add_classes()
            .add_exams()
            .add_workflows()
            .add_document_reviews()
            .build()
        )
        return success({"start": start, "end": end, "events": events})


class ActivityFeedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            limit = min(max(int(request.query_params.get("limit", 20)), 1), 100)
        except (TypeError, ValueError) as exc:
            raise ValidationError(
                {"limit": "Limit must be an integer between 1 and 100."}
            ) from exc
        return success({"items": ActivityFeedService.for_user(request.user, limit)})


class FeedbackListCreateView(PaginationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Feedback.objects.select_related("created_by", "assigned_to")
        if not request.user.has_system_permission("feedback.manage"):
            qs = qs.filter(created_by=request.user)
        status_value = request.query_params.get("status")
        feedback_type = request.query_params.get("type")
        if status_value:
            qs = qs.filter(status=status_value)
        if feedback_type:
            qs = qs.filter(feedback_type=feedback_type)
        return self.paginate(request, qs, FeedbackSerializer)

    def post(self, request):
        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save(created_by=request.user)
        AuditService.record(
            AuditEvent(
                "feedback.created", "Feedback", obj.pk, {"type": obj.feedback_type}
            ),
            actor=request.user,
            request=request,
        )
        return success(
            FeedbackSerializer(obj).data, "Feedback submitted", status.HTTP_201_CREATED
        )


class FeedbackManageView(APIView):
    permission_classes = [HasSystemPermission]
    required_permission = "feedback.manage"

    def patch(self, request, pk):
        from django.shortcuts import get_object_or_404

        obj = get_object_or_404(Feedback, pk=pk)
        serializer = FeedbackManageSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditService.record(
            AuditEvent("feedback.updated", "Feedback", obj.pk, {"status": obj.status}),
            actor=request.user,
            request=request,
        )
        return success(FeedbackSerializer(obj).data, "Feedback updated")
