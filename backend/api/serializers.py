from rest_framework import serializers
from core.models import CustomUser, Resource
from django.contrib.auth import get_user_model, authenticate

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField()

    class Meta:
        model = CustomUser
        fields = ["email", "username", "password", "password2"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate(self, data):
        password = data["password"]
        if password != data["password2"]:
            raise serializers.ValidationError("Passwords do not match!")
        return data

    def create(self, validated_data):
        user = User(
            email=validated_data["email"],
            username=validated_data["username"],
            is_active=True,
        )

        user.set_password(validated_data["password"])
        user.save()

        return user


class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField()

    def validate(self, data):
        user = authenticate(
            request=self.context.get("request"),
            email=data["email"],
            password=data["password"],
        )

        if not user:
            raise serializers.ValidationError("Invalid password or email!")

        data["user"] = user
        return data


class ResourceSerializer(serializers.ModelSerializer):
    tags = serializers.SlugRelatedField(many=True, read_only=True, slug_field="tag")

    class Meta:
        model = Resource
        fields = "__all__"
