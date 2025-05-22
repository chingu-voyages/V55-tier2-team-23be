from django.db import models
from django.contrib.auth.models import (
    BaseUserManager,
    AbstractBaseUser,
    PermissionsMixin,
)
from backend.settings import AUTH_USER_MODEL
from django.core.validators import MinValueValidator, MaxValueValidator


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email")
        if not username:
            raise ValueError("Users must have a username")

        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save()

        return user

    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        return self.create_user(email, username, password, **extra_fields)


class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.email} - {self.username}"


class Tag(models.Model):
    external_id = models.CharField(max_length=255, unique=True)
    tag = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.tag}"


class Resource(models.Model):
    external_id = models.CharField(max_length=255, unique=True)
    author = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=1500)
    created_at = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name="resources")

    def __str__(self):
        return f"{self.author} - {self.name}"


class UserRating(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "resource")
        verbose_name = "User Rating"
        verbose_name_plural = "User Ratings"

    def __str__(self):
        return f"{self.user} - {self.resource} - {self.rating}"


class UserSavedResource(models.Model):
    user = models.ForeignKey(AUTH_USER_MODEL, on_delete=models.CASCADE)
    resource = models.ForeignKey(Resource, on_delete=models.CASCADE)
    is_saved = models.BooleanField(default=False)

    class Meta:
        unique_together = ("user", "resource")
        verbose_name = "User Saved Resource"
        verbose_name_plural = "User Saved Resources"

    def __str__(self):
        return f"{self.user} saved {self.resource} ({'Yes' if self.is_saved else 'No'})"
