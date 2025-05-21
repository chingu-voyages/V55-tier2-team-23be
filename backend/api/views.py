from .serializers import (
    RegisterSerializer,
    LoginSerializer,
    ResourceSerializer,
    TagSerializer,
)
from rest_framework.views import APIView
from rest_framework.viewsets import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken, TokenError
from core.models import Resource, Tag
import os
from rest_framework.decorators import api_view


EXTERNAL_API = os.getenv("EXTERNAL_API")
EXTERNAL_API_RESOURCES = EXTERNAL_API + "resources/"
EXTERNAL_API_TAGS = EXTERNAL_API + "tags/"


@api_view(["POST"])
def upload_data(request):
    tags_data = request.data.get("tags", [])
    resources_data = request.data.get("resources", [])

    for tag in tags_data:
        Tag.objects.update_or_create(
            external_id=tag["id"], defaults={"tag": tag["tag"]}
        )

    for resource in resources_data:
        resource_obj, _ = Resource.objects.update_or_create(
            external_id=resource["id"],
            defaults={
                "author": resource["author"],
                "name": resource["name"],
                "url": resource["url"],
                "created_at": resource.get("createdAt"),
            },
        )

        tag_ids = resource.get("appliedTags", [])
        tags = Tag.objects.filter(external_id__in=tag_ids)
        resource_obj.tags.set(tags)

    return Response({"status": "success"})


class ResourcesListAPIView(generics.ListAPIView):
    serializer_class = ResourceSerializer
    queryset = Resource.objects.all()


class TagListAPIView(generics.ListAPIView):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


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


class LogoutAPIView(APIView):

    def post(self, request, *args, **kwargs):
        res = Response({"message": "Logged out"}, status=status.HTTP_200_OK)
        try:
            refresh_token = request.COOKIES.get("refresh_token")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass

        res.delete_cookie("access_token", samesite="None")
        res.delete_cookie("refresh_token", samesite="None")

        return res


class CheckAuthAPIView(APIView):

    def get(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        access_token = request.COOKIES.get("access_token")

        try:
            if not access_token:
                raise TokenError("No access token in cookies!")

            AccessToken(access_token)
            return Response({"message": "Access token valid"})

        except TokenError:
            try:
                if not refresh_token:
                    raise TokenError("No refresh token in cookies!")

                refresh = RefreshToken(refresh_token)
                new_access_token = refresh.access_token

                res = Response({"message": "Access token refreshed!"})

                res.set_cookie(
                    key="access_token",
                    value=str(new_access_token),
                    httponly=True,
                    secure=True,
                    samesite="None",
                    max_age=30 * 60,
                )

                return res

            except TokenError:
                return Response(
                    {
                        "message": "Authentication credentials were not provided or are invalid"
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )
