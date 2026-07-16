"""
Sharing tests — the business-logic core of the permission model.

Every case listed in the technical review is covered here:
- view permission  → can read, can toggle_status, CANNOT edit fields
- edit permission  → can read, can toggle_status, CAN edit fields
- no relation      → cannot even retrieve (403/404)
- share() twice    → 201 first, 200 second (idempotent update)
- owner only       → delete, share, revoke
- revoke           → removes access completely
"""
import pytest
from rest_framework import status

from apps.tasks.models import Task, TaskShare
from tests.conftest import get_auth_client

TASKS = "/api/tasks/"


def task_url(task):
    return f"{TASKS}{task.pk}/"


def share_url(task):
    return f"{TASKS}{task.pk}/share/"


def shares_url(task):
    return f"{TASKS}{task.pk}/shares/"


def revoke_url(task, share):
    return f"{TASKS}{task.pk}/shares/{share.pk}/"


# ── Share creation (POST /tasks/{id}/share/) ───────────────────────────────────

@pytest.mark.django_db
class TestShareCreate:
    def test_share_by_username_returns_201(self, make_user, make_task):
        alice = make_user(username="alice")
        bob = make_user(username="bob")
        task = make_task(alice)
        client, _ = get_auth_client(alice)
        resp = client.post(share_url(task), {"username": "bob", "permission": "view"})
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["permission"] == "view"
        assert resp.data["shared_with"]["username"] == "bob"

    def test_share_by_email_returns_201(self, make_user, make_task):
        alice = make_user(username="alice")
        bob = make_user(username="bob", email="bob@example.com")
        task = make_task(alice)
        client, _ = get_auth_client(alice)
        resp = client.post(share_url(task), {"email": "bob@example.com", "permission": "edit"})
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["permission"] == "edit"

    def test_share_idempotent_first_201_second_200_updates_permission(
        self, make_user, make_task
    ):
        """
        Sharing the same task with the same user twice must:
        - Return 201 on the first call (created)
        - Return 200 on the second call (updated) — not 409 or 400
        - The permission must be updated to the new value.
        """
        alice = make_user(username="alice")
        bob = make_user(username="bob")
        task = make_task(alice)
        client, _ = get_auth_client(alice)

        resp1 = client.post(share_url(task), {"username": "bob", "permission": "view"})
        assert resp1.status_code == status.HTTP_201_CREATED

        resp2 = client.post(share_url(task), {"username": "bob", "permission": "edit"})
        assert resp2.status_code == status.HTTP_200_OK
        assert resp2.data["permission"] == "edit"

        # Confirm DB has only one share with updated permission
        shares = TaskShare.objects.filter(task=task, shared_with__username="bob")
        assert shares.count() == 1
        assert shares.first().permission == TaskShare.Permission.EDIT

    def test_cannot_share_with_yourself(self, make_user, make_task):
        alice = make_user(username="alice")
        task = make_task(alice)
        client, _ = get_auth_client(alice)
        resp = client.post(share_url(task), {"username": "alice", "permission": "view"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_non_owner_cannot_share_403(self, make_user, make_task, make_share):
        alice = make_user(username="alice")
        bob = make_user(username="bob")
        carol = make_user(username="carol")
        task = make_task(alice)
        make_share(task, bob, TaskShare.Permission.EDIT)
        bob_client, _ = get_auth_client(bob)
        resp = bob_client.post(share_url(task), {"username": "carol", "permission": "view"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN

    def test_share_nonexistent_username_returns_400(self, make_user, make_task):
        alice = make_user(username="alice")
        task = make_task(alice)
        client, _ = get_auth_client(alice)
        resp = client.post(share_url(task), {"username": "nobody", "permission": "view"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ── Retrieve access ────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRetrievePermissions:
    def test_view_permission_can_retrieve_200(self, make_user, make_task, make_share):
        alice = make_user()
        bob = make_user()
        task = make_task(alice)
        make_share(task, bob, TaskShare.Permission.VIEW)
        bob_client, _ = get_auth_client(bob)
        assert bob_client.get(task_url(task)).status_code == status.HTTP_200_OK

    def test_edit_permission_can_retrieve_200(self, make_user, make_task, make_share):
        alice = make_user()
        bob = make_user()
        task = make_task(alice)
        make_share(task, bob, TaskShare.Permission.EDIT)
        bob_client, _ = get_auth_client(bob)
        assert bob_client.get(task_url(task)).status_code == status.HTTP_200_OK

    def test_unrelated_user_cannot_retrieve(self, make_user, make_task):
        """No relation (not owner, not in shares) → must not see the task."""
        alice = make_user()
        bob = make_user()
        task = make_task(alice)
        bob_client, _ = get_auth_client(bob)
        resp = bob_client.get(task_url(task))
        assert resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)


# ── Update (edit title/description) permissions ────────────────────────────────

@pytest.mark.django_db
class TestUpdatePermissions:
    def test_view_permission_cannot_edit_title_403(self, make_user, make_task, make_share):
        """
        Critical business rule: 'view' permission allows reading and toggling
        status ONLY. Editing title/description/category must be rejected.
        """
        alice = make_user()
        bob = make_user()
        task = make_task(alice, "Original title")
        make_share(task, bob, TaskShare.Permission.VIEW)
        bob_client, _ = get_auth_client(bob)

        resp = bob_client.patch(task_url(task), {"title": "Hacked title"})
        assert resp.status_code == status.HTTP_403_FORBIDDEN

        # Confirm title was NOT changed in the database
        task.refresh_from_db()
        assert task.title == "Original title"

    def test_edit_permission_can_edit_title_200(self, make_user, make_task, make_share):
        alice = make_user()
        bob = make_user()
        task = make_task(alice, "Original title")
        make_share(task, bob, TaskShare.Permission.EDIT)
        bob_client, _ = get_auth_client(bob)

        resp = bob_client.patch(task_url(task), {"title": "Updated title"})
        assert resp.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.title == "Updated title"

    def test_unrelated_user_cannot_edit_403_or_404(self, make_user, make_task):
        alice = make_user()
        bob = make_user()
        task = make_task(alice)
        bob_client, _ = get_auth_client(bob)
        resp = bob_client.patch(task_url(task), {"title": "Hack"})
        assert resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)


# ── Toggle status permissions ──────────────────────────────────────────────────

@pytest.mark.django_db
class TestToggleStatus:
    TOGGLE = "{TASKS}{pk}/toggle_status/"

    def _toggle(self, client, task):
        return client.patch(f"{TASKS}{task.pk}/toggle_status/")

    def test_owner_can_toggle_200(self, make_user, make_task):
        user = make_user()
        task = make_task(user)
        client, _ = get_auth_client(user)
        resp = self._toggle(client, task)
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["status"] == Task.Status.COMPLETED

    def test_view_permission_can_toggle_200(self, make_user, make_task, make_share):
        """'view' permission grants toggle_status access."""
        alice = make_user()
        bob = make_user()
        task = make_task(alice)
        make_share(task, bob, TaskShare.Permission.VIEW)
        bob_client, _ = get_auth_client(bob)
        resp = self._toggle(bob_client, task)
        assert resp.status_code == status.HTTP_200_OK
        task.refresh_from_db()
        assert task.status == Task.Status.COMPLETED

    def test_edit_permission_can_toggle_200(self, make_user, make_task, make_share):
        """'edit' permission also grants toggle_status access."""
        alice = make_user()
        bob = make_user()
        task = make_task(alice)
        make_share(task, bob, TaskShare.Permission.EDIT)
        bob_client, _ = get_auth_client(bob)
        resp = self._toggle(bob_client, task)
        assert resp.status_code == status.HTTP_200_OK

    def test_unrelated_user_cannot_toggle_403_or_404(self, make_user, make_task):
        alice = make_user()
        bob = make_user()
        task = make_task(alice)
        bob_client, _ = get_auth_client(bob)
        resp = self._toggle(bob_client, task)
        assert resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)

    def test_toggle_flips_pending_to_completed_and_back(self, make_user, make_task):
        user = make_user()
        task = make_task(user)
        client, _ = get_auth_client(user)
        assert task.status == Task.Status.PENDING
        self._toggle(client, task)
        task.refresh_from_db()
        assert task.status == Task.Status.COMPLETED
        self._toggle(client, task)
        task.refresh_from_db()
        assert task.status == Task.Status.PENDING


# ── Revoke share ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRevokeShare:
    def test_owner_can_revoke_204(self, make_user, make_task, make_share):
        alice = make_user()
        bob = make_user()
        task = make_task(alice)
        share = make_share(task, bob)
        alice_client, _ = get_auth_client(alice)
        resp = alice_client.delete(revoke_url(task, share))
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_after_revoke_shared_user_loses_access(self, make_user, make_task, make_share):
        alice = make_user()
        bob = make_user()
        task = make_task(alice)
        share = make_share(task, bob)

        alice_client, _ = get_auth_client(alice)
        bob_client, _ = get_auth_client(bob)

        # Bob can access before revoke
        assert bob_client.get(task_url(task)).status_code == status.HTTP_200_OK

        # Alice revokes
        alice_client.delete(revoke_url(task, share))

        # Bob can no longer access
        resp = bob_client.get(task_url(task))
        assert resp.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_404_NOT_FOUND)

    def test_non_owner_cannot_revoke_403(self, make_user, make_task, make_share):
        alice = make_user()
        bob = make_user()
        task = make_task(alice)
        share = make_share(task, bob)
        bob_client, _ = get_auth_client(bob)
        resp = bob_client.delete(revoke_url(task, share))
        assert resp.status_code == status.HTTP_403_FORBIDDEN


# ── List shares ────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestListShares:
    def test_owner_can_list_shares(self, make_user, make_task, make_share):
        alice = make_user()
        bob = make_user()
        carol = make_user()
        task = make_task(alice)
        make_share(task, bob)
        make_share(task, carol)
        client, _ = get_auth_client(alice)
        resp = client.get(shares_url(task))
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data) == 2

    def test_non_owner_cannot_list_shares_403(self, make_user, make_task, make_share):
        alice = make_user()
        bob = make_user()
        task = make_task(alice)
        make_share(task, bob)
        bob_client, _ = get_auth_client(bob)
        resp = bob_client.get(shares_url(task))
        assert resp.status_code == status.HTTP_403_FORBIDDEN
