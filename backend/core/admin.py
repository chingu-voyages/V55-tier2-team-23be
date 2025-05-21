from django.contrib import admin
from .models import CustomUser, Resource, Tag, UserRating


admin.site.register(CustomUser)
admin.site.register(Resource)
admin.site.register(Tag)
admin.site.register(UserRating)