"""Defines the generated database schema migration 0002_response_quality_metadata for the qa application."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("qa", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="questionresponse",
            name="citations",
            field=models.JSONField(blank=True, default=list),
        ),
        migrations.AddField(
            model_name="questionresponse",
            name="retrieval_metadata",
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AddField(
            model_name="questionresponse",
            name="safety_status",
            field=models.CharField(default="grounded", max_length=40),
        ),
        migrations.AddField(
            model_name="questionresponse",
            name="latency_ms",
            field=models.PositiveIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="questionresponse",
            name="user_rating",
            field=models.SmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name="questionresponse",
            name="user_feedback",
            field=models.TextField(blank=True),
        ),
    ]
