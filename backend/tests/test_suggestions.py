"""
Suggestions tests — three distinct layers tested separately:

1. service.py  — pure Python scoring logic, no mock needed (no I/O)
2. client.py   — httpx integration, mocked with respx:
                 tests timeout / connect error / HTTP 500 / success
3. views.py    — HTTP endpoint contract (status code, response shape)

The service tests are the most valuable: they prove the scoring algorithm
is correct without any HTTP or database overhead.
"""
import pytest
import respx
import httpx
from rest_framework import status
from rest_framework.test import APIClient

from apps.suggestions.service import suggest_category, FALLBACK_CATEGORY
from apps.suggestions.client import get_category_suggestion

SUGGESTIONS_ENDPOINT = "/api/suggestions/category/"
MOCK_SUGGESTIONS_BASE = "http://mock-suggestions/api/suggestions"


# ── 1. Service tests (pure Python — no DB, no HTTP, no mocks) ─────────────────

class TestSuggestCategoryService:
    """
    Tests for apps/suggestions/service.py.
    No @pytest.mark.django_db needed — pure Python logic with no I/O.
    """

    def test_trabalho_keyword_match(self):
        assert suggest_category("Reunião com o cliente") == "Trabalho"

    def test_saude_keyword_match(self):
        assert suggest_category("Consulta com o médico às 14h") == "Saúde"

    def test_estudos_keyword_match(self):
        assert suggest_category("Estudar para a prova de amanhã") == "Estudos"

    def test_financas_keyword_match(self):
        assert suggest_category("Pagar boleto do cartão") == "Finanças"

    def test_casa_keyword_match(self):
        assert suggest_category("Limpar a casa no fim de semana") == "Casa"

    def test_lazer_keyword_match(self):
        assert suggest_category("Planejar viagem de férias") == "Lazer"

    def test_familia_keyword_match(self):
        assert suggest_category("Aniversário da minha filha") == "Família"

    def test_fallback_empty_string(self):
        assert suggest_category("") == FALLBACK_CATEGORY

    def test_fallback_whitespace_only(self):
        assert suggest_category("   ") == FALLBACK_CATEGORY

    def test_fallback_no_keyword_match(self):
        assert suggest_category("xyzqwerty1234nonexistent") == FALLBACK_CATEGORY

    def test_case_insensitive_matching(self):
        """Keywords must match regardless of title casing."""
        assert suggest_category("REUNIÃO DE TRABALHO") == "Trabalho"
        assert suggest_category("Médico") == "Saúde"

    def test_higher_score_wins(self):
        """
        'Trabalho' has 2 keyword matches; 'Saúde' has 1.
        The category with the highest score must win.
        """
        title = "Reunião sobre projeto com médico corporativo"
        result = suggest_category(title)
        assert result == "Trabalho"

    def test_returns_string(self):
        result = suggest_category("any title")
        assert isinstance(result, str)
        assert len(result) > 0

    def test_fallback_constant_value(self):
        """FALLBACK_CATEGORY must be the literal string 'Geral'."""
        assert FALLBACK_CATEGORY == "Geral"


# ── 2. Client tests (httpx mocked with respx) ──────────────────────────────────

