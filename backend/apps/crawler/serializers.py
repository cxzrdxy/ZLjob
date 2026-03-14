from rest_framework import serializers

from .models import CrawlTask


class CrawlTaskSerializer(serializers.ModelSerializer):
    class Meta:
        model = CrawlTask
        fields = "__all__"
        read_only_fields = ("status", "total_count", "success_count", "fail_count", "created_at")
