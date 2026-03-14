from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Statistics",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("report_type", models.CharField(max_length=32)),
                ("report_date", models.DateField()),
                ("city", models.CharField(blank=True, max_length=64)),
                ("industry", models.CharField(blank=True, max_length=64)),
                ("avg_salary", models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ("job_count", models.IntegerField(default=0)),
                ("hot_tags", models.JSONField(blank=True, default=list)),
            ],
            options={"db_table": "statistics", "ordering": ["-report_date"]},
        ),
    ]
