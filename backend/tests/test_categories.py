"""
Category CRUD tests.

Verifies owner-scoping (users see only their own categories),
duplicate name enforcement, and standard CRUD responses.
"""
import pytest
from rest_framework import status

from tests.conftest import get_auth_client

CATEGORIES = "/api/categories/"


@pytest.mark.django_db
class TestCategoryCRUD:
    def test_create_returns_201(self, make_user):
        user = make_user()
        client, _ = get_auth_client(user)
        resp = client.post(CATEGORIES, {"name": "Trabalho"})
        assert resp.status_code == status.HTTP_201_CREATED
        assert resp.data["name"] == "Trabalho"

    def test_list_scoped_to_owner(self, make_user, make_category):
        alice = make_user()
        bob = make_user()
        make_category(alice, "Alice Cat")
        make_category(bob, "Bob Cat")

        client, _ = get_auth_client(alice)
        resp = client.get(CATEGORIES)
        names = [c["name"] for c in resp.data]
        assert "Alice Cat" in names
        assert "Bob Cat" not in names

    def test_duplicate_name_per_owner_returns_400(self, make_user, make_category):
        user = make_user()
        make_category(user, "Trabalho")
        client, _ = get_auth_client(user)
        resp = client.post(CATEGORIES, {"name": "Trabalho"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_same_name_allowed_across_different_owners(self, make_user):
        alice = make_user()
        bob = make_user()
        alice_client, _ = get_auth_client(alice)
        bob_client, _ = get_auth_client(bob)
        assert alice_client.post(CATEGORIES, {"name": "Trabalho"}).status_code == 201
        assert bob_client.post(CATEGORIES, {"name": "Trabalho"}).status_code == 201

    def test_update_own_category(self, make_user, make_category):
        user = make_user()
        cat = make_category(user, "Old Name")
        client, _ = get_auth_client(user)
        resp = client.patch(f"{CATEGORIES}{cat.pk}/", {"name": "New Name"})
        assert resp.status_code == status.HTTP_200_OK
        assert resp.data["name"] == "New Name"

    def test_delete_own_category(self, make_user, make_category):
        user = make_user()
        cat = make_category(user)
        client, _ = get_auth_client(user)
        resp = client.delete(f"{CATEGORIES}{cat.pk}/")
        assert resp.status_code == status.HTTP_204_NO_CONTENT

    def test_cannot_access_other_owners_category(self, make_user, make_category):
        alice = make_user()
        bob = make_user()
        bob_cat = make_category(bob, "Bob's")
        client, _ = get_auth_client(alice)
        resp = client.get(f"{CATEGORIES}{bob_cat.pk}/")
        assert resp.status_code == status.HTTP_404_NOT_FOUND

    def test_unauthenticated_returns_401(self, api_client):
        assert api_client.get(CATEGORIES).status_code == status.HTTP_401_UNAUTHORIZED
