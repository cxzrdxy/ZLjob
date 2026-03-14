from django.db.models import Count, Avg
from rest_framework.response import Response
from rest_framework.views import APIView
import time

from apps.jobs.models import Job


def wrap_response(data=None, message="success", code=200):
    return {"code": code, "message": message, "data": data or {}, "timestamp": int(time.time())}


class SalaryStatisticsView(APIView):
    def get(self, request):
        rows = (
            Job.objects.values("city")
            .annotate(job_count=Count("id"), avg_salary=Avg("salary_min"))
            .order_by("-job_count")
        )
        return Response(wrap_response(list(rows)))


class HotStatisticsView(APIView):
    def get(self, request):
        top_cities = (
            Job.objects.values("city").annotate(job_count=Count("id")).order_by("-job_count")[:10]
        )
        top_companies = (
            Job.objects.values("company").annotate(job_count=Count("id")).order_by("-job_count")[:10]
        )
        return Response(wrap_response({"top_cities": list(top_cities), "top_companies": list(top_companies)}))


class TrendStatisticsView(APIView):
    def get(self, request):
        rows = (
            Job.objects.exclude(publish_time__isnull=True)
            .extra(select={"day": "date(publish_time)"})
            .values("day")
            .annotate(job_count=Count("id"))
            .order_by("day")
        )
        return Response(wrap_response(list(rows)))
