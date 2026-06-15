from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.responses import success

from .permissions import CanManageDocuments
from .repositories import DocumentAccessProxy, DocumentRepositoryFactory
from .serializers import DocumentSerializer
from .services import DocumentService


class DocumentListCreateView(APIView):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        return (
            [CanManageDocuments()]
            if self.request.method == "POST"
            else [IsAuthenticated()]
        )

    def get(self, request):
        qs = DocumentRepositoryFactory.create().search(
            request.user,
            request.query_params.get("keyword"),
            request.query_params.get("document_type"),
        )
        return success(DocumentSerializer(qs, many=True).data)

    def post(self, request):
        serializer = DocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        roles = data.pop("allowed_roles", [])
        document = DocumentService.create(
            actor=request.user, request=request, allowed_roles=roles, **data
        )
        return success(
            DocumentSerializer(document).data,
            "Document created",
            status.HTTP_201_CREATED,
        )


class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk):
        return DocumentAccessProxy().get(request.user, pk)

    def get_permissions(self):
        return (
            [CanManageDocuments()]
            if self.request.method in {"PATCH", "DELETE"}
            else [IsAuthenticated()]
        )

    def get(self, request, pk):
        return success(DocumentSerializer(self.get_object(request, pk)).data)

    def patch(self, request, pk):
        document = self.get_object(request, pk)
        serializer = DocumentSerializer(document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        roles = data.pop("allowed_roles", None)
        document = DocumentService.update(
            document, actor=request.user, request=request, allowed_roles=roles, **data
        )
        return success(DocumentSerializer(document).data, "Document updated")

    def delete(self, request, pk):
        document = self.get_object(request, pk)
        DocumentService.archive(document, actor=request.user, request=request)
        return success(message="Document archived")


class DocumentSearchView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = DocumentRepositoryFactory.create().search(
            request.user,
            request.query_params.get("keyword"),
            request.query_params.get("document_type"),
        )
        return success(DocumentSerializer(qs, many=True).data)
