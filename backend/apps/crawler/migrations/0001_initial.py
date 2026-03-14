import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [migrations.swappable_dependency(settings.AUTH_USER_MODEL)]

    operations = [
        migrations.CreateModel(
            name="CrawlTask",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("task_name", models.CharField(max_length=128)),
                ("keyword", models.CharField(max_length=64)),
                ("city", models.CharField(max_length=64)),
                ("industry", models.CharField(blank=True, max_length=64)),
                ("max_pages", models.PositiveIntegerField(default=5)),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "pending"), ("running", "running"), ("success", "success"), ("failed", "failed")],
                        default="pending",
                        max_length=16,
                    ),
                ),
                ("total_count", models.IntegerField(default=0)),
                ("success_count", models.IntegerField(default=0)),
                ("fail_count", models.IntegerField(default=0)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "created_by",
                    models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL),
                ),
            ],
            options={"db_table": "crawl_tasks", "ordering": ["-created_at"]},
        ),
    ]
