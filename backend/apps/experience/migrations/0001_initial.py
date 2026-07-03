"""Defines the generated database schema migration 0001_initial for the experience application."""

# Generated manually for the delivery artifact.
from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    initial = True
    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]
    operations = [
        migrations.CreateModel(
            name="UserExperiencePreference",
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
                ("accent_color", models.CharField(default="indigo", max_length=20)),
                (
                    "density",
                    models.CharField(
                        choices=[
                            ("comfortable", "Comfortable"),
                            ("compact", "Compact"),
                        ],
                        default="comfortable",
                        max_length=20,
                    ),
                ),
                ("reduced_motion", models.BooleanField(default=False)),
                ("high_contrast", models.BooleanField(default=False)),
                ("language", models.CharField(default="en", max_length=10)),
                ("dashboard_layout", models.JSONField(blank=True, default=list)),
                ("onboarding_completed", models.BooleanField(default=False)),
                (
                    "digest_frequency",
                    models.CharField(
                        choices=[
                            ("off", "Off"),
                            ("daily", "Daily"),
                            ("weekly", "Weekly"),
                        ],
                        default="daily",
                        max_length=20,
                    ),
                ),
                (
                    "user",
                    models.OneToOneField(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="experience_preferences",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.CreateModel(
            name="Feedback",
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
                    "feedback_type",
                    models.CharField(
                        choices=[
                            ("bug", "Bug"),
                            ("idea", "Idea"),
                            ("ux", "UX feedback"),
                            ("ai", "AI feedback"),
                            ("other", "Other"),
                        ],
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(max_length=180)),
                ("message", models.TextField()),
                ("page", models.CharField(blank=True, max_length=300)),
                ("rating", models.PositiveSmallIntegerField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("new", "New"),
                            ("triaged", "Triaged"),
                            ("in_progress", "In progress"),
                            ("resolved", "Resolved"),
                            ("closed", "Closed"),
                        ],
                        db_index=True,
                        default="new",
                        max_length=20,
                    ),
                ),
                ("admin_note", models.TextField(blank=True)),
                (
                    "assigned_to",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="assigned_feedback",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="feedback_items",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={"ordering": ["-created_at"]},
        ),
        migrations.AddIndex(
            model_name="feedback",
            index=models.Index(
                fields=["status", "feedback_type", "-created_at"],
                name="experience__status_568f3a_idx",
            ),
        ),
    ]
