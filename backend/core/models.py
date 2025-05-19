from django.db import models
from django.contrib.auth.models import BaseUserManager, AbstractBaseUser, PermissionsMixin


class CustomUserManager(BaseUserManager):
    def create_user(self, email, username, password=None, **extra_fields):
        if not email:
            raise ValueError('Users must have an email')
        if not username:
            raise ValueError('Users must have a username')
        
        email = self.normalize_email(email)
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save()

        return user
    
    def create_superuser(self, email, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        return self.create_user(email, username, password, **extra_fields)
    

class CustomUser(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    username = models.CharField(max_length=50, unique=True)
    phone = models.CharField(max_length=20, unique=True, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']


    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'


    def __str__(self):
        return f'{self.email} - {self.username}'
    

class Tag(models.Model):
    external_id = models.CharField(max_length=255, unique=True)
    tag = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.tag}'
    
class Resource(models.Model):
    external_id = models.CharField(max_length=255, unique=True)
    author = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    url = models.URLField(max_length=1500)
    created_at = models.DateTimeField(null=True, blank=True)
    tags = models.ManyToManyField(Tag, related_name='resources')

    def __str__(self):
        return f'{self.author} - {self.name}'    