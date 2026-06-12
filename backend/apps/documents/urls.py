from django.urls import path

from apps.documents.views import (
    DocumentDetailView,
    DocumentListCreateView,
    DocumentSearchView,
)

urlpatterns = [
    path("documents", DocumentListCreateView.as_view(), name="document-list-create"),
    path("documents/search", DocumentSearchView.as_view(), name="document-search"),
    path("documents/<int:document_id>", DocumentDetailView.as_view(), name="document-detail"),
]
