"""Declares API routes for shared platform infrastructure and cross-cutting utilities."""

from django.urls import path

from .views import HealthView

urlpatterns = [path("health", HealthView.as_view(), name="health")]
