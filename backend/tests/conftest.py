"""
Shared pytest fixtures and helpers for all test modules.

Conventions:
- make_* fixtures are factories (callables) — call them inside tests to create objects.
- get_auth_client() is a plain helper function, not a fixture, so it can be
  called multiple times inside a single test without fixture limitations.
- All fixtures that touch the DB depend on `db` implicitly via their models;
  tests must still carry @pytest.mark.django_db.
"""
import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.tasks.models import Category, Task, TaskShare

User = get_user_model()


# ── Stateless helpers (not fixtures) ──────────────────────────────────────────

def get_auth_client(user):
    """
    Return (APIClient with JWT Bearer, refresh_token_str) for the given user.
    Call this inside a test whenever you need an authenticated client.
    """
    client = APIClient()
    refresh = RefreshToken.for_user(user)
    client.credentials(HTTP_AUTHORIZATION=f"Bearer {str(refresh.access_token)}")
    return client, str(refresh)


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest.fixture
def api_client():
    """Unauthenticated DRF APIClient."""
    return APIClient()


@pytest.fixture
def make_user(db):
    """
    Factory for User instances.
    Each call within a test gets a unique username/email via a per-call counter.
    """
    _seq = [0]

    def factory(username=None, email=None, password="TestPass123!"):
        _seq[0] += 1
        n = _seq[0]
        return User.objects.create_user(
            username=username or f"user{n}",
            email=email or f"user{n}@example.com",
            password=password,
        )

    return factory


@pytest.fixture
def make_category(db):
    """Factory for Category instances."""

    def factory(owner, name="Categoria"):
        return Category.objects.create(owner=owner, name=name)

    return factory


@pytest.fixture
def make_task(db):
    """Factory for Task instances."""

    def factory(owner, title="Tarefa de teste", **kwargs):
        return Task.objects.create(owner=owner, title=title, **kwargs)

    return factory


@pytest.fixture
def make_share(db):
    """Factory for TaskShare instances."""

    def factory(task, shared_with, permission=TaskShare.Permission.VIEW):
        return TaskShare.objects.create(
            task=task,
            shared_with=shared_with,
            permission=permission,
        )

    return factory
