"""Development settings."""
from .base import *  # noqa: F401, F403

DEBUG = True

# Allows all hosts in dev for convenience
ALLOWED_HOSTS = ["*"]

# Django Debug Toolbar (optional, not installed by default)
INTERNAL_IPS = ["127.0.0.1"]
