"""Implements authenticated API endpoints for knowledge documents, versions, extraction, and governance."""

import csv
import io
import json

from django.db.models import Count
from django.http import HttpResponse
from rest_framework import status
from rest_framework.exceptions import MethodNotAllowed, ValidationError
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from apps.core.pagination import PaginationMixin
from apps.core.responses import success

from .extraction import extract_uploaded_text
from .models import Document, DocumentVersion
from .permissions import CanManageDocuments
from .repositories import DocumentAccessProxy, DocumentRepositoryFactory
from .serializers import DocumentSerializer, DocumentVersionSerializer
from .services import DocumentService, DocumentVersionService


class DocumentListCreateView(PaginationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get_permissions(self):
        return [CanManageDocuments()] if self.request.method == "POST" else [AllowAny()]

    def get(self, request):
        include_archived = (
            request.query_params.get("include_archived") == "true"
            and getattr(request.user, "is_authenticated", False)
            and request.user.has_system_permission("documents.manage")
        )
        qs = (
            DocumentRepositoryFactory.create()
            .search(
                request.user,
                request.query_params.get("search")
                or request.query_params.get("keyword"),
                request.query_params.get("document_type"),
                request.query_params.get("status"),
                request.query_params.get("access_level"),
                include_archived,
            )
            .select_related("created_by", "last_updated_by", "review_owner")
            .annotate(version_count=Count("versions"))
        )
        governance = request.query_params.get("governance")
        from django.utils import timezone

        if governance == "expired":
            qs = qs.filter(expires_at__lte=timezone.now())
        elif governance == "review_due":
            qs = qs.filter(review_due_at__lte=timezone.now())
        ordering = request.query_params.get("ordering", "-updated_at")
        if ordering not in {
            "title",
            "-title",
            "updated_at",
            "-updated_at",
            "created_at",
            "-created_at",
            "expires_at",
            "-expires_at",
        }:
            ordering = "-updated_at"
        return self.paginate(request, qs.order_by(ordering), DocumentSerializer)

    def post(self, request):
        serializer = DocumentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        roles = data.pop("allowed_roles", [])
        change_summary = data.pop("change_summary", "Initial version")
        document = DocumentService.create(
            actor=request.user,
            request=request,
            allowed_roles=roles,
            change_summary=change_summary,
            **data,
        )
        return success(
            DocumentSerializer(document).data,
            "Document created",
            status.HTTP_201_CREATED,
        )


class DocumentDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request, pk, include_archived=False):
        return DocumentAccessProxy().get(
            request.user, pk, include_archived=include_archived
        )

    def get_permissions(self):
        return (
            [CanManageDocuments()]
            if self.request.method in {"PATCH", "DELETE"}
            else [AllowAny()]
        )

    def get(self, request, pk):
        obj = self.get_object(request, pk)
        obj.version_count = obj.versions.count()
        return success(DocumentSerializer(obj).data)

    def patch(self, request, pk):
        document = self.get_object(request, pk, include_archived=True)
        serializer = DocumentSerializer(document, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        roles = data.pop("allowed_roles", None)
        change_summary = data.pop("change_summary", "")
        document = DocumentService.update(
            document,
            actor=request.user,
            request=request,
            allowed_roles=roles,
            change_summary=change_summary,
            **data,
        )
        document.version_count = document.versions.count()
        return success(DocumentSerializer(document).data, "Document updated")

    def delete(self, request, pk):
        document = self.get_object(request, pk, include_archived=True)
        DocumentService.archive(document, actor=request.user, request=request)
        return success(message="Document archived")


class DocumentPublishView(APIView):
    permission_classes = [CanManageDocuments]

    def post(self, request, pk):
        document = DocumentAccessProxy().get(request.user, pk, include_archived=True)
        document = DocumentService.publish(
            document, actor=request.user, request=request
        )
        return success(DocumentSerializer(document).data, "Document published")


class DocumentRestoreView(APIView):
    permission_classes = [CanManageDocuments]

    def post(self, request, pk):
        document = DocumentAccessProxy().get(request.user, pk, include_archived=True)
        document = DocumentService.restore(
            document, actor=request.user, request=request
        )
        return success(DocumentSerializer(document).data, "Document restored as draft")


class DocumentReindexView(APIView):
    permission_classes = [CanManageDocuments]

    def post(self, request, pk):
        document = DocumentAccessProxy().get(request.user, pk, include_archived=True)
        document.mark_indexed()
        return success(DocumentSerializer(document).data, "Knowledge index updated")


class DocumentVersionListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        include_archived = request.user.has_system_permission("documents.manage")
        document = DocumentAccessProxy().get(
            request.user, pk, include_archived=include_archived
        )
        return success(
            DocumentVersionSerializer(
                document.versions.select_related("created_by"), many=True
            ).data
        )


class DocumentVersionRestoreView(APIView):
    permission_classes = [CanManageDocuments]

    def post(self, request, pk, version_number):
        document = DocumentAccessProxy().get(request.user, pk, include_archived=True)
        try:
            version = document.versions.get(version_number=version_number)
        except DocumentVersion.DoesNotExist as exc:
            raise ValidationError("Document version not found.") from exc
        document = DocumentVersionService.restore(version, request.user)
        return success(
            DocumentSerializer(document).data, f"Version {version_number} restored"
        )


class DocumentExportView(APIView):
    permission_classes = [CanManageDocuments]

    def get(self, request):
        fmt = request.query_params.get("format", "json").lower()
        qs = Document.objects.prefetch_related("allowed_roles").order_by("id")
        rows = [DocumentSerializer(item).data for item in qs]
        if fmt == "json":
            response = HttpResponse(
                json.dumps(rows, ensure_ascii=False, default=str, indent=2),
                content_type="application/json; charset=utf-8",
            )
            response["Content-Disposition"] = 'attachment; filename="documents.json"'
            return response
        if fmt != "csv":
            raise ValidationError({"format": "Supported formats are json and csv."})
        stream = io.StringIO()
        fields = [
            "title",
            "document_type",
            "content",
            "access_level",
            "status",
            "knowledge_enabled",
            "effective_from",
            "expires_at",
            "review_due_at",
            "tags",
        ]
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        for row in rows:
            writer.writerow(
                {
                    field: json.dumps(row[field], ensure_ascii=False)
                    if field == "tags"
                    else row[field]
                    for field in fields
                }
            )
        response = HttpResponse(
            stream.getvalue(), content_type="text/csv; charset=utf-8"
        )
        response["Content-Disposition"] = 'attachment; filename="documents.csv"'
        return response


class DocumentImportView(APIView):
    permission_classes = [CanManageDocuments]

    def post(self, request):
        fmt = str(request.data.get("format", "json")).lower()
        raw = request.data.get("content")
        if fmt == "json":
            try:
                items = raw if isinstance(raw, list) else json.loads(raw or "[]")
            except (json.JSONDecodeError, TypeError) as exc:
                raise ValidationError(
                    {"content": "The JSON import payload is invalid."}
                ) from exc
        elif fmt == "csv":
            items = list(csv.DictReader(io.StringIO(raw or "")))
            for item in items:
                item["knowledge_enabled"] = str(
                    item.get("knowledge_enabled", "true")
                ).lower() in {"1", "true", "yes"}
                if item.get("tags"):
                    try:
                        item["tags"] = json.loads(item["tags"])
                    except json.JSONDecodeError:
                        item["tags"] = [
                            value.strip()
                            for value in item["tags"].split(",")
                            if value.strip()
                        ]
        else:
            raise ValidationError({"format": "Supported formats are json and csv."})
        if not isinstance(items, list) or len(items) > 500:
            raise ValidationError(
                "Import must contain a list of at most 500 documents."
            )
        created, errors = [], []
        for index, item in enumerate(items, start=1):
            serializer = DocumentSerializer(data=item)
            if not serializer.is_valid():
                errors.append({"row": index, "errors": serializer.errors})
                continue
            data = dict(serializer.validated_data)
            roles = data.pop("allowed_roles", [])
            data.pop("change_summary", None)
            obj = DocumentService.create(
                actor=request.user,
                request=request,
                allowed_roles=roles,
                change_summary="Imported",
                **data,
            )
            created.append(obj.pk)
        return success(
            {"created": len(created), "created_ids": created, "errors": errors},
            "Document import completed",
            status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class DocumentUploadView(APIView):
    permission_classes = [CanManageDocuments]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        uploaded_file = request.FILES.get("file")
        content = extract_uploaded_text(uploaded_file)

        raw_metadata = request.data.get("metadata", "{}")
        if isinstance(raw_metadata, str):
            try:
                metadata = json.loads(raw_metadata or "{}")
            except json.JSONDecodeError as exc:
                raise ValidationError(
                    {"metadata": "Upload metadata must be valid JSON."}
                ) from exc
        elif isinstance(raw_metadata, dict):
            metadata = dict(raw_metadata)
        else:
            raise ValidationError({"metadata": "Upload metadata must be an object."})

        if not isinstance(metadata, dict):
            raise ValidationError({"metadata": "Upload metadata must be an object."})

        filename = uploaded_file.name if uploaded_file else "Uploaded document"
        metadata["title"] = str(
            metadata.get("title") or filename.rsplit(".", 1)[0]
        ).strip()
        metadata["content"] = content
        metadata.setdefault("document_type", "other")
        metadata.setdefault("access_level", "authenticated")
        metadata.setdefault("status", "published")
        metadata.setdefault("knowledge_enabled", True)
        metadata.setdefault("tags", [])
        metadata.setdefault("change_summary", f"Uploaded from {filename}")

        serializer = DocumentSerializer(data=metadata)
        serializer.is_valid(raise_exception=True)
        data = dict(serializer.validated_data)
        roles = data.pop("allowed_roles", [])
        change_summary = data.pop("change_summary", f"Uploaded from {filename}")
        document = DocumentService.create(
            actor=request.user,
            request=request,
            allowed_roles=roles,
            change_summary=change_summary,
            **data,
        )
        document.version_count = document.versions.count()
        return success(
            DocumentSerializer(document).data,
            "File uploaded and added to governed knowledge",
            status.HTTP_201_CREATED,
        )


class DocumentSearchView(DocumentListCreateView):
    def post(self, request):
        raise MethodNotAllowed("POST")
