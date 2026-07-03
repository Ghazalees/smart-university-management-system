"""Implements authenticated API endpoints for notification delivery and notification-center state."""

from collections import Counter
from datetime import timedelta

from django.db.models import Q
from django.utils import timezone
from rest_framework import status
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import HasSystemPermission
from apps.core.pagination import PaginationMixin
from apps.core.responses import success

from .models import Notification, NotificationPreference
from .serializers import (
    NotificationActionSerializer,
    NotificationCreateSerializer,
    NotificationPreferenceSerializer,
    NotificationSerializer,
)
from .services import NotificationService


class NotificationListView(PaginationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Notification.objects.filter(recipient=request.user)
        unread = request.query_params.get("unread")
        category = request.query_params.get("category")
        priority = request.query_params.get("priority")
        pinned = request.query_params.get("pinned")
        include_snoozed = request.query_params.get("include_snoozed") == "true"
        if not include_snoozed:
            qs = qs.filter(
                Q(snoozed_until__isnull=True) | Q(snoozed_until__lte=timezone.now())
            )
        if unread == "true":
            qs = qs.filter(read_at__isnull=True)
        elif unread == "false":
            qs = qs.filter(read_at__isnull=False)
        if category:
            qs = qs.filter(category=category)
        if priority:
            qs = qs.filter(priority=priority)
        if pinned == "true":
            qs = qs.filter(pinned_at__isnull=False)
        qs = qs.order_by("-pinned_at", "-created_at")
        return self.paginate(request, qs, NotificationSerializer)


class NotificationUnreadCountView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        count = (
            Notification.objects.filter(recipient=request.user, read_at__isnull=True)
            .filter(
                Q(snoozed_until__isnull=True) | Q(snoozed_until__lte=timezone.now())
            )
            .count()
        )
        return success({"count": count})


class NotificationReadView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from django.shortcuts import get_object_or_404

        notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
        NotificationService.mark_read(notification)
        return success(NotificationSerializer(notification).data, "Notification read")


class NotificationActionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        from django.shortcuts import get_object_or_404

        obj = get_object_or_404(Notification, pk=pk, recipient=request.user)
        serializer = NotificationActionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        action = serializer.validated_data["action"]
        now = timezone.now()
        if action == "pin":
            obj.pinned_at = now
        elif action == "unpin":
            obj.pinned_at = None
        elif action == "snooze":
            until = serializer.validated_data["snoozed_until"]
            if until <= now or until > now + timedelta(days=30):
                raise ValidationError(
                    {"snoozed_until": "Snooze must be within the next 30 days."}
                )
            obj.snoozed_until = until
        elif action == "unsnooze":
            obj.snoozed_until = None
        elif action == "read":
            obj.read_at = now
        elif action == "unread":
            obj.read_at = None
        obj.save(update_fields=["pinned_at", "snoozed_until", "read_at", "updated_at"])
        return success(NotificationSerializer(obj).data, "Notification updated")


class NotificationReadAllView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updated = Notification.objects.filter(
            recipient=request.user, read_at__isnull=True
        ).update(read_at=timezone.now(), updated_at=timezone.now())
        return success({"updated": updated}, "All notifications marked as read")


class NotificationPreferenceView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, user):
        obj, _ = NotificationPreference.objects.get_or_create(
            user=user,
            defaults={
                "enabled_categories": [c[0] for c in Notification.Category.choices]
            },
        )
        return obj

    def get(self, request):
        return success(
            NotificationPreferenceSerializer(self.get_object(request.user)).data
        )

    def patch(self, request):
        obj = self.get_object(request.user)
        serializer = NotificationPreferenceSerializer(
            obj, data=request.data, partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return success(serializer.data, "Notification preferences updated")


class NotificationDigestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        period = request.query_params.get("period", "daily")
        delta = timedelta(days=7 if period == "weekly" else 1)
        qs = Notification.objects.filter(
            recipient=request.user, created_at__gte=timezone.now() - delta
        ).order_by("-created_at")
        categories = Counter(qs.values_list("category", flat=True))
        urgent = qs.filter(priority="urgent").count()
        return success(
            {
                "period": period,
                "total": qs.count(),
                "unread": qs.filter(read_at__isnull=True).count(),
                "urgent": urgent,
                "categories": dict(categories),
                "highlights": NotificationSerializer(qs[:8], many=True).data,
            }
        )


class NotificationBroadcastView(APIView):
    permission_classes = [HasSystemPermission]
    required_permission = "notifications.broadcast"

    def post(self, request):
        serializer = NotificationCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        notifications = NotificationService.broadcast(
            title=data["title"],
            message=data["message"],
            category=data["category"],
            link=data.get("link", ""),
            recipients=data.get("recipient_ids", []),
            roles=data.get("role_ids", []),
            actor=request.user,
            request=request,
            metadata={"priority": data.get("priority", "normal")},
            priority=data.get("priority", "normal"),
        )
        return success(
            {"created": len(notifications)},
            "Notification published",
            status.HTTP_201_CREATED,
        )