class TestSuggestionClient:
    """
    Tests for apps/suggestions/client.py.
    Uses respx to intercept httpx calls without touching the network.
    Settings override ensures the URL is predictable in tests.
    No @pytest.mark.django_db needed.
    """

    @pytest.fixture(autouse=True)
    def patch_suggestions_url(self, settings):
        settings.SUGGESTIONS_API_URL = MOCK_SUGGESTIONS_BASE

    @property
    def url(self):
        return f"{MOCK_SUGGESTIONS_BASE}/category/"

    @respx.mock
    def test_success_returns_suggested_category(self):
        respx.post(self.url).mock(
            return_value=httpx.Response(200, json={"suggested_category": "Trabalho"})
        )
        result = get_category_suggestion("reunião de trabalho")
        assert result == "Trabalho"

    @respx.mock
    def test_success_missing_key_returns_fallback(self):
        """If the API returns 200 but without the expected key, fall back gracefully."""
        respx.post(self.url).mock(
            return_value=httpx.Response(200, json={"other_key": "value"})
        )
        result = get_category_suggestion("test title")
        assert result == FALLBACK_CATEGORY

    @respx.mock
    def test_timeout_returns_fallback_and_does_not_raise(self):
        """TimeoutException → FALLBACK_CATEGORY, never an uncaught exception."""
        respx.post(self.url).mock(side_effect=httpx.TimeoutException("timed out"))
        result = get_category_suggestion("any title")
        assert result == FALLBACK_CATEGORY

    @respx.mock
    def test_connect_error_returns_fallback(self):
        """ConnectError (service down) → FALLBACK_CATEGORY."""
        respx.post(self.url).mock(side_effect=httpx.ConnectError("refused"))
        result = get_category_suggestion("any title")
        assert result == FALLBACK_CATEGORY

    @respx.mock
    def test_http_500_returns_fallback(self):
        """HTTP 5xx response → FALLBACK_CATEGORY via raise_for_status."""
        respx.post(self.url).mock(
            return_value=httpx.Response(500, text="Internal Server Error")
        )
        result = get_category_suggestion("any title")
        assert result == FALLBACK_CATEGORY

    @respx.mock
    def test_http_404_returns_fallback(self):
        respx.post(self.url).mock(
            return_value=httpx.Response(404, text="Not Found")
        )
        result = get_category_suggestion("any title")
        assert result == FALLBACK_CATEGORY

    @respx.mock
    def test_unexpected_exception_returns_fallback(self):
        """Any unexpected exception type is also caught and falls back."""
        respx.post(self.url).mock(side_effect=ValueError("unexpected error"))
        result = get_category_suggestion("any title")
        assert result == FALLBACK_CATEGORY


# ── 3. Endpoint tests (HTTP contract) ─────────────────────────────────────────

@pytest.mark.django_db
class TestCategorySuggestionEndpoint:
    """
    Tests for POST /api/suggestions/category/.
    Uses the actual Django view (no mocking of the service).
    """

    def test_valid_title_returns_200_with_suggested_category(self):
        client = APIClient()
        resp = client.post(
            SUGGESTIONS_ENDPOINT,
            {"title": "Reunião com o cliente"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
        assert "suggested_category" in resp.data
        assert isinstance(resp.data["suggested_category"], str)

    def test_conhecida_categoria_is_returned_correctly(self):
        client = APIClient()
        resp = client.post(
            SUGGESTIONS_ENDPOINT,
            {"title": "Reunião de trabalho"},
            format="json",
        )
        assert resp.data["suggested_category"] == "Trabalho"

    def test_unknown_title_returns_geral(self):
        client = APIClient()
        resp = client.post(
            SUGGESTIONS_ENDPOINT,
            {"title": "xyz123 no match"},
            format="json",
        )
        assert resp.data["suggested_category"] == "Geral"

    def test_empty_title_returns_400(self):
        client = APIClient()
        resp = client.post(SUGGESTIONS_ENDPOINT, {"title": ""}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_missing_title_returns_400(self):
        client = APIClient()
        resp = client.post(SUGGESTIONS_ENDPOINT, {}, format="json")
        assert resp.status_code == status.HTTP_400_BAD_REQUEST

    def test_allows_anonymous_access(self):
        """Endpoint is AllowAny — no auth header needed."""
        client = APIClient()  # no credentials set
        resp = client.post(
            SUGGESTIONS_ENDPOINT,
            {"title": "some title"},
            format="json",
        )
        # Must not return 401/403
        assert resp.status_code not in (
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        )

    def test_authenticated_user_can_also_call_endpoint(self, make_user):
        user = make_user()
        from tests.conftest import get_auth_client
        client, _ = get_auth_client(user)
        resp = client.post(
            SUGGESTIONS_ENDPOINT,
            {"title": "Reunião"},
            format="json",
        )
        assert resp.status_code == status.HTTP_200_OK
