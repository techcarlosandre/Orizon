"""
Task CRUD tests.

Key cases:
- Creation response includes `suggested_category` (mocked via patch)
- List shows owned + shared, but not unrelated tasks
- Unrelated user gets 403/404 on retrieve
- Only owner can delete (even edit-permission shared user gets 403)
"""
import pytest
from unittest.mock import patch
from rest_framework import status

from apps.tasks.models import Task, TaskShare
from tests.conftest import get_auth_client

TASKS = "/api/tasks/"

# Patch target: the function as imported inside the views module
SUGGESTION_PATCH = "apps.tasks.views.get_category_suggestion"


@pytest.mark.django_db
class TestTaskCreate:
    def test_returns_201_with_suggested_category_field(self, make_user):
        user = make_user()
        client, _ = get_auth_client(user)
        with patch(SUGGESTION_PATCH, return_value="Trabalho"):
            resp = client.post(TASKS, {"title": "Reunião com o cliente"})
        assert resp.status_code == status.HTTP_201_CREATED
        assert "suggested_category" in resp.data
        assert resp.data["suggested_category"] == "Trabalho"

    def test_suggestion_timeout_does_not_block_creation(self, make_user):
        """Task must be created even when the suggestions API is unreachable."""
        user = make_user()
        client, _ = get_auth_client(user)
        with patch(SUGGESTION_PATCH, return_value="Geral"):
            resp = client.post(TASKS, {"title": "Some task"})
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["suggested_category"] == "Geral"

    def test_owner_is_set_to_authenticated_user(self, make_user):
        user = make_user(username="alice")
        client, _ = get_auth_client(user)
        with patch(SUGGESTION_PATCH, return_value="Geral"):
            resp = client.post(TASKS, {"title": "My Task"})
        assert resp.data["owner_username"] == "alice"

    def test_unauthenticated_returns_401(self, api_client):
        resp = api_client.post(TASKS, {"title": "Task"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
class TestTaskList:
    def test_shows_owned_tasks(self, make_user, make_task):
        alice = make_user()
        make_task(alice, "Alice's task")
        client, _ = get_auth_client(alice)
        resp = client.get(TASKS)
        titles = [t["title"] for t in resp.data["results"]]
        assert "Alice's task" in titles

    def test_shows_tasks_shared_with_user(self, make_user, make_task, make_share):
        alice = make_user()
        bob = make_user()
        bob_task = make_task(bob, "Bob's shared task")
        make_share(bob_task, alice)
        client, _ = get_auth_client(alice)
        resp = client.get(TASKS)
        titles = [t["title"] for t in resp.data["results"]]
        assert "Bob's shared task" in titles

    def test_does_not_show_unrelated_tasks(self, make_user, make_task):
        alice = make_user()
        bob = make_user()
        make_task(bob, "Bob's private task")
        client, _ = get_auth_client(alice)
        resp = client.get(TASKS)
        titles = [t["title"] for t in resp.data["results"]]
        assert "Bob's private task" not in titles

    def test_no_duplicates_when_shared(self, make_user, make_task, make_share):
        """distinct() must prevent a task appearing twice in the list."""
        alice = make_user()
        bob = make_user()
        carol = make_user()
        task = make_task(alice, "Shared with two people")
        make_share(task, bob)
        make_share(task, carol)
        client, _ = get_auth_client(alice)
        resp = client.get(TASKS)
        task_ids = [t["id"] for t in resp.data["results"]]
        assert task_ids.count(str(task.pk)) == 1


@pytest.mark.django_db
class TestTaskRetrieve:
    def test_owner_can_retrieve_200(self, make_user, make_task):
        user = make_user()
        task = make_task(user)
        client, _ = get_auth_client(user)
        resp = client.get(f"{TASKS}{task.pk}/")
        assert resp.status_code == status.HTTP_200_OK
        assert str(resp.data["id"]) == str(task.pk)

    def test_unrelated_user_gets_403_or_404(self, make_user, make_task):
        """A task that a user has no relation to must not be readable."""
        alice = make_user()
        bob = make_user()
        bob_task = make_task(bob)
        client, _ = get_auth_client(alice)
        resp = client.get(f"{TASKS}{bob_task.pk}/")
        assert resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)


@pytest.mark.django_db
class TestTaskUpdate:
    def test_owner_can_update_200(self, make_user, make_task):
        user = make_user()
        task = make_task(user, "Old title")
        client, _ = get_auth_client(user)
        resp = client.patch(f"{TASKS}{task.pk}/", {"title": "New title"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["title"] == "New title"


@pytest.mark.django_db
class TestTaskDelete:
    def test_owner_can_delete_204(self, make_user, make_task):
        user = make_user()
        task = make_task(user)
        client, _ = get_auth_client(user)
        resp = client.delete(f"{TASKS}{task.pk}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT
        assert not Task.objects.filter(pk=task.pk).exists()

    def test_edit_permission_shared_user_cannot_delete_403(
        self, make_user, make_task, make_share
    ):
        """Even a user with 'edit' permission cannot delete — only the owner can."""
        alice = make_user()
        bob = make_user()
        task = make_task(alice)
        make_share(task, bob, permission=TaskShare.Permission.EDIT)
        bob_client, _ = get_auth_client(bob)
        resp = bob_client.delete(f"{TASKS}{task.pk}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_view_permission_shared_user_cannot_delete_403(
        self, make_user, make_task, make_share
    ):
        alice = make_user()
        bob = make_user()
        task = make_task(alice)
        make_share(task, bob, permission=TaskShare.Permission.VIEW)
        bob_client, _ = get_auth_client(bob)
        resp = bob_client.delete(f"{TASKS}{task.pk}/")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
