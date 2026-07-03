"""Implements authenticated API endpoints for university requests, assignments, statuses, and revisions."""

from django.db.models import Q
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.accounts.permissions import HasSystemPermission
from apps.core.pagination import PaginationMixin
from apps.core.responses import success

from .commands import (
    AssignWorkflowRequestCommand,
    CreateWorkflowRequestCommand,
    TransitionWorkflowRequestCommand,
)
from .models import WorkflowRequest, WorkflowType
from .permissions import CanAccessWorkflowRequest
from .serializers import (
    WorkflowAssignSerializer,
    WorkflowRequestSerializer,
    WorkflowTransitionSerializer,
    WorkflowTypeSerializer,
)


class WorkflowTypeListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = WorkflowType.objects.filter(is_active=True).prefetch_related(
            "allowed_roles"
        )
        if not request.user.has_system_permission("workflows.configure"):
            qs = qs.filter(
                Q(allowed_roles__isnull=True)
                | Q(allowed_roles__in=request.user.roles.all())
            ).distinct()
        return success(WorkflowTypeSerializer(qs, many=True).data)

    def post(self, request):
        if not request.user.has_system_permission("workflows.configure"):
            raise PermissionDenied()
        serializer = WorkflowTypeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        workflow_type = serializer.save()
        return success(
            WorkflowTypeSerializer(workflow_type).data,
            "Workflow type created",
            status.HTTP_201_CREATED,
        )


class WorkflowRequestListCreateView(PaginationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = WorkflowRequest.objects.select_related(
            "request_type", "requester", "assigned_to", "requester__profile"
        ).prefetch_related("history")
        if not request.user.has_system_permission("workflows.view_all"):
            qs = qs.filter(Q(requester=request.user) | Q(assigned_to=request.user))
        status_value = request.query_params.get("status")
        request_type = request.query_params.get("type")
        search = request.query_params.get("search", "").strip()
        if status_value:
            qs = qs.filter(status=status_value)
        if request_type:
            qs = qs.filter(request_type__code=request_type)
        if search:
            qs = qs.filter(
                Q(request_number__icontains=search)
                | Q(title__icontains=search)
                | Q(requester__username__icontains=search)
            )
        return self.paginate(
            request,
            qs,
            WorkflowRequestSerializer,
            context={"request": request},
        )

    def post(self, request):
        if not request.user.has_system_permission("workflows.create"):
            raise PermissionDenied()
        serializer = WorkflowRequestSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        request_obj = CreateWorkflowRequestCommand(
            request.user, serializer.validated_data, request
        ).execute()
        return success(
            WorkflowRequestSerializer(request_obj, context={"request": request}).data,
            "Request draft created",
            status.HTTP_201_CREATED,
        )


class WorkflowRequestDetailView(APIView):
    permission_classes = [IsAuthenticated, CanAccessWorkflowRequest]

    def get_object(self, request, pk):
        from django.shortcuts import get_object_or_404

        obj = get_object_or_404(
            WorkflowRequest.objects.select_related(
                "request_type", "requester", "assigned_to", "requester__profile"
            ).prefetch_related("history"),
            pk=pk,
        )
        self.check_object_permissions(request, obj)
        return obj

    def get(self, request, pk):
        return success(
            WorkflowRequestSerializer(
                self.get_object(request, pk), context={"request": request}
            ).data
        )

    def patch(self, request, pk):
        obj = self.get_object(request, pk)
        if obj.requester_id != request.user.id or obj.status not in {
            WorkflowRequest.Status.DRAFT,
            WorkflowRequest.Status.NEEDS_REVISION,
        }:
            raise PermissionDenied(
                "Only editable requests owned by you can be changed."
            )
        serializer = WorkflowRequestSerializer(
            obj, data=request.data, partial=True, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(version=obj.version + 1)
        return success(serializer.data, "Request updated")


class WorkflowAssignView(APIView):
    permission_classes = [HasSystemPermission]
    required_permission = "workflows.review"

    def post(self, request, pk):
        serializer = WorkflowAssignSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = AssignWorkflowRequestCommand(
            pk,
            serializer.validated_data["assigned_to"],
            serializer.validated_data["expected_version"],
            request.user,
            request,
        ).execute()
        return success(WorkflowRequestSerializer(obj).data, "Request assigned")


class WorkflowTransitionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        serializer = WorkflowTransitionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        obj = TransitionWorkflowRequestCommand(
            request_id=pk,
            actor=request.user,
            http_request=request,
            **serializer.validated_data,
        ).execute()
        return success(WorkflowRequestSerializer(obj).data, "Request status updated")
