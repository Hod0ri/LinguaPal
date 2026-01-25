"""
LinguaPal Django Project

This module imports the Celery app to ensure that it is loaded
when Django starts, so that the @shared_task decorator will use it.
"""

from .celery import app as celery_app

__all__ = ('celery_app',)
