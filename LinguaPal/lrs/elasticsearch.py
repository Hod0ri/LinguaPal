"""
Elasticsearch Client and Indexing Functions

Provides Elasticsearch integration for xAPI statements and cmi5 sessions.
"""

import logging
from typing import Optional, List, Dict, Any

from django.conf import settings

try:
    from elasticsearch import Elasticsearch
    from elasticsearch.exceptions import ConnectionError, NotFoundError
    ES_AVAILABLE = True
except ImportError:
    ES_AVAILABLE = False
    Elasticsearch = None

logger = logging.getLogger(__name__)

# Index names
STATEMENT_INDEX = 'xapi_statements'
SESSION_INDEX = 'cmi5_sessions'
ACTIVITY_INDEX = 'xapi_activities'

# Index mappings
STATEMENT_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "actor": {
                "properties": {
                    "user_id": {"type": "integer"},
                    "mbox": {"type": "keyword"},
                    "name": {
                        "type": "text",
                        "fields": {"keyword": {"type": "keyword"}}
                    }
                }
            },
            "verb": {
                "properties": {
                    "id": {"type": "keyword"},
                    "display": {"type": "keyword"}
                }
            },
            "object": {
                "properties": {
                    "type": {"type": "keyword"},
                    "id": {"type": "keyword"},
                    "definition": {"type": "object", "enabled": False}
                }
            },
            "activity": {
                "properties": {
                    "category": {"type": "keyword"},
                    "subcategory": {"type": "keyword"},
                    "quiz_type": {"type": "keyword"},
                    "language_code": {"type": "keyword"},
                    "character_set": {"type": "keyword"}
                }
            },
            "result": {
                "properties": {
                    "success": {"type": "boolean"},
                    "response": {"type": "text"},
                    "score_scaled": {"type": "float"},
                    "score_raw": {"type": "float"},
                    "completion": {"type": "boolean"},
                    "duration_seconds": {"type": "long"}
                }
            },
            "context": {
                "properties": {
                    "registration": {"type": "keyword"},
                    "quiz_type": {"type": "keyword"},
                    "character_set": {"type": "keyword"},
                    "question_number": {"type": "integer"},
                    "extensions": {"type": "object", "enabled": False}
                }
            },
            "timestamp": {"type": "date"},
            "stored": {"type": "date"}
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0,
        "refresh_interval": "1s"
    }
}

SESSION_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "registration": {"type": "keyword"},
            "actor_user_id": {"type": "integer"},
            "au_id": {"type": "keyword"},
            "au_type": {"type": "keyword"},
            "au_object_id": {"type": "integer"},
            "state": {"type": "keyword"},
            "mastery_score": {"type": "float"},
            "launch_mode": {"type": "keyword"},
            "move_on": {"type": "keyword"},
            "is_passed": {"type": "boolean"},
            "is_completed": {"type": "boolean"},
            "score_scaled": {"type": "float"},
            "launched_at": {"type": "date"},
            "initialized_at": {"type": "date"},
            "terminated_at": {"type": "date"}
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    }
}

ACTIVITY_MAPPING = {
    "mappings": {
        "properties": {
            "id": {"type": "keyword"},
            "category": {"type": "keyword"},
            "subcategory": {"type": "keyword"},
            "quiz_type": {"type": "keyword"},
            "language_code": {"type": "keyword"},
            "language_name": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}}
            },
            "character_set": {"type": "keyword"},
            "name": {
                "type": "text",
                "fields": {"keyword": {"type": "keyword"}}
            },
            "description": {"type": "text"},
            "type": {"type": "keyword"},
            "stats": {
                "properties": {
                    "total_attempts": {"type": "long"},
                    "total_completions": {"type": "long"},
                    "total_passes": {"type": "long"},
                    "total_fails": {"type": "long"},
                    "avg_score": {"type": "float"},
                    "unique_users": {"type": "long"}
                }
            },
            "created_at": {"type": "date"},
            "updated_at": {"type": "date"}
        }
    },
    "settings": {
        "number_of_shards": 1,
        "number_of_replicas": 0
    }
}


