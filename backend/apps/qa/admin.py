"""Registers grounded question answering, retrieval, and AI orchestration models and controls for Django administration."""

from django.contrib import admin

from .models import Question, QuestionHistory, QuestionResponse

admin.site.register([Question, QuestionHistory, QuestionResponse])
