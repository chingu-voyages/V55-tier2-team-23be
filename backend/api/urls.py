from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView,
)
from .views import (
    RegisterAPIView,
    LoginAPIView,
    LogoutAPIView,
    CheckAuthAPIView,
    ResourcesListAPIView,
    TagListAPIView,
    upload_data,
    SyncPageView,
    SaveOrUnsaveResourceAPIView,
    SavedResourcesAPIView,
    GoogleAuthAPIView
)
from django.contrib.staticfiles.views import serve


urlpatterns = [
    path("auth/token/", TokenObtainPairView.as_view(), name="token-obtain"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path("auth/token/verify/", TokenVerifyView.as_view(), name="token-verify"),
    path("auth/register/", RegisterAPIView.as_view(), name="register"),
    path("auth/login/", LoginAPIView.as_view(), name="login"),
    path("auth/logout/", LogoutAPIView.as_view(), name="logout"),
    path("auth/check-auth/", CheckAuthAPIView.as_view(), name="check-auth"),
    path("auth/google/", GoogleAuthAPIView.as_view(), name="google-auth"),
    path("resources/", ResourcesListAPIView.as_view(), name="resources"),
    path("resource/save/<int:id>/", SaveOrUnsaveResourceAPIView.as_view(), name="save-resource"),
    path("resource/unsave/<int:id>/", SaveOrUnsaveResourceAPIView.as_view(), name="unsave-resource"),
    path("resources/saved/", SavedResourcesAPIView.as_view(), name="saved-resource"),
    path("tags/", TagListAPIView.as_view(), name="tags"),
    path("upload-data/", upload_data),
    path("sync-page/", SyncPageView.as_view(), name="sync-page"),
]
