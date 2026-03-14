from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
import time

from .serializers import RegisterSerializer


def success_response(data=None, message="success", code=200):
    return {"code": code, "message": message, "data": data or {}, "timestamp": int(time.time())}


class RegisterView(APIView):
    permission_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(success_response(message="register success"), status=status.HTTP_201_CREATED)


class LoginView(TokenObtainPairView):
    permission_classes = []

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        return Response(success_response(response.data), status=response.status_code)
