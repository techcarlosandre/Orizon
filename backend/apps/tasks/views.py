"""
Tasks views — CRUD endpoints.
Full implementation in Phase 3.
"""
from rest_framework.viewsets import ViewSet
from rest_framework.response import Response
from rest_framework import status


class TaskViewSet(ViewSet):
    def list(self, request):
        return Response({"detail": "Not implemented yet."}, status=status.HTTP_501_NOT_IMPLEMENTED)


class CategoryViewSet(ViewSet):
    def list(self, request):
        return Response({"detail": "Not implemented yet."}, status=status.HTTP_501_NOT_IMPLEMENTED)
