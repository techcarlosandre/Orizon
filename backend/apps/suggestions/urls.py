"""Suggestions URL configuration."""
from django.urls import path
from .views import CategorySuggestionView

urlpatterns = [
    path("category/", CategorySuggestionView.as_view(), name="suggest-category"),
]
