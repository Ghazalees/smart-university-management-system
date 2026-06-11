from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("documents", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="document",
            name="summary",
            field=models.TextField(blank=True),
        ),
        migrations.AddField(
            model_name="document",
            name="keywords",
            field=models.TextField(
                blank=True,
                help_text="Comma-separated keywords used for document search and AI retrieval.",
            ),
        ),
        migrations.AddField(
            model_name="document",
            name="is_knowledge_base_enabled",
            field=models.BooleanField(default=True),
        ),
        migrations.AddField(
            model_name="document",
            name="version",
            field=models.PositiveIntegerField(default=1),
        ),
        migrations.AddField(
            model_name="document",
            name="archived_at",
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="document",
            name="archived_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="archived_documents",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.AddField(
            model_name="document",
            name="last_updated_by",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name="last_updated_documents",
                to=settings.AUTH_USER_MODEL,
            ),
        ),
        migrations.CreateModel(
            name="DocumentAuditLog",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "action",
                    models.CharField(
                        choices=[
                            ("created", "Created"),
                            ("updated", "Updated"),
                            ("archived", "Archived"),
                        ],
                        max_length=40,
                    ),
                ),
                ("changes", models.JSONField(blank=True, default=dict)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "actor",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="document_audit_logs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "document",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="audit_logs",
                        to="documents.document",
                    ),
                ),
            ],
            options={
                "db_table": "document_audit_logs",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="document",
            index=models.Index(fields=["updated_at"], name="documents_updated_5ad4a2_idx"),
        ),
        migrations.AddIndex(
            model_name="document",
            index=models.Index(fields=["is_knowledge_base_enabled"], name="documents_is_know_31f7bb_idx"),
        ),
        migrations.AddIndex(
            model_name="documentauditlog",
            index=models.Index(fields=["action"], name="document_au_action_2701ba_idx"),
        ),
        migrations.AddIndex(
            model_name="documentauditlog",
            index=models.Index(fields=["created_at"], name="document_au_created_0787a9_idx"),
        ),
        migrations.AddIndex(
            model_name="documentauditlog",
            index=models.Index(fields=["document", "action"], name="document_au_documen_e04a61_idx"),
        ),
    ]
