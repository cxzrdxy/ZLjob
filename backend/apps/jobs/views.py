from rest_framework import generics
from rest_framework.response import Response
import time

from .models import Job
from .serializers import JobSerializer


def wrap_response(data=None, message="success", code=200):
    return {"code": code, "message": message, "data": data, "timestamp": int(time.time())}


class JobListView(generics.ListAPIView):
    serializer_class = JobSerializer

    def get_queryset(self):
        queryset = Job.objects.all()
        city = self.request.query_params.get("city")
        keyword = self.request.query_params.get("keyword")
        industry = self.request.query_params.get("industry")
        experience = self.request.query_params.get("experience")
        education = self.request.query_params.get("education")
        salary_min = self.request.query_params.get("salary_min")
        salary_max = self.request.query_params.get("salary_max")
        if city:
            queryset = queryset.filter(city=city)
        if keyword:
            queryset = queryset.filter(title__icontains=keyword)
        if industry:
            queryset = queryset.filter(industry=industry)
        if experience:
            queryset = queryset.filter(experience=experience)
        if education:
            queryset = queryset.filter(education=education)
        if salary_min:
            queryset = queryset.filter(salary_max__gte=int(salary_min))
        if salary_max:
            queryset = queryset.filter(salary_min__lte=int(salary_max))
        return queryset

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        return Response(wrap_response(response.data), status=response.status_code)


class JobDetailView(generics.RetrieveAPIView):
    queryset = Job.objects.all()
    serializer_class = JobSerializer

    def retrieve(self, request, *args, **kwargs):
        response = super().retrieve(request, *args, **kwargs)
        return Response(wrap_response(response.data), status=response.status_code)
