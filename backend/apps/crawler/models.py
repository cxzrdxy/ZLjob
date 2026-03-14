from django.contrib.auth.models import User
from django.db import models


class CrawlTask(models.Model):
    STATUS_CHOICES = (
        ("pending", "pending"),
        ("running", "running"),
        ("success", "success"),
        ("failed", "failed"),
    )

    task_name = models.CharField(max_length=128)
    keyword = models.CharField(max_length=64)
    city = models.CharField(max_length=64)
    industry = models.CharField(max_length=64, blank=True)
    max_pages = models.PositiveIntegerField(default=5)
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="pending")
    total_count = models.IntegerField(default=0)
    success_count = models.IntegerField(default=0)
    fail_count = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_by = models.ForeignKey(User, null=True, blank=True, on_delete=models.SET_NULL)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "crawl_tasks"
        ordering = ["-created_at"]
