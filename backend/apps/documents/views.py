from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.accounts.permissions import BearerTokenAuthentication
from apps.documents.permissions import CanManageDocuments
from apps.documents.serializers import DocumentSerializer
from apps.documents.services import DocumentService


class DocumentListCreateView(APIView):
    """Handle GET/POST /api/v1/documents."""

    authentication_classes = [BearerTokenAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return active documents visible to the authenticated user."""
        documents = DocumentService.visible_queryset_for_user(request.user)
        serializer = DocumentSerializer(documents, many=True)
        return Response(
            {"success": True, "data": serializer.data},
            status=status.HTTP_200_OK,
        )

    def post(self, request):
        """Create a new document for authorized document managers."""
        self.check_permissions(request)
        CanManageDocuments().has_permission(request, self) or self.permission_denied(
            request,
            message="Only administrative staff or the university president can create documents.",
        )

        serializer = DocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        document = DocumentService.create_document(
            data=serializer.validated_data,
            user=request.user,
        )
        return Response(
            {"success": True, "data": DocumentSerializer(document).data},
            status=status.HTTP_201_CREATED,
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
        return Response(
            {"success": True, "data": DocumentSerializer(document).data},
            status=status.HTTP_200_OK,
        )

    def patch(self, request, document_id):
        """Partially update a document for authorized document managers."""
        CanManageDocuments().has_permission(request, self) or self.permission_denied(
            request,
            message="Only administrative staff or the university president can update documents.",
        )
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
        return Response(
            {"success": True, "data": DocumentSerializer(updated).data},
            status=status.HTTP_200_OK,
        )

    def delete(self, request, document_id):
        """Archive a document for authorized document managers."""
        CanManageDocuments().has_permission(request, self) or self.permission_denied(
            request,
            message="Only administrative staff or the university president can archive documents.",
        )
        document = DocumentService.get_visible_document_or_403(
            document_id=document_id,
            user=request.user,
        )
        DocumentService.archive_document(document=document, user=request.user)
        return Response(
            {"success": True, "message": "Document archived successfully."},
            status=status.HTTP_200_OK,
        )
