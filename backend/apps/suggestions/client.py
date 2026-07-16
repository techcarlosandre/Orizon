"""
HTTP client for the Suggestions API.

This module is the integration point between the Tasks domain and the
Suggestions API. The main backend calls its own /api/suggestions/category/
endpoint via httpx, fulfilling the "consume an external API" requirement.

Design decisions:
- Short timeout (2s default): suggestion is a nice-to-have, not a blocker.
- All exceptions are caught and return FALLBACK_CATEGORY silently —
  task creation must never fail because of a suggestion lookup.
- The URL is read from settings (SUGGESTIONS_API_URL) so it can be
  overridden per environment (docker vs local vs production).
- httpx is used instead of requests for its modern API and async-readiness.
"""
from __future__ import annotations

import logging

import httpx
from django.conf import settings

from apps.suggestions.service import FALLBACK_CATEGORY

logger = logging.getLogger(__name__)

_DEFAULT_TIMEOUT = 2.0  # seconds


def get_category_suggestion(title: str, timeout: float = _DEFAULT_TIMEOUT) -> str:
    """
    Call the Suggestions API and return the suggested category name.

    Args:
        title:   The task title to send to the suggestions service.
        timeout: HTTP timeout in seconds. Defaults to 2s.

    Returns:
        A category name string. Falls back to FALLBACK_CATEGORY ("Geral")
        on any error (connection, timeout, unexpected response, etc.).
    """
    url = f"{settings.SUGGESTIONS_API_URL}/category/"

    try:
        with httpx.Client(timeout=timeout) as client:
            response = client.post(url, json={"title": title})
            response.raise_for_status()
            data = response.json()
            return data.get("suggested_category", FALLBACK_CATEGORY)

    except httpx.TimeoutException:
        logger.warning("Suggestions API timed out for title=%r", title)
        return FALLBACK_CATEGORY

    except httpx.ConnectError:
        logger.warning("Could not connect to Suggestions API at %s", url)
        return FALLBACK_CATEGORY

    except httpx.HTTPStatusError as exc:
        logger.warning(
            "Suggestions API returned HTTP %s for title=%r",
            exc.response.status_code,
            title,
        )
        return FALLBACK_CATEGORY

    except Exception:  # noqa: BLE001
        logger.exception("Unexpected error calling Suggestions API for title=%r", title)
        return FALLBACK_CATEGORY
