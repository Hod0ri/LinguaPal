"""
LRS Signals

Django signals for Elasticsearch synchronization.
Statements are indexed via Celery tasks for async processing.
"""

import logging

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from .models import XAPIStatement, CMI5Session

logger = logging.getLogger(__name__)


@receiver(post_save, sender=XAPIStatement)
def index_statement_on_save(sender, instance, created, **kwargs):
    """
    Index xAPI statement in Elasticsearch when saved.

    Uses Celery task for async indexing.
    Also ensures the associated activity is indexed.
    """
    try:
        from .tasks import index_statement_task, ensure_activity_indexed_task

        # Index the statement
        index_statement_task.delay(str(instance.id))
        logger.debug(f"Queued statement for ES indexing: {instance.id}")

        # Also ensure the activity is indexed and stats updated
        ensure_activity_indexed_task.delay(str(instance.id))
        logger.debug(f"Queued activity indexing for statement: {instance.id}")

    except Exception as exc:
        # Don't fail if Celery is not available
        logger.warning(f"Could not queue statement/activity indexing: {exc}")


@receiver(post_delete, sender=XAPIStatement)
def delete_statement_from_es(sender, instance, **kwargs):
    """
    Delete statement from Elasticsearch when deleted from DB.

    Note: We use synchronous delete here since deletes are less frequent
    and we want to ensure consistency.
    """
    try:
        from .elasticsearch import delete_statement
        delete_statement(str(instance.id))
        logger.debug(f"Deleted statement from ES: {instance.id}")
    except Exception as exc:
        logger.error(f"Error deleting statement from ES: {exc}")


@receiver(post_save, sender=CMI5Session)
def index_session_on_save(sender, instance, created, **kwargs):
    """
    Index cmi5 session in Elasticsearch when saved.

    Uses Celery task for async indexing.
    """
    try:
        from .tasks import index_session_task
        index_session_task.delay(str(instance.id))
    except Exception as exc:
        # Don't fail if Celery is not available
        logger.warning(f"Could not queue session indexing: {exc}")


@receiver(post_delete, sender=CMI5Session)
def delete_session_from_es(sender, instance, **kwargs):
    """
    Delete session from Elasticsearch when deleted from DB.
    """
    try:
        from .elasticsearch import get_client, SESSION_INDEX
        client = get_client()
        if client:
            client.delete(index=SESSION_INDEX, id=str(instance.id), ignore=[404])
            logger.debug(f"Deleted session from ES: {instance.id}")
    except Exception as exc:
        logger.error(f"Error deleting session from ES: {exc}")
