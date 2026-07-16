"""
Suggestions views — category suggestion endpoint.

POST /api/suggestions/category/
Body:   {"title": "..."}
Response: {"suggested_category": "Trabalho"}

Authentication: AllowAny — this endpoint is consumed internally by the
backend itself via httpx and must not require a Bearer token in the request,
which would create a circular auth dependency.

The actual logic lives in service.py (pure Python, no I/O) so it can be
unit-tested in isolation without hitting this HTTP layer.
"""
from rest_framework import serializers, status
from rest_framework.permissions import AllowAny
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from .service import suggest_category


class CategorySuggestionInputSerializer(serializers.Serializer):
    title = serializers.CharField(max_length=255, allow_blank=False)


class CategorySuggestionView(APIView):
    """
    Accepts a task title and returns a suggested category name.
    Open endpoint (AllowAny) — no sensitive data is exposed.
    """

    permission_classes = [AllowAny]

    def post(self, request: Request) -> Response:
        serializer = CategorySuggestionInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        title = serializer.validated_data["title"]
        suggested = suggest_category(title)

        return Response(
            {"suggested_category": suggested},
            status=status.HTTP_200_OK,
        )
