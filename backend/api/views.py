from .serializers import RegisterSerializer, LoginSerializer, ResourceSerializer
from rest_framework.views import APIView
from rest_framework.viewsets import generics
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, AccessToken
from core.models import Resource, Tag
import os
import requests
from django.http import JsonResponse
from django.views.decorators.http import require_GET

@require_GET
def trigger_sync(request):
    try:
        sync_resources_and_tags()
        return JsonResponse({"status": "success", "message": "Sync completed"})
    except Exception as e:
        return JsonResponse({"status": "error", "message": str(e)}, status=500)

EXTERNAL_API = os.getenv("EXTERNAL_API")
EXTERNAL_API_RESOURCES = EXTERNAL_API + "resources/"
EXTERNAL_API_TAGS = EXTERNAL_API + "tags/"


def sync_resources_and_tags():
    tag_response = requests.get(EXTERNAL_API_TAGS)
    if tag_response.status_code == 200:
        tags_data = tag_response.json()
        for tag in tags_data:
            Tag.objects.update_or_create(
                external_id=tag["id"], defaults={"tag": tag["tag"]}
            )
            print(tag["tag"])

    resource_response = requests.get(EXTERNAL_API_RESOURCES)
    print(resource_response.status_code)
    if resource_response.status_code == 200:
        resources_data = resource_response.json()
        for resource in resources_data:
            resource_obj, created = Resource.objects.update_or_create(
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
