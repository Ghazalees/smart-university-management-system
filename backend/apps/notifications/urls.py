"""Declares API routes for notification delivery and notification-center state."""

from django.urls import path

from .views import (
    NotificationActionView,
    NotificationBroadcastView,
    NotificationDigestView,
    NotificationListView,
    NotificationPreferenceView,
    NotificationReadAllView,
    NotificationReadView,
    NotificationUnreadCountView,
)

urlpatterns = [
    path("notifications", NotificationListView.as_view(), name="notifications"),
    path(
        "notifications/unread-count",
        NotificationUnreadCountView.as_view(),
        name="notification-count",
    ),
    path(
        "notifications/read-all",
        NotificationReadAllView.as_view(),
        name="notification-read-all",
    ),
    path(
        "notifications/preferences",
        NotificationPreferenceView.as_view(),
        name="notification-preferences",
    ),
    path(
        "notifications/digest",
        NotificationDigestView.as_view(),
        name="notification-digest",
    ),
    path(
        "notifications/<int:pk>/read",
        NotificationReadView.as_view(),
        name="notification-read",
    ),
    path(
        "notifications/<int:pk>/action",
        NotificationActionView.as_view(),
        name="notification-action",
    ),
    path(
        "notifications/broadcast",
        NotificationBroadcastView.as_view(),
        name="notification-broadcast",
    ),
]
