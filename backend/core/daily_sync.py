import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "backend.settings")
django.setup()

from core.models import Tag, Resource
import requests

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


sync_resources_and_tags()
