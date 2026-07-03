"""Declares API routes for knowledge documents, versions, extraction, and governance."""

from django.urls import path

from .views import (
    DocumentDetailView,
    DocumentExportView,
    DocumentImportView,
    DocumentListCreateView,
    DocumentPublishView,
    DocumentReindexView,
    DocumentRestoreView,
    DocumentSearchView,
    DocumentUploadView,
    DocumentVersionListView,
    DocumentVersionRestoreView,
)

urlpatterns = [
    path("documents", DocumentListCreateView.as_view(), name="documents"),
    path("documents/search", DocumentSearchView.as_view(), name="document-search"),
    path("documents/export", DocumentExportView.as_view(), name="document-export"),
    path("documents/import", DocumentImportView.as_view(), name="document-import"),
    path("documents/upload", DocumentUploadView.as_view(), name="document-upload"),
    path("documents/<int:pk>", DocumentDetailView.as_view(), name="document-detail"),
    path(
        "documents/<int:pk>/publish",
        DocumentPublishView.as_view(),
        name="document-publish",
    ),
    path(
        "documents/<int:pk>/restore",
        DocumentRestoreView.as_view(),
        name="document-restore",
    ),
    path(
        "documents/<int:pk>/reindex",
        DocumentReindexView.as_view(),
        name="document-reindex",
    ),
    path(
        "documents/<int:pk>/versions",
        DocumentVersionListView.as_view(),
        name="document-versions",
    ),
    path(
        "documents/<int:pk>/versions/<int:version_number>/restore",
        DocumentVersionRestoreView.as_view(),
        name="document-version-restore",
    ),
]
