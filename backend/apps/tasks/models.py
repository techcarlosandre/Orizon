"""
Tasks domain models: Category, Task, TaskShare.

Design decisions:
- UUID PKs: avoid resource enumeration in URLs.
- TaskShare.permission choices (view/edit): explicit, minimal, testable.
  See README for full permission matrix.
- category is nullable on Task: tasks can exist without a category.
- due_date is nullable: not all tasks have deadlines.
"""
import uuid
from django.conf import settings
from django.db import models


class Category(models.Model):
    """
    A task category scoped to the owning user.
    Users see only their own categories.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=100)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="categories",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Categoria"
        verbose_name_plural = "Categorias"
        ordering = ["name"]
        # A user cannot have two categories with the same name.
        unique_together = [("owner", "name")]

    def __str__(self) -> str:
        return f"{self.name} ({self.owner.username})"


class Task(models.Model):
    """A task owned by a user, optionally shared with others."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pendente"
        COMPLETED = "completed", "Concluída"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="tasks",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    due_date = models.DateField(null=True, blank=True)
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_tasks",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Tarefa"
        verbose_name_plural = "Tarefas"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return self.title

    @property
    def is_completed(self) -> bool:
        return self.status == self.Status.COMPLETED

    def toggle_status(self) -> None:
        """Flip status between pending and completed."""
        if self.is_completed:
            self.status = self.Status.PENDING
        else:
            self.status = self.Status.COMPLETED
        self.save(update_fields=["status", "updated_at"])


class TaskShare(models.Model):
    """
    Represents a sharing relationship between a Task and a User.

    Permission matrix:
    - 'view': shared user can read the task and toggle its status only.
    - 'edit': shared user can read, edit all fields, and toggle its status.
    Only the owner can delete, share, or revoke shares.
    """

    class Permission(models.TextChoices):
        VIEW = "view", "Visualizar"
        EDIT = "edit", "Editar"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    task = models.ForeignKey(
        Task,
        on_delete=models.CASCADE,
        related_name="shares",
    )
    shared_with = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="shared_tasks",
    )
    permission = models.CharField(
        max_length=10,
        choices=Permission.choices,
        default=Permission.VIEW,
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Compartilhamento"
        verbose_name_plural = "Compartilhamentos"
        # A task can only be shared once per user.
        unique_together = [("task", "shared_with")]

    def __str__(self) -> str:
        return f"{self.task.title} → {self.shared_with.username} [{self.permission}]"
