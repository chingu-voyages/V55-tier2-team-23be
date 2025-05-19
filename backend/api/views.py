from .serializers import RegisterSerializer, LoginSerializer, ResourceSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from core.models import Resource, Tag
import os


class ResourcesListAPIView(generics.ListAPIView):
    serializer_class = ResourceSerializer
    queryset = Resource.objects.all()


class RegisterAPIView(APIView):
    serializer_class = RegisterSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        access = AccessToken.for_user(user)

        res = Response(
            {"message": "user was successfully registrated"},
            status=status.HTTP_201_CREATED,
        )

        res.set_cookie(
            key="access_token",
            value=str(access),
            httponly=True,
            secure=True,
            samesite="None",
            max_age=30 * 60,
        )

        res.set_cookie(
            key="refresh_token",
            value=str(refresh),
            httponly=True,
            secure=True,
            samesite="None",
            max_age=7 * 24 * 60 * 60,
        )

        return res


class LoginAPIView(APIView):
    serializer_class = LoginSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data["user"]
            refresh = RefreshToken.for_user(user)
            access = AccessToken.for_user(user)

            res = Response(
                {"message": "successfully logged in!"}, status=status.HTTP_200_OK
            )

            res.set_cookie(
                key="access_token",
                value=str(access),
                httponly=True,
                secure=True,
                samesite="None",
                max_age=30 * 60,
            )

            res.set_cookie(
                key="refresh_token",
                value=str(refresh),
                httponly=True,
                secure=True,
                samesite="None",
                max_age=7 * 24 * 60 * 60,
            )

            return res

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
