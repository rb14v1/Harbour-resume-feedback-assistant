from rest_framework import serializers

from apps.accounts.models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "email",
            "full_name",
            "role",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["id", "role", "is_active", "date_joined"]


class RegisterSerializer(serializers.ModelSerializer):
    """Simple self-service registration. Not required for the demo (seed
    data covers the demo accounts) but kept for completeness."""

    password = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ["id", "email", "full_name", "password"]

    def create(self, validated_data):
        password = validated_data.pop("password")
        user = User(role=User.Role.CANDIDATE, **validated_data)
        user.set_password(password)
        user.save()
        return user
