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
            name="Question",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=180)),
                ("body", models.TextField()),
                ("category", models.CharField(blank=True, max_length=80)),
                ("status", models.CharField(choices=[("Pending", "Pending"), ("Answered", "Answered"), ("Escalated", "Escalated"), ("Failed", "Failed")], default="Pending", max_length=20)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("submitted_by", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="questions", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "questions",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="QuestionHistory",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("event", models.CharField(max_length=80)),
                ("status_from", models.CharField(blank=True, max_length=20)),
                ("status_to", models.CharField(blank=True, max_length=20)),
                ("note", models.TextField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("actor", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="question_history_events", to=settings.AUTH_USER_MODEL)),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="history", to="qa.question")),
            ],
            options={
                "db_table": "question_history",
                "ordering": ["created_at"],
            },
        ),
        migrations.CreateModel(
            name="QuestionResponse",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("body", models.TextField()),
                ("confidence", models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ("source_documents", models.JSONField(blank=True, default=list)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("question", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="responses", to="qa.question")),
                ("responder", models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="question_responses", to=settings.AUTH_USER_MODEL)),
            ],
            options={
                "db_table": "question_responses",
                "ordering": ["-created_at"],
            },
        ),
    ]
