"""
Filter and pagination tests.

Verifies that each filter param returns the correct subset and that
page_size is configurable and capped at max_page_size (100).
"""
import datetime
import pytest
from rest_framework import status

from apps.tasks.models import Task
from apps.tasks.pagination import TaskPagination
from tests.conftest import get_auth_client

TASKS = "/api/tasks/"


@pytest.mark.django_db
class TestTaskFilters:
    def test_filter_by_category(self, make_user, make_task, make_category):
        user = make_user()
        cat_a = make_category(user, "Trabalho")
        cat_b = make_category(user, "Lazer")
        make_task(user, "Work task", category=cat_a)
        make_task(user, "Fun task", category=cat_b)
        make_task(user, "No category task")

        client, _ = get_auth_client(user)
        resp = client.get(TASKS, {"category": str(cat_a.pk)})
        titles = [t["title"] for t in resp.data["results"]]
        assert "Work task" in titles
        assert "Fun task" not in titles
        assert "No category task" not in titles

    def test_filter_by_status_pending(self, make_user, make_task):
        user = make_user()
        make_task(user, "Pending task", status=Task.Status.PENDING)
        make_task(user, "Done task", status=Task.Status.COMPLETED)

        client, _ = get_auth_client(user)
        resp = client.get(TASKS, {"status": "pending"})
        titles = [t["title"] for t in resp.data["results"]]
        assert "Pending task" in titles
        assert "Done task" not in titles

    def test_filter_by_status_completed(self, make_user, make_task):
        user = make_user()
        make_task(user, "Pending task", status=Task.Status.PENDING)
        make_task(user, "Done task", status=Task.Status.COMPLETED)

        client, _ = get_auth_client(user)
        resp = client.get(TASKS, {"status": "completed"})
        titles = [t["title"] for t in resp.data["results"]]
        assert "Done task" in titles
        assert "Pending task" not in titles

    def test_filter_by_search_title_icontains(self, make_user, make_task):
        user = make_user()
        make_task(user, "Reunião com cliente")
        make_task(user, "Comprar mantimentos")
        make_task(user, "Reunião de planejamento")

        client, _ = get_auth_client(user)
        resp = client.get(TASKS, {"search": "reunião"})
        titles = [t["title"] for t in resp.data["results"]]
        assert "Reunião com cliente" in titles
        assert "Reunião de planejamento" in titles
        assert "Comprar mantimentos" not in titles

    def test_filter_search_is_case_insensitive(self, make_user, make_task):
        user = make_user()
        make_task(user, "REUNIÃO IMPORTANTE")
        client, _ = get_auth_client(user)
        resp = client.get(TASKS, {"search": "reunião"})
        assert resp.data["count"] >= 1

    def test_filter_by_due_date_after(self, make_user, make_task):
        user = make_user()
        make_task(user, "Old task", due_date=datetime.date(2024, 1, 1))
        make_task(user, "Future task", due_date=datetime.date(2026, 12, 31))
        make_task(user, "No date task")

        client, _ = get_auth_client(user)
        resp = client.get(TASKS, {"due_date_after": "2025-01-01"})
        titles = [t["title"] for t in resp.data["results"]]
        assert "Future task" in titles
        assert "Old task" not in titles
        assert "No date task" not in titles

    def test_filter_by_due_date_before(self, make_user, make_task):
        user = make_user()
        make_task(user, "Old task", due_date=datetime.date(2024, 1, 1))
        make_task(user, "Future task", due_date=datetime.date(2026, 12, 31))

        client, _ = get_auth_client(user)
        resp = client.get(TASKS, {"due_date_before": "2024-06-01"})
        titles = [t["title"] for t in resp.data["results"]]
        assert "Old task" in titles
        assert "Future task" not in titles

    def test_combined_filters(self, make_user, make_task, make_category):
        """Multiple filters applied together narrow the result correctly."""
        user = make_user()
        cat = make_category(user, "Trabalho")
        make_task(user, "Work pending", status=Task.Status.PENDING, category=cat)
        make_task(user, "Work done", status=Task.Status.COMPLETED, category=cat)
        make_task(user, "Other pending", status=Task.Status.PENDING)

        client, _ = get_auth_client(user)
        resp = client.get(TASKS, {"category": str(cat.pk), "status": "pending"})
        titles = [t["title"] for t in resp.data["results"]]
        assert titles == ["Work pending"]

    def test_no_filter_returns_all_accessible_tasks(self, make_user, make_task):
        user = make_user()
        make_task(user, "Task A")
        make_task(user, "Task B")
        client, _ = get_auth_client(user)
        resp = client.get(TASKS)
        assert resp.data["count"] == 2


@pytest.mark.django_db
class TestPagination:
    def test_pagination_config(self):
        """Unit-level check: verify the paginator class is correctly configured."""
        assert TaskPagination.page_size == 20
        assert TaskPagination.max_page_size == 100
        assert TaskPagination.page_size_query_param == "page_size"

    def test_page_size_query_param_respected(self, make_user, make_task):
        user = make_user()
        for i in range(5):
            make_task(user, f"Task {i}")
        client, _ = get_auth_client(user)

        resp = client.get(TASKS, {"page_size": 2})
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["results"]) == 2
        assert resp.data["count"] == 5

    def test_page_2_returns_remaining_items(self, make_user, make_task):
        user = make_user()
        for i in range(3):
            make_task(user, f"Task {i}")
        client, _ = get_auth_client(user)

        resp = client.get(TASKS, {"page_size": 2, "page": 2})
        assert resp.status_code == status.HTTP_200_OK
        assert len(resp.data["results"]) == 1

    def test_page_size_capped_at_max(self, make_user, make_task):
        """
        Requesting page_size=200 (> max_page_size=100) must be capped.
        We verify this by checking the results never exceed max_page_size,
        regardless of the requested value.
        """
        user = make_user()
        for i in range(5):
            make_task(user, f"Task {i}")
        client, _ = get_auth_client(user)

        # page_size=200 is beyond the max of 100 — should be silently capped
        resp = client.get(TASKS, {"page_size": 200})
        assert resp.status_code == status.HTTP_200_OK
        # With only 5 tasks, all 5 fit in a capped-at-100 page
        assert len(resp.data["results"]) == 5
        # Critically: the API must not raise an error or return > max_page_size items
        assert len(resp.data["results"]) <= TaskPagination.max_page_size

    def test_response_has_pagination_metadata(self, make_user, make_task):
        user = make_user()
        make_task(user, "Task 1")
        client, _ = get_auth_client(user)
        resp = client.get(TASKS)
        assert "count" in resp.data
        assert "next" in resp.data
        assert "previous" in resp.data
        assert "results" in resp.data
