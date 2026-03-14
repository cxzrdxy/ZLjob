from django.db import models


class Job(models.Model):
    title = models.CharField(max_length=128)
    company = models.CharField(max_length=128)
    salary = models.CharField(max_length=64)
    salary_min = models.IntegerField(default=0)
    salary_max = models.IntegerField(default=0)
    city = models.CharField(max_length=64)
    industry = models.CharField(max_length=64, blank=True)
    experience = models.CharField(max_length=64, blank=True)
    education = models.CharField(max_length=64, blank=True)
    description = models.TextField(blank=True)
    tags = models.JSONField(default=list, blank=True)
    welfare = models.JSONField(default=list, blank=True)
    publish_time = models.DateTimeField(null=True, blank=True)
    source_url = models.URLField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "jobs"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.title} - {self.company}"
