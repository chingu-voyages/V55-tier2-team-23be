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
from core.models import Resource, Tag, UserSavedResource, UserRating
import os
from rest_framework.decorators import api_view
from django.views.generic import TemplateView
from django.shortcuts import get_object_or_404
from rest_framework.permissions import IsAuthenticated, AllowAny
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.views import TokenRefreshView


EXTERNAL_API = os.getenv("EXTERNAL_API")
EXTERNAL_API_RESOURCES = EXTERNAL_API + "resources/"
EXTERNAL_API_TAGS = EXTERNAL_API + "tags/"

User = get_user_model()


class SyncPageView(TemplateView):
    template_name = "sync/sync.html"


class CustomRefreshTokenView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {"message": "Refresh token must be set in cookies!"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            refresh = RefreshToken(refresh_token)

            user_id = refresh["user_id"]
            user = User.objects.get(id=user_id)

            new_refresh = RefreshToken.for_user(user)
            new_access = new_refresh.access_token

            res = Response(
                {"message": "Tokens refreshed successfully"},
                status=status.HTTP_200_OK,
            )

            res.set_cookie(
                key="access_token",
                value=str(new_access),
                httponly=True,
                secure=True,
                samesite="None",
                max_age=30 * 60,
            )

            res.set_cookie(
                key="refresh_token",
                value=str(new_refresh),
                httponly=True,
                secure=True,
                samesite="None",
                max_age=7 * 24 * 60 * 60,
            )

            return res

        except TokenError:
            return Response(
                {"message": "Invalid or expired refresh token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        except User.DoesNotExist:
            return Response(
                {"message": "User not found"}, 
                status=status.HTTP_404_NOT_FOUND
            )


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
    permission_classes = [AllowAny]

    def get(self, request):
        refresh_token = request.COOKIES.get("refresh_token")
        access_token = request.COOKIES.get("access_token")

        try:
            if not access_token:
                raise TokenError("No access token in cookies!")

            token = AccessToken(access_token)
            token.verify()
            return Response(
                {"message": "Access token valid"}, status=status.HTTP_200_OK
            )

        except TokenError as e:
            try:
                if not refresh_token:
                    raise TokenError("No refresh token in cookies!")

                refresh = RefreshToken(refresh_token)

                user_id = refresh["user_id"]
                try:
                    user = User.objects.get(id=user_id)
                except User.DoesNotExist:
                    raise TokenError("User not found")

                new_refresh = RefreshToken.for_user(user)
                new_access = new_refresh.access_token

                try:
                    refresh.blacklist()
                except Exception as e:
                    pass

                res = Response(
                    {"message": "Access token refreshed!"}, status=status.HTTP_200_OK
                )

                res.set_cookie(
                    key="access_token",
                    value=str(new_access),
                    httponly=True,
                    secure=True,
                    samesite="None",
                    max_age=30 * 60,
                )

                res.set_cookie(
                    key="refresh_token",
                    value=str(new_refresh),
                    httponly=True,
                    secure=True,
                    samesite="None",
                    max_age=7 * 24 * 60 * 60,
                )

                return res

            except TokenError as e:
                return Response(
                    {
                        "message": "Authentication credentials were not provided or are invalid"
                    },
                    status=status.HTTP_401_UNAUTHORIZED,
                )


class SaveOrUnsaveResourceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        id = kwargs.get("id")
        url_path = request.path
        resource = get_object_or_404(Resource, id=id)
        user = request.user

        if "unsave" in url_path:
            UserSavedResource.objects.filter(resource=resource, user=user).delete()
            return Response(
                {"message": "Resouce was unsaved succesffully!"},
                status=status.HTTP_200_OK,
            )

        UserSavedResource.objects.get_or_create(
            resource=resource, user=user, is_saved=True
        )

        return Response(
            {"message": "Resource was saved successfully!"}, status=status.HTTP_200_OK
        )


class SavedResourcesAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        saved_resources = UserSavedResource.objects.filter(user=request.user)

        resources = [saved.resource for saved in saved_resources]

        serializer = ResourceSerializer(resources, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    

class RateResourceAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        resource_id = kwargs.get("resource_id")
        rating = request.data.get("rating")
        user = request.user

        if not rating:
            return Response({"error": "Rating value is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            resource = Resource.objects.get(id=resource_id)
        except Resource.DoesNotExist:
            return Response({"error": "Resource not found."}, status=status.HTTP_404_NOT_FOUND)

        rating_obj, created = UserRating.objects.update_or_create(
            user=user,
            resource=resource,
            defaults={'rating': rating}
        )

        if created:
            message = "Rating was successfully created!"
        else:
            message = "Rating was successfully updated!"

        return Response({"message": message}, status=status.HTTP_200_OK)


class GoogleAuthAPIView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request, *args, **kwargs):
        token = request.data.get("token")
        if not token:
            return Response(
                {"message": "Token must be set!"}, status=status.HTTP_400_BAD_REQUEST
            )

        try:
            CLIEND_ID = os.getenv("GOOGLE_CLIENT_ID")
            idinfo = id_token.verify_oauth2_token(
                token, google_requests.Request(), CLIEND_ID
            )
            email = idinfo["email"]
            name = idinfo.get("name", "")
            picture = idinfo.get("picture")

            user, created = User.objects.get_or_create(
                email=email,
                defaults={"username": name, "email": email},
            )

            if created:
                user.set_unusable_password()
                user.is_active = True
                user.save()

            refresh = RefreshToken.for_user(user)
            access = AccessToken.for_user(user)

            res = Response(status=status.HTTP_200_OK)

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
        except ValueError as e:
            return Response(
                {"message": "Invalid token"}, status=status.HTTP_400_BAD_REQUEST
            )
