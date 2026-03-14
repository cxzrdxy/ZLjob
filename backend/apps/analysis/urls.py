from django.urls import path

from .views import HotStatisticsView, SalaryStatisticsView, TrendStatisticsView


urlpatterns = [
    path("salary", SalaryStatisticsView.as_view(), name="statistics-salary"),
    path("hot", HotStatisticsView.as_view(), name="statistics-hot"),
    path("trend", TrendStatisticsView.as_view(), name="statistics-trend"),
]
