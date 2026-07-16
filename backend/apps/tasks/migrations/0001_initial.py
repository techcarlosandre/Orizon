"""
Tasks initial migration.
Creates Category, Task, and TaskShare models with UUID PKs.
Depends on accounts.0001_initial (custom User must exist first).
"""
import django.db.models.deletion
import uuid
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ("accounts", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="Category",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="categories",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Categoria",
                "verbose_name_plural": "Categorias",
                "ordering": ["name"],
            },
        ),
        migrations.AddConstraint(
            model_name="category",
            constraint=models.UniqueConstraint(
                fields=["owner", "name"],
                name="unique_category_per_owner",
            ),
        ),
        migrations.CreateModel(
            name="Task",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True, default="")),
                (
                    "status",
                    models.CharField(
                        choices=[("pending", "Pendente"), ("completed", "Concluída")],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("due_date", models.DateField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "category",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="tasks",
                        to="tasks.category",
                    ),
                ),
                (
                    "owner",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="owned_tasks",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Tarefa",
                "verbose_name_plural": "Tarefas",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="TaskShare",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "permission",
                    models.CharField(
                        choices=[("view", "Visualizar"), ("edit", "Editar")],
                        default="view",
                        max_length=10,
                    ),
                ),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                (
                    "task",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shares",
                        to="tasks.task",
                    ),
                ),
                (
                    "shared_with",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="shared_tasks",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Compartilhamento",
                "verbose_name_plural": "Compartilhamentos",
            },
        ),
        migrations.AddConstraint(
            model_name="taskshare",
            constraint=models.UniqueConstraint(
                fields=["task", "shared_with"],
                name="unique_share_per_task_user",
            ),
        ),
    ]
