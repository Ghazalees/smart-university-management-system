from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.responses import api_success
from apps.accounts.permissions import BearerTokenAuthentication
from apps.documents.permissions import CanManageDocuments
from apps.documents.serializers import DocumentQuerySerializer, DocumentSerializer
from apps.documents.services import DocumentService


def _ensure_document_manager(request, view, action):
    """Enforce document manager permission with a consistent message."""
    if not CanManageDocuments().has_permission(request, view):
        view.permission_denied(
            request,
            message=f"Only administrative staff or the university president can {action} documents.",
        )


class DocumentListCreateView(APIView):
    """Handle GET/POST /api/v1/documents."""

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return active documents visible to the authenticated user."""
        query_serializer = DocumentQuerySerializer(data=request.query_params)
        query_serializer.is_valid(raise_exception=True)
        documents = DocumentService.visible_queryset_for_user(
            request.user,
            filters=query_serializer.validated_data,
        )
        serializer = DocumentSerializer(documents, many=True)
        return api_success(
            message="Documents retrieved successfully.",
            data=serializer.data,
            meta={"count": len(serializer.data)},
        )

    def post(self, request):
        """Create a new document for authorized document managers."""
        _ensure_document_manager(request, self, "create")
        serializer = DocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = DocumentService.create_document(
            data=serializer.validated_data,
            user=request.user,
        )
        return api_success(
            message="Document created successfully.",
            data=DocumentSerializer(document).data,
            status_code=status.HTTP_201_CREATED,
        )


class DocumentDetailView(APIView):
    """Handle GET/PATCH/DELETE /api/v1/documents/<id>."""

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request, document_id):
        """Return one accessible document."""
        document = DocumentService.get_visible_document_or_403(
            document_id=document_id,
            user=request.user,
        )
        return api_success(
            message="Document retrieved successfully.",
            data=DocumentSerializer(document).data,
        )

    def patch(self, request, document_id):
        """Partially update a document for authorized document managers."""
        _ensure_document_manager(request, self, "update")
        document = DocumentService.get_visible_document_or_403(
            document_id=document_id,
            user=request.user,
        )
        serializer = DocumentSerializer(document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        updated = DocumentService.update_document(
            document=document,
            data=serializer.validated_data,
            user=request.user,
        )
        return api_success(
            message="Document updated successfully.",
            data=DocumentSerializer(updated).data,
        )

    def delete(self, request, document_id):
        """Archive a document for authorized document managers."""
        _ensure_document_manager(request, self, "archive")
        document = DocumentService.get_visible_document_or_403(
            document_id=document_id,
            user=request.user,
        )
        DocumentService.archive_document(document=document, user=request.user)
        return api_success(message="Document archived successfully.")