def get_es_client() -> Optional[Elasticsearch]:
    """
    Get Elasticsearch client instance.

    Returns None if Elasticsearch is not available or configured.
    """
    if not ES_AVAILABLE:
        logger.warning("Elasticsearch package not installed")
        return None

    host = getattr(settings, 'ELASTICSEARCH_HOST', None)
    if not host:
        logger.warning("ELASTICSEARCH_HOST not configured")
        return None

    try:
        user = getattr(settings, 'ELASTICSEARCH_USER', '')
        password = getattr(settings, 'ELASTICSEARCH_PASSWORD', '')

        # Client options
        client_options = {
            'hosts': [host],
            'request_timeout': 30,
            'verify_certs': False,
        }

        if user and password:
            client_options['basic_auth'] = (user, password)

        client = Elasticsearch(**client_options)

        # Test connection using info() instead of ping() for ES 8.x compatibility
        try:
            info = client.info()
            logger.debug(f"Connected to Elasticsearch: {info.get('version', {}).get('number', 'unknown')}")
            return client
        except Exception as e:
            logger.warning(f"Elasticsearch connection test failed: {e}")
            return None

    except ConnectionError as e:
        logger.error(f"Elasticsearch connection error: {e}")
        return None
    except Exception as e:
        logger.error(f"Elasticsearch client error: {e}")
        return None


# Lazy initialization
_es_client = None


def get_client() -> Optional[Elasticsearch]:
    """Get or create Elasticsearch client (lazy singleton)."""
    global _es_client
    if _es_client is None:
        _es_client = get_es_client()
    return _es_client


# Module-level client accessor (lazy)
class _ESClientAccessor:
    """Lazy accessor for Elasticsearch client."""
    _client = None

    def __getattr__(self, name):
        if self._client is None:
            self._client = get_client()
        if self._client is None:
            raise RuntimeError("Elasticsearch client not available")
        return getattr(self._client, name)

    def __bool__(self):
        if self._client is None:
            self._client = get_client()
        return self._client is not None


es_client = _ESClientAccessor()


def index_statement_to_dict(statement) -> Dict:
    """
    Convert XAPIStatement to Elasticsearch document dict.

    Alias for _statement_to_doc for external use.
    """
    return _statement_to_doc(statement)


def create_indices():
    """Create Elasticsearch indices if they don't exist."""
    client = get_client()
    if not client:
        logger.warning("Cannot create indices: Elasticsearch not available")
        return False

    try:
        # Create statement index
        if not client.indices.exists(index=STATEMENT_INDEX):
            client.indices.create(index=STATEMENT_INDEX, body=STATEMENT_MAPPING)
            logger.info(f"Created index: {STATEMENT_INDEX}")

        # Create session index
        if not client.indices.exists(index=SESSION_INDEX):
            client.indices.create(index=SESSION_INDEX, body=SESSION_MAPPING)
            logger.info(f"Created index: {SESSION_INDEX}")

        # Create activity index
        if not client.indices.exists(index=ACTIVITY_INDEX):
            client.indices.create(index=ACTIVITY_INDEX, body=ACTIVITY_MAPPING)
            logger.info(f"Created index: {ACTIVITY_INDEX}")

        return True

    except Exception as e:
        logger.error(f"Error creating indices: {e}")
        return False


def delete_indices():
    """Delete Elasticsearch indices (use with caution)."""
    client = get_client()
    if not client:
        return False

    try:
        if client.indices.exists(index=STATEMENT_INDEX):
            client.indices.delete(index=STATEMENT_INDEX)
            logger.info(f"Deleted index: {STATEMENT_INDEX}")

        if client.indices.exists(index=SESSION_INDEX):
            client.indices.delete(index=SESSION_INDEX)
            logger.info(f"Deleted index: {SESSION_INDEX}")

        if client.indices.exists(index=ACTIVITY_INDEX):
            client.indices.delete(index=ACTIVITY_INDEX)
            logger.info(f"Deleted index: {ACTIVITY_INDEX}")

        return True

    except Exception as e:
        logger.error(f"Error deleting indices: {e}")
        return False


def index_statement(statement) -> bool:
    """
    Index a single xAPI statement.

    Args:
        statement: XAPIStatement model instance

    Returns:
        True if successful, False otherwise
    """
    client = get_client()
    if not client:
        return False

    try:
        doc = _statement_to_doc(statement)
        client.index(
            index=STATEMENT_INDEX,
            id=str(statement.id),
            document=doc
        )
        return True

    except Exception as e:
        logger.error(f"Error indexing statement {statement.id}: {e}")
        return False


