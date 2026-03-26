from rest_framework import generics, permissions, status
from rest_framework.response import Response
import time

from .models import CrawlTask
from .serializers import CrawlTaskSerializer
from .tasks import run_crawl_task


def wrap_response(data=None, message="success", code=200):
    return {"code": code, "message": message, "data": data, "timestamp": int(time.time())}


class CrawlTaskListCreateView(generics.ListCreateAPIView):
    serializer_class = CrawlTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CrawlTask.objects.filter(created_by=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        task = serializer.save(created_by=request.user)
        try:
            run_crawl_task.delay(task.id)
        except Exception:
            task.delete()
            return Response(
                wrap_response(message="任务调度失败，请检查 Redis/Celery 服务后重试", code=503),
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )
        out = self.get_serializer(task).data
        return Response(wrap_response(out), status=status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(wrap_response(response.data), status=response.status_code)


class CrawlTaskDetailView(generics.RetrieveAPIView):
    serializer_class = CrawlTaskSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return CrawlTask.objects.filter(created_by=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(wrap_response(response.data), status=response.status_code)
