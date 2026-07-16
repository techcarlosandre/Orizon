"""
Selenium E2E test conftest.
Full implementation in Phase 9.
"""
import pytest


@pytest.fixture
def base_url():
    return "http://localhost:5173"
