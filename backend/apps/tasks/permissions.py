"""
Centralized permission classes for the Tasks domain.

Design principle (SOLID — Single Responsibility):
Each class encodes exactly one access rule. ViewSets declare which
permission is needed per action via get_permissions(), keeping views
free of inline if/else access logic.

Permission matrix (as documented in the README):
┌──────────────────┬────────┬───────────┬────────┬──────────────────────────┐
│ Action           │ owner  │ share=edit│share=view│  unauthenticated        │
├──────────────────┼────────┼───────────┼────────┼──────────────────────────┤
│ retrieve         │ ✅     │ ✅        │ ✅     │ ❌                       │
│ update           │ ✅     │ ✅        │ ❌     │ ❌                       │
│ partial_update   │ ✅     │ ✅        │ ❌     │ ❌                       │
│ destroy          │ ✅     │ ❌        │ ❌     │ ❌                       │
│ toggle_status    │ ✅     │ ✅        │ ✅     │ ❌                       │
│ share/revoke     │ ✅     │ ❌        │ ❌     │ ❌                       │
│ list shares      │ ✅     │ ❌        │ ❌     │ ❌                       │
└──────────────────┴────────┴───────────┴────────┴──────────────────────────┘
"""
from rest_framework.permissions import BasePermission

from .models import TaskShare


class IsTaskOwner(BasePermission):
    """
    Grants access only to the owner of the task.

    Used for: destroy, share (POST), shares (GET), revoke_share (DELETE).
    """

    message = "Apenas o dono da tarefa pode realizar esta ação."

    def has_object_permission(self, request, view, obj) -> bool:
        return obj.owner_id == request.user.pk


class IsTaskOwnerOrSharedWith(BasePermission):
    """
    Grants access to the owner OR any user the task was shared with,
    regardless of permission level (view or edit).

    Used for: retrieve, toggle_status.
    """

    message = "Você não tem acesso a esta tarefa."

    def has_object_permission(self, request, view, obj) -> bool:
        if obj.owner_id == request.user.pk:
            return True
        return obj.shares.filter(shared_with_id=request.user.pk).exists()


class IsTaskOwnerOrSharedWithEdit(BasePermission):
    """
    Grants write access to the owner OR shared users with 'edit' permission.
    Shared users with 'view' permission cannot write.

    Used for: update, partial_update.
    """

    message = "Você não tem permissão para editar esta tarefa."

    def has_object_permission(self, request, view, obj) -> bool:
        if obj.owner_id == request.user.pk:
            return True
        return obj.shares.filter(
            shared_with_id=request.user.pk,
            permission=TaskShare.Permission.EDIT,
        ).exists()
