"""Declares top-level API and administrative URL routes for the Django project."""

from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/v1/", include("apps.core.urls")),
    path("api/v1/", include("apps.accounts.urls")),
    path("api/v1/", include("apps.documents.urls")),
    path("api/v1/", include("apps.qa.urls")),
    path("api/v1/", include("apps.notifications.urls")),
    path("api/v1/", include("apps.workflows.urls")),
    path("api/v1/", include("apps.academics.urls")),
    path("api/v1/", include("apps.reports.urls")),
    path("api/v1/", include("apps.experience.urls")),
]
