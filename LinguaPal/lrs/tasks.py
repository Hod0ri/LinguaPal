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


@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def index_activity_task(self, activity_data: Dict[str, Any]) -> bool:
    """
    Index or update an activity in Elasticsearch.

    Args:
        activity_data: Dict containing activity information

    Returns:
        True if successful
    """
    try:
        from .elasticsearch import get_or_create_activity

        activity_id = activity_data.get('id')
        if not activity_id:
            logger.error("Activity ID is required")
            return False

        get_or_create_activity(activity_id, activity_data)
        logger.info(f"Indexed activity: {activity_id}")
        return True

    except Exception as exc:
        logger.error(f"Error indexing activity: {exc}")
        self.retry(exc=exc)


@shared_task
def update_activity_stats_task(activity_id: str, verb: str, user_id: int, score: float = None) -> bool:
    """
    Update activity statistics when a statement is created.

    Args:
        activity_id: The activity IRI
        verb: The verb ID
        user_id: The user who performed the action
        score: Optional score for completed/passed/failed

    Returns:
        True if successful
    """
    try:
        from .elasticsearch import update_activity_stats

        result = update_activity_stats(activity_id, verb, user_id, score)
        if result:
            logger.debug(f"Updated activity stats: {activity_id}")
        return result

    except Exception as exc:
        logger.error(f"Error updating activity stats {activity_id}: {exc}")
        return False


@shared_task
def ensure_activity_indexed_task(statement_id: str) -> bool:
    """
    Ensure the activity referenced by a statement is indexed in ES.

    This task extracts activity info from a statement and ensures
    the activity exists in the activities index.

    Args:
        statement_id: UUID string of the statement

    Returns:
        True if successful
    """
    try:
        from .models import XAPIStatement
        from .constants import ActivityID, get_activity_name, XAPIActivityType
        from .elasticsearch import get_or_create_activity, update_activity_stats

        statement = XAPIStatement.objects.get(id=statement_id)
        activity_meta = ActivityID.parse(statement.object_id)

        # Only index quiz activities (not individual questions)
        if activity_meta.get('question_id') is not None:
            return True  # Skip questions

        # Build activity data
        category = activity_meta.get('category')
        subcategory = activity_meta.get('subcategory')
        quiz_type = activity_meta.get('quiz_type')

        if not all([category, subcategory, quiz_type]):
            return True  # Not a valid activity pattern

        # Get base activity ID (without session)
        if category == 'gana':
            base_activity_id = ActivityID.gana_quiz(subcategory, quiz_type)
            activity_name = get_activity_name('gana', subcategory, quiz_type)
        elif category == 'word':
            base_activity_id = ActivityID.word_quiz(subcategory, quiz_type)
            # Try to get language name from context
            language_name = statement.context_extensions.get('language_name', subcategory)
            activity_name = get_activity_name('word', subcategory, quiz_type, language_name)
        else:
            return True

        activity_data = {
            'id': base_activity_id,
            'category': category,
            'subcategory': subcategory,
            'quiz_type': quiz_type,
            'language_code': subcategory if category == 'word' else None,
            'character_set': subcategory if category == 'gana' else None,
            'name': activity_name,
            'type': XAPIActivityType.ASSESSMENT,
        }

        # Ensure activity exists
        get_or_create_activity(base_activity_id, activity_data)

        # Update stats based on verb
        score = statement.result_score_scaled
        update_activity_stats(base_activity_id, statement.verb_id, statement.actor_user_id, score)

        logger.info(f"Ensured activity indexed: {base_activity_id}")
        return True

    except XAPIStatement.DoesNotExist:
        logger.error(f"Statement not found: {statement_id}")
        return False
    except Exception as exc:
        logger.error(f"Error ensuring activity indexed for {statement_id}: {exc}")
        return False