def index_statement_by_id(statement_id: str) -> bool:
    """
    Index a statement by its ID.

    Args:
        statement_id: UUID string of the statement

    Returns:
        True if successful, False otherwise
    """
    from .models import XAPIStatement

    try:
        statement = XAPIStatement.objects.get(id=statement_id)
        return index_statement(statement)
    except XAPIStatement.DoesNotExist:
        logger.error(f"Statement not found: {statement_id}")
        return False


def delete_statement(statement_id: str) -> bool:
    """
    Delete a statement from Elasticsearch.

    Args:
        statement_id: UUID string of the statement

    Returns:
        True if successful, False otherwise
    """
    client = get_client()
    if not client:
        return False

    try:
        client.delete(index=STATEMENT_INDEX, id=str(statement_id))
        return True
    except NotFoundError:
        return True  # Already deleted
    except Exception as e:
        logger.error(f"Error deleting statement {statement_id}: {e}")
        return False


def bulk_index_statements(statements) -> Dict[str, int]:
    """
    Bulk index multiple statements.

    Args:
        statements: Iterable of XAPIStatement instances

    Returns:
        Dict with 'success' and 'failed' counts
    """
    client = get_client()
    if not client:
        return {'success': 0, 'failed': len(list(statements))}

    from elasticsearch.helpers import bulk

    actions = []
    for stmt in statements:
        doc = _statement_to_doc(stmt)
        actions.append({
            '_index': STATEMENT_INDEX,
            '_id': str(stmt.id),
            '_source': doc
        })

    try:
        success, failed = bulk(client, actions, raise_on_error=False)
        return {'success': success, 'failed': len(failed) if failed else 0}
    except Exception as e:
        logger.error(f"Bulk indexing error: {e}")
        return {'success': 0, 'failed': len(actions)}


def index_session(session) -> bool:
    """
    Index a cmi5 session.

    Args:
        session: CMI5Session model instance

    Returns:
        True if successful, False otherwise
    """
    client = get_client()
    if not client:
        return False

    try:
        doc = _session_to_doc(session)
        client.index(
            index=SESSION_INDEX,
            id=str(session.id),
            document=doc
        )
        return True

    except Exception as e:
        logger.error(f"Error indexing session {session.id}: {e}")
        return False


def index_activity(activity_data: Dict[str, Any]) -> bool:
    """
    Index or update an activity in Elasticsearch.

    Args:
        activity_data: Dict containing activity information

    Returns:
        True if successful, False otherwise
    """
    client = get_client()
    if not client:
        return False

    try:
        activity_id = activity_data.get('id')
        if not activity_id:
            logger.error("Activity ID is required")
            return False

        # Use upsert to create or update
        client.index(
            index=ACTIVITY_INDEX,
            id=activity_id,
            document=activity_data
        )
        return True

    except Exception as e:
        logger.error(f"Error indexing activity {activity_data.get('id')}: {e}")
        return False


def get_or_create_activity(activity_id: str, activity_data: Dict[str, Any]) -> Dict:
    """
    Get an activity from ES or create it if it doesn't exist.

    Args:
        activity_id: The activity IRI
        activity_data: Data to use if creating new activity

    Returns:
        Activity document from ES
    """
    client = get_client()
    if not client:
        return activity_data

    try:
        result = client.get(index=ACTIVITY_INDEX, id=activity_id)
        return result['_source']
    except NotFoundError:
        # Create new activity
        from django.utils import timezone
        activity_data['id'] = activity_id
        activity_data['created_at'] = timezone.now().isoformat()
        activity_data['updated_at'] = timezone.now().isoformat()
        activity_data['stats'] = {
            'total_attempts': 0,
            'total_completions': 0,
            'total_passes': 0,
            'total_fails': 0,
            'avg_score': 0.0,
            'unique_users': 0
        }
        index_activity(activity_data)
        return activity_data
    except Exception as e:
        logger.error(f"Error getting activity {activity_id}: {e}")
        return activity_data


