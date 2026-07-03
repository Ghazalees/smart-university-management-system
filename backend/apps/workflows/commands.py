"""Defines explicit command objects for state-changing workflows operations."""

from dataclasses import dataclass

from django.db import transaction
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from .models import WorkflowRequest
from .observers import WorkflowEvent, WorkflowEventPublisher


TRANSITIONS = {
    "submit": {
        WorkflowRequest.Status.DRAFT: WorkflowRequest.Status.PENDING,
        WorkflowRequest.Status.NEEDS_REVISION: WorkflowRequest.Status.PENDING,
    },
    "start_review": {
        WorkflowRequest.Status.PENDING: WorkflowRequest.Status.UNDER_REVIEW,
    },
    "request_revision": {
        WorkflowRequest.Status.UNDER_REVIEW: WorkflowRequest.Status.NEEDS_REVISION,
    },
    "approve": {
        WorkflowRequest.Status.UNDER_REVIEW: WorkflowRequest.Status.APPROVED,
    },
    "reject": {
        WorkflowRequest.Status.UNDER_REVIEW: WorkflowRequest.Status.REJECTED,
    },
}


@dataclass
class CreateWorkflowRequestCommand:
    requester: object
    validated_data: dict
    http_request: object = None

    @transaction.atomic
    def execute(self):
        request_obj = WorkflowRequest.objects.create(
            requester=self.requester, **self.validated_data
        )
        WorkflowEventPublisher.publish(
            WorkflowEvent(
                request=request_obj,
                event="created",
                actor=self.requester,
                to_status=request_obj.status,
                http_request=self.http_request,
            )
        )
        return request_obj


@dataclass
class AssignWorkflowRequestCommand:
    request_id: int
    assignee: object
    expected_version: int
    actor: object
    http_request: object = None

    @transaction.atomic
    def execute(self):
        request_obj = WorkflowRequest.objects.select_for_update().get(
            pk=self.request_id
        )
        if request_obj.version != self.expected_version:
            raise ValidationError(
                "This request was changed by another user. Refresh and try again."
            )
        if request_obj.status not in {
            WorkflowRequest.Status.PENDING,
            WorkflowRequest.Status.UNDER_REVIEW,
        }:
            raise ValidationError("Only active requests can be assigned.")
        request_obj.assigned_to = self.assignee
        request_obj.version += 1
        request_obj.save(update_fields=["assigned_to", "version", "updated_at"])
        WorkflowEventPublisher.publish(
            WorkflowEvent(
                request=request_obj,
                event="assigned",
                actor=self.actor,
                metadata={"assigned_to": self.assignee.pk},
                http_request=self.http_request,
            )
        )
        return request_obj


@dataclass
class TransitionWorkflowRequestCommand:
    request_id: int
    action: str
    expected_version: int
    actor: object
    note: str = ""
    http_request: object = None

    @transaction.atomic
    def execute(self):
        request_obj = WorkflowRequest.objects.select_for_update().get(
            pk=self.request_id
        )
        if request_obj.version != self.expected_version:
            raise ValidationError(
                "This request was changed by another user. Refresh and try again."
            )
        current = request_obj.status
        target = TRANSITIONS.get(self.action, {}).get(current)
        if not target:
            raise ValidationError(
                f"Action '{self.action}' is not allowed from status '{current}'."
            )
        if self.action == "submit" and self.actor.pk != request_obj.requester_id:
            raise ValidationError(
                "Only the requester can submit or resubmit this request."
            )
        if self.action != "submit" and not self.actor.has_system_permission(
            "workflows.review"
        ):
            raise ValidationError("You are not authorized to review requests.")
        request_obj.status = target
        request_obj.current_step = target
        request_obj.version += 1
        if self.action == "submit":
            request_obj.submitted_at = timezone.now()
        if self.action in {"approve", "reject"}:
            request_obj.decided_at = timezone.now()
            request_obj.decision_reason = self.note
        elif self.action == "request_revision":
            request_obj.decision_reason = self.note
        request_obj.save()
        WorkflowEventPublisher.publish(
            WorkflowEvent(
                request=request_obj,
                event=self.action,
                actor=self.actor,
                from_status=current,
                to_status=target,
                note=self.note,
                http_request=self.http_request,
            )
        )
        return request_obj
