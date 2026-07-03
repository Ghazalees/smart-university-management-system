"""Defines the generated database schema migration 0002_profile_experience_fields for the accounts application."""

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("accounts", "0001_initial")]
    operations = [
        migrations.AddField(
            model_name="profile", name="avatar_url", field=models.URLField(blank=True)
        ),
        migrations.AddField(
            model_name="profile",
            name="job_title",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="profile",
            name="office_location",
            field=models.CharField(blank=True, max_length=120),
        ),
        migrations.AddField(
            model_name="profile", name="website", field=models.URLField(blank=True)
        ),
        migrations.AddField(
            model_name="profile",
            name="preferred_language",
            field=models.CharField(default="en", max_length=10),
        ),
        migrations.AddField(
            model_name="profile",
            name="timezone",
            field=models.CharField(default="UTC", max_length=80),
        ),
        migrations.AddField(
            model_name="profile",
            name="emergency_contact",
            field=models.JSONField(blank=True, default=dict),
        ),
    ]
