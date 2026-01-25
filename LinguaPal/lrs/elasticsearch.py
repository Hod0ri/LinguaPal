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

        if user and password:
            client = Elasticsearch(
                hosts=[host],
                basic_auth=(user, password)
            )
        else:
            client = Elasticsearch(hosts=[host])

        # Test connection
        if client.ping():
            return client
        else:
            logger.warning("Elasticsearch ping failed")
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
