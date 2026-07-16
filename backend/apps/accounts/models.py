"""
Custom User model.

Extending AbstractUser now (even if empty) ensures we can add fields later
without breaking existing migrations. AUTH_USER_MODEL must be set before
the first migration of any app that has FK to User.
"""
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    """Custom user — placeholder for future field extensions."""

    class Meta:
        verbose_name = "Usuário"
        verbose_name_plural = "Usuários"

    def __str__(self) -> str:
        return self.username
