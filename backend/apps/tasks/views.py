"""
Tasks ViewSets.

Design principles applied:
- Permission declared per action via get_permissions() — no inline if/else.
- Queryset scoped to accessible tasks (owned + shared) — 404 for truly invisible tasks.
- perform_create() sets owner automatically — serializer stays clean.
- Custom actions (toggle_status, share, shares, revoke_share) follow the same
  retrieve-then-check-permission pattern as standard DRF actions.
- Category ViewSet is fully owner-scoped: users never see other users' categories.
"""
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from .filters import TaskFilter
from .models import Category, Task, TaskShare
from .pagination import TaskPagination
from .permissions import IsTaskOwner, IsTaskOwnerOrSharedWith, IsTaskOwnerOrSharedWithEdit
from .serializers import (
    CategorySerializer,
    TaskDetailSerializer,
    TaskListSerializer,
    TaskShareCreateSerializer,
    TaskShareSerializer,
)

User = get_user_model()


class CategoryViewSet(ModelViewSet):
    """
    CRUD de categorias.
    Each user sees and manages only their own categories.
    """

    serializer_class = CategorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Category.objects.filter(owner=self.request.user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class TaskViewSet(ModelViewSet):
    """
    CRUD de tarefas + compartilhamento.

    Action → permission mapping (declared, not scattered in ifs):
      list / create        → IsAuthenticated
      retrieve             → IsTaskOwnerOrSharedWith (any share level)
      update / partial     → IsTaskOwnerOrSharedWithEdit (edit permission only)
      destroy              → IsTaskOwner (owner only)
      toggle_status        → IsTaskOwnerOrSharedWith (any share level)
      share / revoke_share → IsTaskOwner (owner only)
      shares (list)        → IsTaskOwner (owner only)
    """

    pagination_class = TaskPagination
    filterset_class = TaskFilter
    ordering_fields = ["created_at", "due_date", "title", "status"]
    ordering = ["-created_at"]

    # ── Permission routing ─────────────────────────────────────────────────────
    _PERMISSION_MAP = {
        "list": [IsAuthenticated],
        "create": [IsAuthenticated],
        "retrieve": [IsTaskOwnerOrSharedWith],
        "update": [IsTaskOwnerOrSharedWithEdit],
        "partial_update": [IsTaskOwnerOrSharedWithEdit],
        "destroy": [IsTaskOwner],
        "toggle_status": [IsTaskOwnerOrSharedWith],
        "share": [IsTaskOwner],
        "shares": [IsTaskOwner],
        "revoke_share": [IsTaskOwner],
    }

    def get_permissions(self):
        perm_classes = self._PERMISSION_MAP.get(self.action, [IsAuthenticated])
        return [cls() for cls in perm_classes]

    # ── Queryset ───────────────────────────────────────────────────────────────
    def get_queryset(self):
        """
        Returns tasks that are visible to the current user:
        owned tasks + tasks explicitly shared with the user.
        distinct() prevents duplicates from the shares join.
        """
        user = self.request.user
        return (
            Task.objects.filter(Q(owner=user) | Q(shares__shared_with=user))
            .select_related("owner", "category")
            .prefetch_related("shares__shared_with")
            .distinct()
        )

    # ── Serializer selection ───────────────────────────────────────────────────
    def get_serializer_class(self):
        if self.action == "list":
            return TaskListSerializer
        return TaskDetailSerializer

    # ── Standard CRUD overrides ────────────────────────────────────────────────
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    # ── Custom actions ─────────────────────────────────────────────────────────

    @action(detail=True, methods=["patch"], url_path="toggle_status")
    def toggle_status(self, request, pk=None):
        """
        PATCH /api/tasks/{id}/toggle_status/
        Flips status between pending ↔ completed.
        Permission: owner OR any shared user (view or edit).
        """
        task = self.get_object()  # triggers has_object_permission
        task.toggle_status()
        serializer = TaskDetailSerializer(task, context={"request": request})
        return Response(serializer.data)

    @action(detail=True, methods=["post"], url_path="share")
    def share(self, request, pk=None):
        """
        POST /api/tasks/{id}/share/
        Body: { "username": "..." | "email": "...", "permission": "view"|"edit" }
        Permission: owner only.
        """
        task = self.get_object()  # triggers has_object_permission → IsTaskOwner

        serializer = TaskShareCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_user = serializer.resolve_user()

        # Cannot share with yourself
        if target_user == request.user:
            return Response(
                {"detail": "Você não pode compartilhar uma tarefa com você mesmo."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        share, created = TaskShare.objects.get_or_create(
            task=task,
            shared_with=target_user,
            defaults={"permission": serializer.validated_data["permission"]},
        )

        if not created:
            # Update permission if share already exists
            share.permission = serializer.validated_data["permission"]
            share.save(update_fields=["permission"])

        return Response(
            TaskShareSerializer(share).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="shares")
    def shares(self, request, pk=None):
        """
        GET /api/tasks/{id}/shares/
        Lists all active shares for the task.
        Permission: owner only.
        """
        task = self.get_object()  # triggers has_object_permission → IsTaskOwner
        task_shares = task.shares.select_related("shared_with").all()
        serializer = TaskShareSerializer(task_shares, many=True)
        return Response(serializer.data)

    @action(
        detail=True,
        methods=["delete"],
        url_path=r"shares/(?P<share_pk>[0-9a-f-]+)",
    )
    def revoke_share(self, request, pk=None, share_pk=None):
        """
        DELETE /api/tasks/{id}/shares/{share_id}/
        Revokes a specific share by its UUID.
        Permission: owner only.
        """
        task = self.get_object()  # triggers has_object_permission → IsTaskOwner
        share = get_object_or_404(TaskShare, pk=share_pk, task=task)
        share.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
