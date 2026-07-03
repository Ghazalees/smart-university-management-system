"""Declares API routes for role-aware dashboards and operational reports."""

from django.urls import path

from .views import AIAnalyticsView, AuditLogListView, DashboardView

urlpatterns = [
    path("reports/dashboard", DashboardView.as_view(), name="dashboard-report"),
    path("reports/ai-analytics", AIAnalyticsView.as_view(), name="ai-analytics"),
    path("audit-logs", AuditLogListView.as_view(), name="audit-logs"),
]
