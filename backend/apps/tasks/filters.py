"""
Task FilterSet using django-filter.

All filter parameters are handled here — no ad-hoc filtering in views.

Supported query params:
  ?category=<uuid>           — filter by category ID
  ?status=pending|completed  — filter by status
  ?search=<text>             — case-insensitive substring match on title
  ?due_date_after=YYYY-MM-DD — tasks with due_date >= this date
  ?due_date_before=YYYY-MM-DD— tasks with due_date <= this date

Ordering is handled by DRF OrderingFilter (declared on the ViewSet).
"""
import django_filters

from .models import Task


class TaskFilter(django_filters.FilterSet):
    search = django_filters.CharFilter(
        field_name="title",
        lookup_expr="icontains",
        label="Busca no título",
    )
    due_date_after = django_filters.DateFilter(
        field_name="due_date",
        lookup_expr="gte",
        label="Vencimento a partir de",
    )
    due_date_before = django_filters.DateFilter(
        field_name="due_date",
        lookup_expr="lte",
        label="Vencimento até",
    )

    class Meta:
        model = Task
        fields = {
            "category": ["exact"],
            "status": ["exact"],
        }
