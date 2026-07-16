from django.contrib import admin
from .models import Category, Task, TaskShare


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "owner", "created_at"]
    list_filter = ["owner"]
    search_fields = ["name", "owner__username"]


@admin.register(Task)
class TaskAdmin(admin.ModelAdmin):
    list_display = ["title", "owner", "status", "category", "due_date", "created_at"]
    list_filter = ["status", "category", "owner"]
    search_fields = ["title", "description", "owner__username"]
    date_hierarchy = "created_at"


@admin.register(TaskShare)
class TaskShareAdmin(admin.ModelAdmin):
    list_display = ["task", "shared_with", "permission", "created_at"]
    list_filter = ["permission"]
    search_fields = ["task__title", "shared_with__username"]
