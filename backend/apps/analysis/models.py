from django.db import models


class Statistics(models.Model):
    report_type = models.CharField(max_length=32)
    report_date = models.DateField()
    city = models.CharField(max_length=64, blank=True)
    industry = models.CharField(max_length=64, blank=True)
    avg_salary = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    job_count = models.IntegerField(default=0)
    hot_tags = models.JSONField(default=list, blank=True)

    class Meta:
        db_table = "statistics"
        ordering = ["-report_date"]
