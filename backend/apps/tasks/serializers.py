"""
Tasks serializers.

Hierarchy (DRY — no field duplication):
  CategorySerializer         → CRUD de categorias
  TaskShareSerializer        → leitura de compartilhamentos
  TaskShareCreateSerializer  → escrita (aceita username OU email)
  TaskListSerializer         → listagem leve de tarefas (sem shares)
  TaskDetailSerializer       → detalhe / criação / edição (com shares aninhados)
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Category, Task, TaskShare

User = get_user_model()


# ── Category ──────────────────────────────────────────────────────────────────

class CategorySerializer(serializers.ModelSerializer):
    owner_username = serializers.CharField(source="owner.username", read_only=True)

    class Meta:
        model = Category
        fields = ["id", "name", "owner_username", "created_at"]
        read_only_fields = ["id", "owner_username", "created_at"]

    def validate_name(self, value: str) -> str:
        """Enforce unique category name per owner at serializer level for cleaner error messages."""
        owner = self.context["request"].user
        qs = Category.objects.filter(owner=owner, name__iexact=value)
        # Exclude current instance on update
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("Você já possui uma categoria com este nome.")
        return value


# ── TaskShare ─────────────────────────────────────────────────────────────────

class SharedWithUserSerializer(serializers.ModelSerializer):
    """Minimal user representation nested inside TaskShareSerializer."""

    class Meta:
        model = User
        fields = ["id", "username", "email"]
        read_only_fields = fields


class TaskShareSerializer(serializers.ModelSerializer):
    """Read-only representation of a share, returned in task detail and share list."""

    shared_with = SharedWithUserSerializer(read_only=True)

    class Meta:
        model = TaskShare
        fields = ["id", "shared_with", "permission", "created_at"]
        read_only_fields = fields


class TaskShareCreateSerializer(serializers.Serializer):
    """
    Input serializer for POST /tasks/{id}/share/.

    Accepts either 'username' or 'email' to identify the target user.
    Validates that:
    - the target user exists
    - the owner is not sharing with themselves
    - the task is not already shared with the target user
    """

    username = serializers.CharField(required=False, allow_blank=False)
    email = serializers.EmailField(required=False)
    permission = serializers.ChoiceField(
        choices=TaskShare.Permission.choices,
        default=TaskShare.Permission.VIEW,
    )

    def validate(self, attrs: dict) -> dict:
        if not attrs.get("username") and not attrs.get("email"):
            raise serializers.ValidationError(
                "Informe 'username' ou 'email' do usuário com quem compartilhar."
            )
        return attrs

    def resolve_user(self) -> User:
        """Look up target user by username or email. Raises ValidationError if not found."""
        data = self.validated_data
        try:
            if username := data.get("username"):
                return User.objects.get(username=username)
            return User.objects.get(email__iexact=data["email"])
        except User.DoesNotExist:
            field = "username" if data.get("username") else "email"
            raise serializers.ValidationError({field: "Usuário não encontrado."})


# ── Task ──────────────────────────────────────────────────────────────────────

class CategoryNestedSerializer(serializers.ModelSerializer):
    """Lightweight nested category (id + name) for task responses."""

    class Meta:
        model = Category
        fields = ["id", "name"]


class TaskListSerializer(serializers.ModelSerializer):
    """
    Lightweight serializer for task listings.
    Excludes full share list to reduce payload size.
    """

    category = CategoryNestedSerializer(read_only=True)
    category_id = serializers.PrimaryKeyRelatedField(
        queryset=Category.objects.none(),  # overridden in __init__
        source="category",
        write_only=True,
        required=False,
        allow_null=True,
    )
    owner_username = serializers.CharField(source="owner.username", read_only=True)
    is_shared_with_me = serializers.SerializerMethodField()

    class Meta:
        model = Task
        fields = [
            "id", "title", "status", "due_date",
            "category", "category_id",
            "owner_username", "is_shared_with_me",
            "created_at", "updated_at",
        ]
        read_only_fields = ["id", "owner_username", "is_shared_with_me", "created_at", "updated_at"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            # Restrict category choices to the owner's categories
            self.fields["category_id"].queryset = Category.objects.filter(owner=request.user)

    def get_is_shared_with_me(self, obj: Task) -> bool:
        request = self.context.get("request")
        if not request:
            return False
        return obj.owner_id != request.user.pk


class TaskDetailSerializer(TaskListSerializer):
    """
    Full serializer for task retrieve/create/update.
    Adds description and nested shares list.
    """

    shares = TaskShareSerializer(many=True, read_only=True)

    class Meta(TaskListSerializer.Meta):
        fields = TaskListSerializer.Meta.fields + ["description", "shares"]
