from django.urls import path

from .views import DocumentDetailView, DocumentListCreateView, DocumentSearchView

urlpatterns = [
    path("documents", DocumentListCreateView.as_view(), name="documents"),
    path("documents/search", DocumentSearchView.as_view(), name="document-search"),
    path("documents/<int:pk>", DocumentDetailView.as_view(), name="document-detail"),
]
