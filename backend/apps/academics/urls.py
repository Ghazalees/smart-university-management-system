"""Declares API routes for academic classes, enrollments, exams, grades, and progress."""

from django.urls import path

from .views import (
    AcademicClassDetailView,
    AcademicClassListView,
    AcademicRecommendationView,
    CourseListView,
    DegreeProgressView,
    EnrollmentListCreateView,
    ExamListCreateView,
    GradeListCreateView,
    ScheduleSuggestionView,
    StudentAcademicGoalView,
)

urlpatterns = [
    path("courses", CourseListView.as_view(), name="courses"),
    path("classes", AcademicClassListView.as_view(), name="classes"),
    path("classes/<int:pk>", AcademicClassDetailView.as_view(), name="class-detail"),
    path("enrollments", EnrollmentListCreateView.as_view(), name="enrollments"),
    path("exams", ExamListCreateView.as_view(), name="exams"),
    path("grades", GradeListCreateView.as_view(), name="grades"),
    path(
        "academics/degree-progress",
        DegreeProgressView.as_view(),
        name="degree-progress",
    ),
    path(
        "academics/recommendations",
        AcademicRecommendationView.as_view(),
        name="academic-recommendations",
    ),
    path("academics/goals", StudentAcademicGoalView.as_view(), name="academic-goals"),
    path(
        "academics/schedule-suggestions",
        ScheduleSuggestionView.as_view(),
        name="schedule-suggestions",
    ),
]