def update_activity_stats(activity_id: str, verb: str, user_id: int, score: float = None) -> bool:
    """
    Update activity statistics when a statement is created.

    Args:
        activity_id: The activity IRI
        verb: The verb ID (initialized, completed, passed, failed)
        user_id: The user who performed the action
        score: Optional score for completed/passed/failed

    Returns:
        True if successful, False otherwise
    """
    client = get_client()
    if not client:
        return False

    try:
        # Use painless script to update stats atomically
        script_parts = []
        params = {}

        if 'initialized' in verb:
            script_parts.append("ctx._source.stats.total_attempts += 1")

        if 'completed' in verb:
            script_parts.append("ctx._source.stats.total_completions += 1")
            if score is not None:
                script_parts.append("""
                    double oldAvg = ctx._source.stats.avg_score;
                    long count = ctx._source.stats.total_completions;
                    ctx._source.stats.avg_score = ((oldAvg * (count - 1)) + params.score) / count
                """)
                params['score'] = score

        if 'passed' in verb:
            script_parts.append("ctx._source.stats.total_passes += 1")

        if 'failed' in verb:
            script_parts.append("ctx._source.stats.total_fails += 1")

        if not script_parts:
            return True

        # Update timestamp
        script_parts.append("ctx._source.updated_at = params.now")
        params['now'] = __import__('django.utils.timezone', fromlist=['timezone']).timezone.now().isoformat()

        script = "; ".join(script_parts)

        client.update(
            index=ACTIVITY_INDEX,
            id=activity_id,
            body={
                'script': {
                    'source': script,
                    'params': params
                }
            }
        )
        return True

    except NotFoundError:
        logger.warning(f"Activity not found for stats update: {activity_id}")
        return False
    except Exception as e:
        logger.error(f"Error updating activity stats {activity_id}: {e}")
        return False


def search_activities(query_params: Dict[str, Any]) -> Dict:
    """
    Search activities with filters.

    Args:
        query_params: Dict with keys like 'category', 'subcategory', 'quiz_type', 'language_code'

    Returns:
        Elasticsearch search results
    """
    client = get_client()
    if not client:
        return {'hits': {'total': {'value': 0}, 'hits': []}}

    must = []

    if 'category' in query_params:
        must.append({'term': {'category': query_params['category']}})

    if 'subcategory' in query_params:
        must.append({'term': {'subcategory': query_params['subcategory']}})

    if 'quiz_type' in query_params:
        must.append({'term': {'quiz_type': query_params['quiz_type']}})

    if 'language_code' in query_params:
        must.append({'term': {'language_code': query_params['language_code']}})

    if 'character_set' in query_params:
        must.append({'term': {'character_set': query_params['character_set']}})

    # Build query
    if must:
        query = {'bool': {'must': must}}
    else:
        query = {'match_all': {}}

    body = {
        'query': query,
        'sort': [{'stats.total_attempts': 'desc'}],
        'size': query_params.get('limit', 100)
    }

    try:
        return client.search(index=ACTIVITY_INDEX, body=body)
    except Exception as e:
        logger.error(f"Activity search error: {e}")
        return {'hits': {'total': {'value': 0}, 'hits': []}}


def search_statements(query_params: Dict[str, Any]) -> Dict:
    """
    Search statements with xAPI-style parameters.

    Args:
        query_params: Dict with keys like 'verb', 'agent', 'activity', 'since', 'until', 'limit'

    Returns:
        Elasticsearch search results
    """
    client = get_client()
    if not client:
        return {'hits': {'total': {'value': 0}, 'hits': []}}

    must = []

    if 'verb' in query_params:
        must.append({'term': {'verb.id': query_params['verb']}})

    if 'agent' in query_params:
        # Agent can be user_id or mbox
        agent = query_params['agent']
        if isinstance(agent, int):
            must.append({'term': {'actor.user_id': agent}})
        else:
            must.append({'term': {'actor.mbox': agent}})

    if 'activity' in query_params:
        must.append({'term': {'object.id': query_params['activity']}})

    # Date range
    date_range = {}
    if 'since' in query_params:
        date_range['gte'] = query_params['since']
    if 'until' in query_params:
        date_range['lte'] = query_params['until']
    if date_range:
        must.append({'range': {'timestamp': date_range}})

    # Build query
    if must:
        query = {'bool': {'must': must}}
    else:
        query = {'match_all': {}}

    body = {
        'query': query,
        'sort': [{'timestamp': 'desc'}],
        'size': query_params.get('limit', 100)
    }

    try:
        return client.search(index=STATEMENT_INDEX, body=body)
    except Exception as e:
        logger.error(f"Search error: {e}")
        return {'hits': {'total': {'value': 0}, 'hits': []}}


