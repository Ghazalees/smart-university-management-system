"""Implements authenticated API endpoints for academic classes, enrollments, exams, grades, and progress."""

from django.db import transaction
from django.db.models import Avg, Count, Max, Min, Q
from rest_framework import status
from rest_framework.exceptions import PermissionDenied
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

from apps.core.pagination import PaginationMixin, StandardResultsSetPagination
from apps.core.responses import success
from apps.core.services import AuditEvent, AuditService
from apps.notifications.models import Notification
from apps.notifications.services import NotificationService

from .models import AcademicClass, Course, Enrollment, Exam, Grade, StudentAcademicGoal
from .services import (
    AcademicRecommendationService,
    DegreeProgressService,
    ScheduleSuggestionService,
)
from .serializers import (
    AcademicClassSerializer,
    CourseSerializer,
    EnrollmentSerializer,
    ExamSerializer,
    GradeSerializer,
    ScheduleSuggestionSerializer,
    StudentAcademicGoalSerializer,
)


def _class_queryset_for(user):
    qs = AcademicClass.objects.select_related("course", "professor").annotate(
        enrolled_count=Count("enrollments")
    )
    if user.has_system_permission("academics.manage"):
        return qs
    if user.has_role("Professor"):
        return qs.filter(professor=user)
    return qs.filter(enrollments__student=user).distinct()


