"""Declares API routes for university requests, assignments, statuses, and revisions."""

from django.urls import path

from .views import (
    WorkflowAssignView,
    WorkflowRequestDetailView,
    WorkflowRequestListCreateView,
    WorkflowTransitionView,
    WorkflowTypeListView,
)

urlpatterns = [
    path("workflow-types", WorkflowTypeListView.as_view(), name="workflow-types"),
    path(
        "workflow-requests",
        WorkflowRequestListCreateView.as_view(),
        name="workflow-requests",
    ),
    path(
        "workflow-requests/<int:pk>",
        WorkflowRequestDetailView.as_view(),
        name="workflow-request-detail",
    ),
    path(
        "workflow-requests/<int:pk>/assign",
        WorkflowAssignView.as_view(),
        name="workflow-assign",
    ),
    path(
        "workflow-requests/<int:pk>/transition",
        WorkflowTransitionView.as_view(),
        name="workflow-transition",
    ),
]
