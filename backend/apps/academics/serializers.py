"""Validates and transforms API data for academic classes, enrollments, exams, grades, and progress."""

from django.utils import timezone
from rest_framework import serializers

from apps.accounts.models import Role, User

from .models import AcademicClass, Course, Enrollment, Exam, Grade, StudentAcademicGoal


class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "code", "title", "credits", "department", "is_active"]


class AcademicClassSerializer(serializers.ModelSerializer):
    course_detail = CourseSerializer(source="course", read_only=True)
    professor_name = serializers.SerializerMethodField()
    enrolled_count = serializers.IntegerField(read_only=True, required=False)

    class Meta:
        model = AcademicClass
        fields = [
            "id",
            "course",
            "course_detail",
            "professor",
            "professor_name",
            "term",
            "section",
            "weekday",
            "start_time",
            "end_time",
            "location",
            "capacity",
            "enrolled_count",
            "is_active",
        ]

    def get_professor_name(self, obj):
        return obj.professor.get_full_name() or obj.professor.username

    def validate_professor(self, value):
        if not value.has_role(Role.PROFESSOR):
            raise serializers.ValidationError("The selected user is not a professor.")
        return value

    def validate(self, attrs):
        start = attrs.get("start_time", getattr(self.instance, "start_time", None))
        end = attrs.get("end_time", getattr(self.instance, "end_time", None))
        if start and end and start >= end:
            raise serializers.ValidationError(
                {"end_time": "End time must be after start time."}
            )
        professor = attrs.get("professor", getattr(self.instance, "professor", None))
        weekday = attrs.get("weekday", getattr(self.instance, "weekday", None))
        term = attrs.get("term", getattr(self.instance, "term", None))
        if professor and weekday and term and start and end:
            conflicts = AcademicClass.objects.filter(
                professor=professor,
                weekday=weekday,
                term=term,
                start_time__lt=end,
                end_time__gt=start,
                is_active=True,
            )
            if self.instance:
                conflicts = conflicts.exclude(pk=self.instance.pk)
            if conflicts.exists():
                raise serializers.ValidationError(
                    "The professor has a conflicting class."
                )
            location = attrs.get("location", getattr(self.instance, "location", ""))
            if location:
                room_conflicts = AcademicClass.objects.filter(
                    location__iexact=location,
                    weekday=weekday,
                    term=term,
                    start_time__lt=end,
                    end_time__gt=start,
                    is_active=True,
                )
                if self.instance:
                    room_conflicts = room_conflicts.exclude(pk=self.instance.pk)
                if room_conflicts.exists():
                    raise serializers.ValidationError(
                        {
                            "location": "The selected room is already occupied at this time."
                        }
                    )
        capacity = attrs.get("capacity", getattr(self.instance, "capacity", None))
        if self.instance and capacity is not None:
            enrolled_count = self.instance.enrollments.count()
            if capacity < enrolled_count:
                raise serializers.ValidationError(
                    {
                        "capacity": (
                            f"Capacity cannot be lower than the {enrolled_count} "
                            "students already enrolled."
                        )
                    }
                )
        return attrs


class EnrollmentSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = ["id", "academic_class", "student", "student_name", "created_at"]
        validators = []

    def get_student_name(self, obj):
        return obj.student.get_full_name() or obj.student.username

    def validate_student(self, value):
        if not value.has_role(Role.STUDENT):
            raise serializers.ValidationError("The selected user is not a student.")
        return value

    def validate(self, attrs):
        academic_class = attrs["academic_class"]
        student = attrs["student"]
        if not academic_class.is_active:
            raise serializers.ValidationError(
                "Students cannot be enrolled in an inactive class."
            )
        if not student.is_active:
            raise serializers.ValidationError(
                "An inactive student account cannot be enrolled."
            )
        if Enrollment.objects.filter(
            academic_class=academic_class, student=student
        ).exists():
            raise serializers.ValidationError(
                {"student": "This student is already enrolled in the selected class."}
            )
        if academic_class.enrollments.count() >= academic_class.capacity:
            raise serializers.ValidationError("This class is at capacity.")
        return attrs


class ExamSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(
        source="academic_class.course.title", read_only=True
    )

    class Meta:
        model = Exam
        fields = [
            "id",
            "academic_class",
            "course_title",
            "title",
            "scheduled_at",
            "duration_minutes",
            "location",
            "instructions",
        ]

    def validate_scheduled_at(self, value):
        if value <= timezone.now():
            raise serializers.ValidationError(
                "An exam must be scheduled in the future."
            )
        return value

    def validate(self, attrs):
        academic_class = attrs.get(
            "academic_class", getattr(self.instance, "academic_class", None)
        )
        scheduled_at = attrs.get(
            "scheduled_at", getattr(self.instance, "scheduled_at", None)
        )
        duration = attrs.get(
            "duration_minutes", getattr(self.instance, "duration_minutes", 90)
        )
        if academic_class and scheduled_at:
            from datetime import timedelta

            finish = scheduled_at + timedelta(minutes=duration)
            conflicts = Exam.objects.filter(
                academic_class__enrollments__student__in=academic_class.students.all(),
                scheduled_at__lt=finish,
                scheduled_at__gte=scheduled_at - timedelta(hours=4),
            ).distinct()
            if self.instance:
                conflicts = conflicts.exclude(pk=self.instance.pk)
            if conflicts.exists():
                raise serializers.ValidationError(
                    "One or more students have a potentially conflicting exam."
                )
        return attrs


class GradeSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    course_title = serializers.CharField(
        source="academic_class.course.title", read_only=True
    )

    class Meta:
        model = Grade
        fields = [
            "id",
            "academic_class",
            "course_title",
            "student",
            "student_name",
            "score",
            "feedback",
            "graded_by",
            "updated_at",
        ]
        read_only_fields = ["graded_by"]

    def get_student_name(self, obj):
        return obj.student.get_full_name() or obj.student.username

    def validate(self, attrs):
        academic_class = attrs.get(
            "academic_class", getattr(self.instance, "academic_class", None)
        )
        student = attrs.get("student", getattr(self.instance, "student", None))
        if (
            academic_class
            and student
            and not Enrollment.objects.filter(
                academic_class=academic_class, student=student
            ).exists()
        ):
            raise serializers.ValidationError(
                "The student is not enrolled in this class."
            )
        request = self.context.get("request")
        if (
            request
            and academic_class
            and not (
                request.user.is_superuser
                or academic_class.professor_id == request.user.id
                or request.user.has_system_permission("academics.manage")
            )
        ):
            raise serializers.ValidationError("You cannot grade this class.")
        return attrs


class StudentAcademicGoalSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentAcademicGoal
        fields = [
            "target_gpa",
            "target_graduation_term",
            "preferred_max_credits",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]


class ScheduleSuggestionSerializer(serializers.Serializer):
    professor = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.filter(is_active=True)
    )
    term = serializers.CharField(max_length=40)
    duration_minutes = serializers.IntegerField(min_value=30, max_value=240, default=90)
    weekdays = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=7),
        required=False,
    )
    location = serializers.CharField(max_length=120, required=False, allow_blank=True)

    def validate_professor(self, value):
        if not value.has_role(Role.PROFESSOR):
            raise serializers.ValidationError("The selected user is not a professor.")
        return value
