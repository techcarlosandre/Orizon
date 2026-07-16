"""
Auth tests — registration, login, logout and JWT blacklist.

Key business-logic cases covered:
- Duplicate username/email returns 400 (not 500 or silent)
- Refresh token is rejected after logout, proving the blacklist is active
  and ROTATE_REFRESH_TOKENS/BLACKLIST_AFTER_ROTATION work together.
"""
import pytest
from rest_framework import status

from tests.conftest import get_auth_client

REGISTER = "/api/auth/register/"
LOGIN = "/api/auth/login/"
LOGOUT = "/api/auth/logout/"
REFRESH = "/api/auth/refresh/"


# ── Registration ───────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestRegister:
    def test_success_returns_201_with_tokens_and_user(self, api_client):
        payload = {
            "username": "alice",
            "email": "alice@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        resp = api_client.post(REGISTER, payload)
        assert resp.status_code == status.HTTP_201_CREATED
        assert "access" in resp.data
        assert "refresh" in resp.data
        assert resp.data["user"]["username"] == "alice"

    def test_duplicate_username_returns_400(self, api_client, make_user):
        make_user(username="alice")
        payload = {
            "username": "alice",
            "email": "other@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        resp = api_client.post(REGISTER, payload)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        # Response must point to the offending field
        assert "username" in resp.data

    def test_duplicate_email_returns_400(self, api_client, make_user):
        make_user(email="taken@example.com")
        payload = {
            "username": "newuser",
            "email": "taken@example.com",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        resp = api_client.post(REGISTER, payload)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert "email" in resp.data

    def test_password_mismatch_returns_400(self, api_client):
        payload = {
            "username": "user",
            "email": "user@example.com",
            "password": "SecurePass123!",
            "password_confirm": "DifferentPass456!",
        }
        resp = api_client.post(REGISTER, payload)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_email_returns_400(self, api_client):
        payload = {
            "username": "user",
            "password": "SecurePass123!",
            "password_confirm": "SecurePass123!",
        }
        resp = api_client.post(REGISTER, payload)
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ── Login ──────────────────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLogin:
    def test_success_returns_200_with_tokens(self, api_client, make_user):
        make_user(username="alice", password="TestPass123!")
        resp = api_client.post(LOGIN, {"username": "alice", "password": "TestPass123!"})
        assert resp.status_code == status.HTTP_200_OK
        assert "access" in resp.data
        assert "refresh" in resp.data

    def test_wrong_password_returns_401(self, api_client, make_user):
        make_user(username="alice", password="TestPass123!")
        resp = api_client.post(LOGIN, {"username": "alice", "password": "WrongPass!"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_nonexistent_user_returns_401(self, api_client):
        resp = api_client.post(LOGIN, {"username": "ghost", "password": "any"})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_missing_fields_returns_400(self, api_client):
        resp = api_client.post(LOGIN, {"username": "alice"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST


# ── Logout + Blacklist ─────────────────────────────────────────────────────────

@pytest.mark.django_db
class TestLogoutAndBlacklist:
    def test_logout_success_returns_200(self, make_user):
        user = make_user()
        client, refresh_str = get_auth_client(user)
        resp = client.post(LOGOUT, {"refresh": refresh_str})
        assert resp.status_code == status.HTTP_200_OK

    def test_refresh_token_rejected_after_logout_proves_blacklist_active(
        self, api_client, make_user
    ):
        """
        Critical business-logic test:
        1. Login → get refresh token
        2. Logout → token is blacklisted
        3. Use the same refresh token → must get 401

        This proves INSTALLED_APPS includes token_blacklist,
        ROTATE_REFRESH_TOKENS=True and BLACKLIST_AFTER_ROTATION=True
        are all wired together correctly.
        """
        user = make_user()
        client, refresh_str = get_auth_client(user)

        # Step 1: logout blacklists the token
        logout_resp = client.post(LOGOUT, {"refresh": refresh_str})
        assert logout_resp.status_code == status.HTTP_200_OK, (
            "Logout failed — cannot proceed with blacklist assertion"
        )

        # Step 2: the same refresh token must now be rejected
        refresh_resp = api_client.post(REFRESH, {"refresh": refresh_str})
        assert refresh_resp.status_code == status.HTTP_401_UNAUTHORIZED, (
            "Blacklisted refresh token was accepted — "
            "check that token_blacklist is in INSTALLED_APPS and "
            "BLACKLIST_AFTER_ROTATION=True in SIMPLE_JWT"
        )

    def test_refresh_works_before_logout(self, api_client, make_user):
        """Baseline: confirm refresh works when NOT logged out."""
        user = make_user()
        _, refresh_str = get_auth_client(user)
        resp = api_client.post(REFRESH, {"refresh": refresh_str})
        assert resp.status_code == status.HTTP_200_OK

    def test_logout_requires_authentication(self, api_client, make_user):
        user = make_user()
        _, refresh_str = get_auth_client(user)
        # No Authorization header
        resp = api_client.post(LOGOUT, {"refresh": refresh_str})
        assert resp.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_without_refresh_body_returns_400(self, make_user):
        user = make_user()
        client, _ = get_auth_client(user)
        resp = client.post(LOGOUT, {})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_logout_with_invalid_token_returns_400(self, make_user):
        user = make_user()
        client, _ = get_auth_client(user)
        resp = client.post(LOGOUT, {"refresh": "not.a.real.token"})
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
