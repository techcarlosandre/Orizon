"""
Custom pagination for task listings.

Allows clients to request a specific page_size via query param,
capped at max_page_size to prevent abuse.
"""
from rest_framework.pagination import PageNumberPagination


class TaskPagination(PageNumberPagination):
    """
    Default page size: 20.
    Client can override via ?page_size=N (max 100).
    """

    page_size = 20
    page_size_query_param = "page_size"
    max_page_size = 100
