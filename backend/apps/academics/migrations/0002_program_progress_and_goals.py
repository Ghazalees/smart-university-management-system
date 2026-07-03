"""Defines the generated database schema migration 0002_program_progress_and_goals for the academics application."""

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
from django.core.validators import MaxValueValidator, MinValueValidator


class Migration(migrations.Migration):
    dependencies = [
        ("academics", "0001_initial"),
        ("accounts", "0001_initial"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]
    operations = [
        migrations.CreateModel(
            name="ProgramRequirement",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.CharField(
                        choices=[
                            ("core", "Core"),
                            ("specialized", "Specialized"),
                            ("elective", "Elective"),
                            ("general", "General"),
                        ],
                        default="core",
                        max_length=30,
                    ),
                ),
                (
                    "minimum_score",
                    models.DecimalField(decimal_places=2, default=50, max_digits=5),
                ),
                ("is_required", models.BooleanField(default=True)),
                (
                    "recommended_term",
                    models.PositiveSmallIntegerField(blank=True, null=True),
                ),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="program_requirements",
                        to="academics.course",
                    ),
                ),
                (
                    "department",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="program_requirements",
                        to="accounts.department",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="CoursePrerequisite",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "minimum_score",
                    models.DecimalField(decimal_places=2, default=50, max_digits=5),
                ),
                (
                    "course",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="prerequisite_links",
                        to="academics.course",
                    ),
                ),
                (
                    "prerequisite",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="required_for_links",
                        to="academics.course",
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="StudentAcademicGoal",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "target_gpa",
                    models.DecimalField(
                        decimal_places=2,
                        default=75,
                        max_digits=4,
                        validators=[MinValueValidator(0), MaxValueValidator(100)],
                    ),
                ),
                ("target_graduation_term", models.CharField(blank=True, max_length=40)),
                (
                    "preferred_max_credits",
                    models.PositiveSmallIntegerField(
                        default=15,
                        validators=[MinValueValidator(3), MaxValueValidator(30)],
                    ),
                ),
                (
                    "student",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="academic_goal",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name="programrequirement",
            constraint=models.UniqueConstraint(
                fields=("department", "course"), name="unique_program_requirement"
            ),
        ),
        migrations.AddConstraint(
            model_name="courseprerequisite",
            constraint=models.UniqueConstraint(
                fields=("course", "prerequisite"), name="unique_course_prerequisite"
            ),
        ),
        migrations.AddConstraint(
            model_name="courseprerequisite",
            constraint=models.CheckConstraint(
                condition=~models.Q(course=models.F("prerequisite")),
                name="course_not_own_prerequisite",
            ),
        ),
    ]
