from django.db import transaction
from .decorators import audited
from .models import Document

class DocumentService:
    @staticmethod
    @transaction.atomic
    @audited("document.created")
    def create(*, actor, request=None, allowed_roles=None, **data):
        document = Document.objects.create(created_by=actor, **data)
        if allowed_roles is not None:
            document.allowed_roles.set(allowed_roles)
        return document

    @staticmethod
    @transaction.atomic
    @audited("document.updated")
    def update(document, *, actor, request=None, allowed_roles=None, **data):
        for field, value in data.items(): setattr(document, field, value)
        document.save()
        if allowed_roles is not None: document.allowed_roles.set(allowed_roles)
        return document

    @staticmethod
    @audited("document.archived")
    def archive(document, *, actor, request=None):
        document.archive()
        return document
