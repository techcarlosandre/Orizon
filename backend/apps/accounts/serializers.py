"""
Accounts serializers.

RegisterSerializer: validates uniqueness of username/email and creates user.
UserSerializer: read-only representation of the authenticated user.
"""
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Read-only user representation returned after register/login."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "date_joined"]
        read_only_fields = fields


class RegisterSerializer(serializers.ModelSerializer):
    """
    Handles user registration.

    Validates:
    - password complexity (Django's built-in validators)
    - password confirmation match
    - email uniqueness (email is not unique by default in AbstractUser)
    """

    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "password_confirm", "first_name", "last_name"]
        extra_kwargs = {
            "email": {"required": True},
            "first_name": {"required": False},
            "last_name": {"required": False},
        }

    def validate_email(self, value: str) -> str:
        if User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("Este e-mail já está em uso.")
        return value.lower()

    def validate(self, attrs: dict) -> dict:
        if attrs["password"] != attrs.pop("password_confirm"):
            raise serializers.ValidationError({"password_confirm": "As senhas não conferem."})
        return attrs

    def create(self, validated_data: dict) -> User:
        return User.objects.create_user(**validated_data)
