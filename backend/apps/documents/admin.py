"""Registers knowledge documents, versions, extraction, and governance models and controls for Django administration."""

from django.contrib import admin

from .models import Document

admin.site.register(Document)