class CourseListView(PaginationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Course.objects.filter(is_active=True)
        search = request.query_params.get("search", "").strip()
        if search:
            qs = qs.filter(Q(code__icontains=search) | Q(title__icontains=search))
        return self.paginate(request, qs, CourseSerializer)

    def post(self, request):
        if not request.user.has_system_permission("academics.manage"):
            raise PermissionDenied()
        serializer = CourseSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        course = serializer.save()
        return success(
            CourseSerializer(course).data, "Course created", status.HTTP_201_CREATED
        )


class AcademicClassListView(PaginationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = _class_queryset_for(request.user)
        term = request.query_params.get("term")
        if term:
            qs = qs.filter(term=term)
        return self.paginate(request, qs, AcademicClassSerializer)

    def post(self, request):
        if not (
            request.user.has_system_permission("academics.manage")
            or request.user.has_system_permission("classes.create")
        ):
            raise PermissionDenied()
        data = request.data.copy()
        if request.user.has_role(
            "Professor"
        ) and not request.user.has_system_permission("academics.manage"):
            data["professor"] = request.user.pk
        serializer = AcademicClassSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        obj = serializer.save()
        AuditService.record(
            AuditEvent("academic.class_created", "AcademicClass", obj.pk),
            actor=request.user,
            request=request,
        )
        return success(
            AcademicClassSerializer(obj).data, "Class created", status.HTTP_201_CREATED
        )


class AcademicClassDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, user, pk):
        from django.shortcuts import get_object_or_404

        return get_object_or_404(_class_queryset_for(user), pk=pk)

    def get(self, request, pk):
        obj = self.get_object(request.user, pk)
        can_view_report = (
            request.user.has_system_permission("academics.manage")
            or obj.professor_id == request.user.id
        )
        if not can_view_report:
            raise PermissionDenied()
        grade_queryset = Grade.objects.filter(academic_class=obj).select_related(
            "student"
        )
        aggregate = grade_queryset.aggregate(
            average=Avg("score"),
            minimum=Min("score"),
            maximum=Max("score"),
            graded_count=Count("id"),
        )
        grades_by_student = {grade.student_id: grade for grade in grade_queryset}
        enrollments = obj.enrollments.select_related("student").order_by(
            "student__first_name", "student__last_name", "student__username"
        )
        students = []
        for enrollment in enrollments:
            grade = grades_by_student.get(enrollment.student_id)
            students.append(
                {
                    "enrollment_id": enrollment.pk,
                    "student_id": enrollment.student_id,
                    "student_name": enrollment.student.get_full_name()
                    or enrollment.student.username,
                    "score": float(grade.score) if grade else None,
                    "feedback": grade.feedback if grade else "",
                    "graded_at": grade.updated_at if grade else None,
                    "has_grade": grade is not None,
                }
            )
        report = {
            "average": (
                float(aggregate["average"])
                if aggregate["average"] is not None
                else None
            ),
            "minimum": (
                float(aggregate["minimum"])
                if aggregate["minimum"] is not None
                else None
            ),
            "maximum": (
                float(aggregate["maximum"])
                if aggregate["maximum"] is not None
                else None
            ),
            "graded_count": aggregate["graded_count"],
            "ungraded_count": max(len(students) - aggregate["graded_count"], 0),
            "students": students,
        }
        return success({"class": AcademicClassSerializer(obj).data, "report": report})

    def patch(self, request, pk):
        obj = self.get_object(request.user, pk)
        can_manage_all = request.user.has_system_permission("academics.manage")
        if not (can_manage_all or obj.professor_id == request.user.id):
            raise PermissionDenied()
        data = request.data.copy()
        if not can_manage_all:
            data["professor"] = obj.professor_id
        serializer = AcademicClassSerializer(obj, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditService.record(
            AuditEvent("academic.class_updated", "AcademicClass", obj.pk),
            actor=request.user,
            request=request,
        )
        return success(serializer.data, "Class updated")


class EnrollmentPagination(StandardResultsSetPagination):
    max_page_size = 500


class EnrollmentListCreateView(PaginationMixin, APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = EnrollmentPagination

    def get(self, request):
        qs = Enrollment.objects.select_related("academic_class", "student")
        if not request.user.has_system_permission("academics.manage"):
            qs = qs.filter(
                Q(student=request.user) | Q(academic_class__professor=request.user)
            )
        class_id = request.query_params.get("class_id")
        if class_id:
            qs = qs.filter(academic_class_id=class_id)
        return self.paginate(request, qs, EnrollmentSerializer)

    def post(self, request):
        if not request.user.has_system_permission("academics.manage"):
            raise PermissionDenied()
        serializer = EnrollmentSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        enrollment = serializer.save()
        return success(
            EnrollmentSerializer(enrollment).data,
            "Student enrolled",
            status.HTTP_201_CREATED,
        )


class ExamListCreateView(PaginationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Exam.objects.select_related("academic_class", "academic_class__course")
        class_ids = _class_queryset_for(request.user).values_list("id", flat=True)
        qs = qs.filter(academic_class_id__in=class_ids)
        return self.paginate(request, qs, ExamSerializer)

    @transaction.atomic
    def post(self, request):
        serializer = ExamSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        academic_class = serializer.validated_data["academic_class"]
        if not (
            request.user.has_system_permission("academics.manage")
            or academic_class.professor_id == request.user.id
        ):
            raise PermissionDenied()
        exam = serializer.save()
        for student in academic_class.students.filter(is_active=True):
            NotificationService.send(
                recipient=student,
                title=f"New exam: {exam.title}",
                message=f"{academic_class.course.title} exam is scheduled for {exam.scheduled_at}.",
                category=Notification.Category.ACADEMIC,
                link="/academics/exams",
                actor=request.user,
            )
        return success(
            ExamSerializer(exam).data, "Exam scheduled", status.HTTP_201_CREATED
        )


class GradeListCreateView(PaginationMixin, APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        qs = Grade.objects.select_related(
            "academic_class", "academic_class__course", "student"
        )
        if request.user.has_system_permission("academics.manage"):
            pass
        elif request.user.has_role("Professor"):
            qs = qs.filter(academic_class__professor=request.user)
        else:
            qs = qs.filter(student=request.user)
        class_id = request.query_params.get("class_id")
        if class_id:
            qs = qs.filter(academic_class_id=class_id)
        return self.paginate(request, qs, GradeSerializer)

    @transaction.atomic
    def post(self, request):
        serializer = GradeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data
        grade, created = Grade.objects.update_or_create(
            academic_class=data["academic_class"],
            student=data["student"],
            defaults={
                "score": data["score"],
                "feedback": data.get("feedback", ""),
                "graded_by": request.user,
            },
        )
        NotificationService.send(
            recipient=grade.student,
            title="Grade updated",
            message=f"A grade for {grade.academic_class.course.title} is now available.",
            category=Notification.Category.ACADEMIC,
            link="/academics/grades",
            actor=request.user,
        )
        return success(
            GradeSerializer(grade).data,
            "Grade saved",
            status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )


class DegreeProgressView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = request.user
        student_id = request.query_params.get("student_id")
        if student_id and request.user.has_system_permission("academics.manage"):
            from apps.accounts.models import User
            from django.shortcuts import get_object_or_404

            student = get_object_or_404(User, pk=student_id)
        return success(DegreeProgressService.build(student))


class AcademicRecommendationView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        student = request.user
        student_id = request.query_params.get("student_id")
        if student_id and request.user.has_system_permission("academics.manage"):
            from apps.accounts.models import User
            from django.shortcuts import get_object_or_404

            student = get_object_or_404(User, pk=student_id)
        progress, recommendations = AcademicRecommendationService().build(student)
        return success({"progress": progress, "recommendations": recommendations})


class StudentAcademicGoalView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, user):
        obj, _ = StudentAcademicGoal.objects.get_or_create(student=user)
        return obj

    def get(self, request):
        return success(
            StudentAcademicGoalSerializer(self.get_object(request.user)).data
        )

    def patch(self, request):
        obj = self.get_object(request.user)
        serializer = StudentAcademicGoalSerializer(obj, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        AuditService.record(
            AuditEvent("academic.goal_updated", "StudentAcademicGoal", obj.pk),
            actor=request.user,
            request=request,
        )
        return success(serializer.data, "Academic goal updated")


class ScheduleSuggestionView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        if not (
            request.user.has_system_permission("academics.manage")
            or request.user.has_system_permission("classes.create")
        ):
            raise PermissionDenied()
        data = request.data.copy()
        if request.user.has_role(
            "Professor"
        ) and not request.user.has_system_permission("academics.manage"):
            data["professor"] = request.user.pk
        serializer = ScheduleSuggestionSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        suggestions = ScheduleSuggestionService.suggest(
            values["professor"],
            values["term"],
            values.get("duration_minutes", 90),
            values.get("weekdays"),
            values.get("location", ""),
        )
        return success({"suggestions": suggestions})
