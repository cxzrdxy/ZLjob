from django.urls import path

from .views import CrawlTaskDetailView, CrawlTaskListCreateView


urlpatterns = [
    path("tasks", CrawlTaskListCreateView.as_view(), name="crawl-task-list-create"),
    path("tasks/<int:pk>", CrawlTaskDetailView.as_view(), name="crawl-task-detail"),
]