def aggregate_stats(aggregations: Dict[str, Any], filters: Dict = None) -> Dict:
    """
    Run aggregation queries for dashboard statistics.

    Args:
        aggregations: Elasticsearch aggregation definition
        filters: Optional filters to apply

    Returns:
        Aggregation results
    """
    client = get_client()
    if not client:
        return {}

    body = {
        'size': 0,
        'aggs': aggregations
    }

    if filters:
        body['query'] = {'bool': {'filter': filters}}

    try:
        result = client.search(index=STATEMENT_INDEX, body=body)
        return result.get('aggregations', {})
    except Exception as e:
        logger.error(f"Aggregation error: {e}")
        return {}


def _statement_to_doc(statement) -> Dict:
    """Convert XAPIStatement to Elasticsearch document."""
    from .constants import ActivityID

    # Parse activity ID to extract metadata
    activity_meta = ActivityID.parse(statement.object_id)

    # If ActivityID.parse doesn't provide category, try context_extensions
    # This handles flashcard and other non-standard activity types
    ctx_ext = statement.context_extensions or {}
    category = activity_meta.get('category') or ctx_ext.get('category')

    # For flashcard, context_extensions has the correct display values
    # ActivityID.parse returns "session" and session_id which are not useful for display
    if category == 'flashcard':
        subcategory = ctx_ext.get('subcategory') or activity_meta.get('subcategory')
        quiz_type = ctx_ext.get('quiz_type') or activity_meta.get('quiz_type')
    else:
        subcategory = activity_meta.get('subcategory') or ctx_ext.get('subcategory')
        quiz_type = activity_meta.get('quiz_type') or ctx_ext.get('quiz_type')
    language_code = ctx_ext.get('language_code') or (
        activity_meta.get('subcategory') if activity_meta.get('category') == 'word' else None
    )
    language_name = ctx_ext.get('language_name')
    character_set = activity_meta.get('subcategory') if activity_meta.get('category') == 'gana' else None

    doc = {
        'id': str(statement.id),
        'actor': {
            'user_id': statement.actor_user_id,
            'mbox': statement.actor_mbox,
            'name': statement.actor_name,
        },
        'verb': {
            'id': statement.verb_id,
            'display': statement.verb_display,
        },
        'object': {
            'type': statement.object_type,
            'id': statement.object_id,
            'definition': statement.object_definition,
        },
        'activity': {
            'category': category,
            'subcategory': subcategory,
            'quiz_type': quiz_type,
            'language_code': language_code,
            'language_name': language_name,
            'character_set': character_set,
        },
        'result': {
            'success': statement.result_success,
            'response': statement.result_response,
            'score_scaled': statement.result_score_scaled,
            'score_raw': statement.result_score_raw,
            'completion': statement.result_completion,
            'duration_seconds': (
                statement.result_duration.total_seconds()
                if statement.result_duration else None
            ),
        },
        'context': {
            'registration': str(statement.context_registration) if statement.context_registration else None,
            **statement.context_extensions,
        },
        'timestamp': statement.timestamp.isoformat(),
        'stored': statement.stored.isoformat() if statement.stored else None,
    }
    return doc


def _session_to_doc(session) -> Dict:
    """Convert CMI5Session to Elasticsearch document."""
    return {
        'id': str(session.id),
        'registration': str(session.registration),
        'actor_user_id': session.actor_user_id,
        'au_id': session.au_id,
        'au_type': session.au_type,
        'au_object_id': session.au_object_id,
        'state': session.state,
        'mastery_score': session.mastery_score,
        'launch_mode': session.launch_mode,
        'move_on': session.move_on,
        'is_passed': session.is_passed,
        'is_completed': session.is_completed,
        'score_scaled': session.score_scaled,
        'launched_at': session.launched_at.isoformat() if session.launched_at else None,
        'initialized_at': session.initialized_at.isoformat() if session.initialized_at else None,
        'terminated_at': session.terminated_at.isoformat() if session.terminated_at else None,
    }
