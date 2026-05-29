# Generated for Sprint 1 Backend Developer 2 document foundation.

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="Document",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=255)),
                (
                    "document_type",
                    models.CharField(
                        choices=[
                            ("policy", "Policy"),
                            ("faq", "FAQ"),
                            ("guide", "Guide"),
                            ("form", "Form"),
                            ("announcement", "Announcement"),
                            ("other", "Other"),
                        ],
                        default="other",
                        max_length=40,
                    ),
                ),
                (
                    "access_level",
                    models.CharField(
                        choices=[
                            ("public", "Public"),
                            ("student", "Student"),
                            ("professor", "Professor"),
                            ("staff", "Administrative Staff"),
                            ("president", "University President"),
                        ],
                        default="public",
                        max_length=40,
                    ),
                ),
                ("content", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_documents",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "documents",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="document",
            index=models.Index(fields=["document_type"], name="documents_docume_bf7d98_idx"),
        ),
        migrations.AddIndex(
            model_name="document",
            index=models.Index(fields=["access_level"], name="documents_access__94260f_idx"),
        ),
        migrations.AddIndex(
            model_name="document",
            index=models.Index(fields=["is_active"], name="documents_is_acti_7eb1a8_idx"),
        ),
        migrations.AddIndex(
            model_name="document",
            index=models.Index(fields=["title"], name="documents_title_5f04e8_idx"),
        ),
    ]
