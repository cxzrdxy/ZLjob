from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path


def api_root(_request):
    return JsonResponse(
        {
            "code": 200,
            "message": "success",
            "data": {
                "auth": "/api/auth/",
                "jobs": "/api/jobs/",
                "statistics": "/api/statistics/",
                "crawl": "/api/crawl/",
            },
        }
    )


urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", api_root),
    path("api/auth/", include("apps.users.urls")),
    path("api/jobs/", include("apps.jobs.urls")),
    path("api/statistics/", include("apps.analysis.urls")),
    path("api/crawl/", include("apps.crawler.urls")),
]
