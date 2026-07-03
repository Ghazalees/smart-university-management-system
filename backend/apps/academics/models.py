"""Defines persistent data models for academic classes, enrollments, exams, grades, and progress."""

from django.conf import settings
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from apps.accounts.models import Department
from apps.core.models import TimeStampedModel


class Course(TimeStampedModel):
    code = models.CharField(max_length=30, unique=True)
    title = models.CharField(max_length=180)
    credits = models.PositiveSmallIntegerField(default=3)
    department = models.ForeignKey(
        Department,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="courses",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code} — {self.title}"


class AcademicClass(TimeStampedModel):
    class Weekday(models.IntegerChoices):
        MONDAY = 1, "Monday"
        TUESDAY = 2, "Tuesday"
        WEDNESDAY = 3, "Wednesday"
        THURSDAY = 4, "Thursday"
        FRIDAY = 5, "Friday"
        SATURDAY = 6, "Saturday"
        SUNDAY = 7, "Sunday"

    course = models.ForeignKey(Course, on_delete=models.PROTECT, related_name="classes")
    professor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="teaching_classes",
    )
    term = models.CharField(max_length=40)
    section = models.CharField(max_length=20, default="01")
    weekday = models.PositiveSmallIntegerField(choices=Weekday.choices)
    start_time = models.TimeField()
    end_time = models.TimeField()
    location = models.CharField(max_length=120)
    capacity = models.PositiveIntegerField(default=30)
    students = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="Enrollment",
        related_name="enrolled_classes",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["weekday", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["course", "term", "section"], name="unique_course_term_section"
            )
        ]


class Enrollment(TimeStampedModel):
    academic_class = models.ForeignKey(
        AcademicClass, on_delete=models.CASCADE, related_name="enrollments"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="enrollments"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["academic_class", "student"], name="unique_class_student"
            )
        ]


class Exam(TimeStampedModel):
    academic_class = models.ForeignKey(
        AcademicClass, on_delete=models.CASCADE, related_name="exams"
    )
    title = models.CharField(max_length=150)
    scheduled_at = models.DateTimeField()
    duration_minutes = models.PositiveIntegerField(default=90)
    location = models.CharField(max_length=120)
    instructions = models.TextField(blank=True)

    class Meta:
        ordering = ["scheduled_at"]


class Grade(TimeStampedModel):
    academic_class = models.ForeignKey(
        AcademicClass, on_delete=models.CASCADE, related_name="grades"
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="grades"
    )
    score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
        related_name="submitted_grades",
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["academic_class", "student"], name="unique_class_grade"
            )
        ]


class ProgramRequirement(TimeStampedModel):
    class Category(models.TextChoices):
        CORE = "core", "Core"
        SPECIALIZED = "specialized", "Specialized"
        ELECTIVE = "elective", "Elective"
        GENERAL = "general", "General"

    department = models.ForeignKey(
        Department, on_delete=models.CASCADE, related_name="program_requirements"
    )
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="program_requirements"
    )
    category = models.CharField(
        max_length=30, choices=Category.choices, default=Category.CORE
    )
    minimum_score = models.DecimalField(max_digits=5, decimal_places=2, default=50)
    is_required = models.BooleanField(default=True)
    recommended_term = models.PositiveSmallIntegerField(null=True, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["department", "course"], name="unique_program_requirement"
            )
        ]


class CoursePrerequisite(TimeStampedModel):
    course = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="prerequisite_links"
    )
    prerequisite = models.ForeignKey(
        Course, on_delete=models.CASCADE, related_name="required_for_links"
    )
    minimum_score = models.DecimalField(max_digits=5, decimal_places=2, default=50)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["course", "prerequisite"], name="unique_course_prerequisite"
            ),
            models.CheckConstraint(
                condition=~models.Q(course=models.F("prerequisite")),
                name="course_not_own_prerequisite",
            ),
        ]


class StudentAcademicGoal(TimeStampedModel):
    student = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="academic_goal"
    )
    target_gpa = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        default=75,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    target_graduation_term = models.CharField(max_length=40, blank=True)
    preferred_max_credits = models.PositiveSmallIntegerField(
        default=15, validators=[MinValueValidator(3), MaxValueValidator(30)]
    )
