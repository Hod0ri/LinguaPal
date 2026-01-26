"""
LRS Celery Tasks

Async tasks for xAPI statement creation and Elasticsearch indexing.
"""

import logging
from typing import Dict, Any, List

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def create_statement_task(self, statement_data: Dict[str, Any]) -> str:
    """
    Create an xAPI statement asynchronously.

    Args:
        statement_data: Dictionary containing statement data

    Returns:
        Statement ID as string
    """
    try:
        from .services import StatementBuilder

        statement = StatementBuilder.create_from_data(statement_data)
        logger.info(f"Created statement: {statement.id}")

        # Trigger ES indexing
        index_statement_task.delay(str(statement.id))

        return str(statement.id)

    except Exception as exc:
        logger.error(f"Error creating statement: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def index_statement_task(self, statement_id: str) -> bool:
    """
    Index a statement in Elasticsearch.

    Args:
        statement_id: UUID string of the statement

    Returns:
        True if successful
    """
    try:
        from .elasticsearch import index_statement_by_id

        result = index_statement_by_id(statement_id)
        if result:
            logger.info(f"Indexed statement: {statement_id}")
        else:
            logger.warning(f"Failed to index statement: {statement_id}")
        return result

    except Exception as exc:
        logger.error(f"Error indexing statement {statement_id}: {exc}")
        self.retry(exc=exc)


@shared_task(bind=True)
def bulk_index_task(self, statement_ids: List[str]) -> Dict[str, int]:
    """
    Bulk index multiple statements in Elasticsearch.

    Args:
        statement_ids: List of statement UUID strings

    Returns:
        Dict with 'success' and 'failed' counts
    """
    try:
        from .models import XAPIStatement
        from .elasticsearch import bulk_index_statements

        statements = XAPIStatement.objects.filter(id__in=statement_ids)
        result = bulk_index_statements(statements)
        logger.info(f"Bulk indexed: {result}")
        return result

    except Exception as exc:
        logger.error(f"Bulk indexing error: {exc}")
        return {'success': 0, 'failed': len(statement_ids)}


@shared_task
def create_quiz_statements_task(quiz_data: Dict[str, Any]) -> List[str]:
    """
    Create multiple statements for quiz completion.

    This is used when a quiz is completed to create:
    - COMPLETED statement
    - PASSED or FAILED statement

    Args:
        quiz_data: Dict containing 'statements' list

    Returns:
        List of created statement IDs
    """
    from .services import StatementBuilder

    statement_ids = []
    statements_data = quiz_data.get('statements', [])

    for stmt_data in statements_data:
        try:
            statement = StatementBuilder.create_from_data(stmt_data)
            statement_ids.append(str(statement.id))
            logger.info(f"Created quiz statement: {statement.id}")
        except Exception as exc:
            logger.error(f"Error creating quiz statement: {exc}")

    # Bulk index all created statements
    if statement_ids:
        bulk_index_task.delay(statement_ids)

    return statement_ids


@shared_task
def index_session_task(session_id: str) -> bool:
    """
    Index a cmi5 session in Elasticsearch.

    Args:
        session_id: UUID string of the session

    Returns:
        True if successful
    """
    try:
        from .models import CMI5Session
        from .elasticsearch import index_session

        session = CMI5Session.objects.get(id=session_id)
        result = index_session(session)
        if result:
            logger.info(f"Indexed session: {session_id}")
        return result

    except CMI5Session.DoesNotExist:
        logger.error(f"Session not found: {session_id}")
        return False
    except Exception as exc:
        logger.error(f"Error indexing session {session_id}: {exc}")
        return False
