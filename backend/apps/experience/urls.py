"""Declares API routes for user experience preferences, feedback, search, and calendar features."""

from django.urls import path

from .views import (
    ActivityFeedView,
    CalendarView,
    FeedbackListCreateView,
    FeedbackManageView,
    GlobalSearchView,
    PreferenceView,
)

urlpatterns = [
    path(
        "experience/preferences",
        PreferenceView.as_view(),
        name="experience-preferences",
    ),
    path("search", GlobalSearchView.as_view(), name="global-search"),
    path("calendar", CalendarView.as_view(), name="calendar"),
    path("activity-feed", ActivityFeedView.as_view(), name="activity-feed"),
    path("feedback", FeedbackListCreateView.as_view(), name="feedback"),
    path("feedback/<int:pk>", FeedbackManageView.as_view(), name="feedback-manage"),
]
