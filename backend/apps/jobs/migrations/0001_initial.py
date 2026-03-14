from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Job",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(max_length=128)),
                ("company", models.CharField(max_length=128)),
                ("salary", models.CharField(max_length=64)),
                ("salary_min", models.IntegerField(default=0)),
                ("salary_max", models.IntegerField(default=0)),
                ("city", models.CharField(max_length=64)),
                ("industry", models.CharField(blank=True, max_length=64)),
                ("experience", models.CharField(blank=True, max_length=64)),
                ("education", models.CharField(blank=True, max_length=64)),
                ("description", models.TextField(blank=True)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("welfare", models.JSONField(blank=True, default=list)),
                ("publish_time", models.DateTimeField(blank=True, null=True)),
                ("source_url", models.URLField(blank=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
            ],
            options={"db_table": "jobs", "ordering": ["-created_at"]},
        ),
    ]
