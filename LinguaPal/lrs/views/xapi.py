"""
xAPI LRS Views

Standard xAPI LRS endpoints following the xAPI 1.0.3 specification.

Endpoints:
- GET/POST/PUT /xapi/statements - Statement Resource
- GET /xapi/about - About Resource
"""

import logging
import uuid

from django.conf import settings
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from ..models import XAPIStatement
from ..serializers import (
    XAPIStatementSerializer,
    XAPIStatementInputSerializer,
    StatementQuerySerializer,
    LRSAboutSerializer,
)
from ..authentication import (
    LRSBasicAuthentication,
    HasLRSReadPermission,
    HasLRSWritePermission,
)
from ..services import StatementBuilder
from ..tasks import index_statement_task

logger = logging.getLogger(__name__)

# xAPI version supported
XAPI_VERSION = '1.0.3'


class StatementView(APIView):
    """
    xAPI Statement Resource.

    Supports:
    - GET: Retrieve statement(s)
    - POST: Store statement(s)
    - PUT: Store a single statement with specified ID
    """

    authentication_classes = [LRSBasicAuthentication]

    def get_permissions(self):
        """Return appropriate permissions based on HTTP method."""
        if self.request.method == 'GET':
            return [HasLRSReadPermission()]
        return [HasLRSWritePermission()]

    def get(self, request):
        """
        Retrieve xAPI statement(s).

        Query parameters (xAPI standard):
        - statementId: Fetch specific statement
        - agent: Filter by actor
        - verb: Filter by verb IRI
        - activity: Filter by object ID
        - registration: Filter by registration UUID
        - since: Return statements stored after this timestamp
        - until: Return statements stored before this timestamp
        - limit: Maximum number of statements (default 100)
        - ascending: Sort order (default False = descending)
        """
        # Validate X-Experience-API-Version header
        api_version = request.META.get('HTTP_X_EXPERIENCE_API_VERSION')
        if api_version and not api_version.startswith('1.'):
            return Response(
                {'error': f'Unsupported xAPI version: {api_version}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Parse query parameters
        query_serializer = StatementQuerySerializer(data=request.query_params)
        if not query_serializer.is_valid():
            return Response(
                query_serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )
        params = query_serializer.validated_data

        # Single statement lookup
        statement_id = params.get('statementId')
        if statement_id:
            try:
                statement = XAPIStatement.objects.get(id=statement_id)
                serializer = XAPIStatementSerializer(statement)
                return Response(serializer.data)
            except XAPIStatement.DoesNotExist:
                return Response(
                    {'error': 'Statement not found'},
                    status=status.HTTP_404_NOT_FOUND
                )

        # Build queryset with filters
        queryset = XAPIStatement.objects.all()

        # Filter by agent (actor mbox)
        agent = params.get('agent')
        if agent:
            # Agent can be JSON or mbox string
            if agent.startswith('mailto:'):
                queryset = queryset.filter(actor_mbox=agent.replace('mailto:', ''))
            else:
                queryset = queryset.filter(actor_mbox__icontains=agent)

        # Filter by verb
        verb = params.get('verb')
        if verb:
            queryset = queryset.filter(verb_id=verb)

        # Filter by activity (object)
        activity = params.get('activity')
        if activity:
            queryset = queryset.filter(object_id=activity)

        # Filter by registration
        registration = params.get('registration')
        if registration:
            queryset = queryset.filter(context_registration=registration)

        # Filter by time range
        since = params.get('since')
        if since:
            queryset = queryset.filter(stored__gt=since)

        until = params.get('until')
        if until:
            queryset = queryset.filter(stored__lte=until)

        # Sorting
        ascending = params.get('ascending', False)
        if ascending:
            queryset = queryset.order_by('stored')
        else:
            queryset = queryset.order_by('-stored')

        # Limit results
        limit = params.get('limit', 100)
        queryset = queryset[:limit]

        # Serialize and return
        serializer = XAPIStatementSerializer(queryset, many=True)

        response_data = {
            'statements': serializer.data,
        }

        response = Response(response_data)
        response['X-Experience-API-Version'] = XAPI_VERSION
        return response

    def post(self, request):
        """
        Store xAPI statement(s).

        Accepts single statement or array of statements.
        Returns array of statement IDs.
        """
        # Validate X-Experience-API-Version header
        api_version = request.META.get('HTTP_X_EXPERIENCE_API_VERSION')
        if not api_version:
            return Response(
                {'error': 'X-Experience-API-Version header required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        data = request.data
        is_array = isinstance(data, list)
        statements_data = data if is_array else [data]

        statement_ids = []

        for stmt_data in statements_data:
            # Validate input
            serializer = XAPIStatementInputSerializer(data=stmt_data)
            if not serializer.is_valid():
                return Response(
                    serializer.errors,
                    status=status.HTTP_400_BAD_REQUEST
                )

            validated_data = serializer.validated_data

            try:
                # Create statement
                statement = self._create_statement(validated_data, request.auth)
                statement_ids.append(str(statement.id))

                # Queue ES indexing
                try:
                    index_statement_task.delay(str(statement.id))
                except Exception as exc:
                    logger.warning(f"Could not queue ES indexing: {exc}")

            except Exception as exc:
                logger.error(f"Error creating statement: {exc}")
                return Response(
                    {'error': str(exc)},
                    status=status.HTTP_400_BAD_REQUEST
                )

        response = Response(statement_ids, status=status.HTTP_200_OK)
        response['X-Experience-API-Version'] = XAPI_VERSION
        return response

    def put(self, request):
        """
        Store a single xAPI statement with specified ID.

        Query parameter:
        - statementId: Required UUID for the statement
        """
        statement_id = request.query_params.get('statementId')
        if not statement_id:
            return Response(
                {'error': 'statementId query parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            statement_uuid = uuid.UUID(statement_id)
        except ValueError:
            return Response(
                {'error': 'Invalid statementId format'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Check if statement already exists
        if XAPIStatement.objects.filter(id=statement_uuid).exists():
            return Response(
                {'error': 'Statement with this ID already exists'},
                status=status.HTTP_409_CONFLICT
            )

        # Validate input
        serializer = XAPIStatementInputSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        validated_data = serializer.validated_data
        validated_data['id'] = statement_uuid

        try:
            statement = self._create_statement(validated_data, request.auth)

            # Queue ES indexing
            try:
                index_statement_task.delay(str(statement.id))
            except Exception as exc:
                logger.warning(f"Could not queue ES indexing: {exc}")

            response = Response(status=status.HTTP_204_NO_CONTENT)
            response['X-Experience-API-Version'] = XAPI_VERSION
            return response

        except Exception as exc:
            logger.error(f"Error creating statement: {exc}")
            return Response(
                {'error': str(exc)},
                status=status.HTTP_400_BAD_REQUEST
            )

    def _create_statement(self, validated_data, credential):
        """
        Create an XAPIStatement from validated data.

        Args:
            validated_data: Validated statement data dict
            credential: LRSCredential used for authentication

        Returns:
            Created XAPIStatement instance
        """
        actor = validated_data['actor']
        verb = validated_data['verb']
        obj = validated_data['object']
        result = validated_data.get('result', {})
        context = validated_data.get('context', {})

        # Extract actor info
        actor_mbox = actor.get('mbox', '').replace('mailto:', '')
        if not actor_mbox and 'account' in actor:
            actor_mbox = actor['account'].get('name', 'unknown')
        actor_name = actor.get('name', actor_mbox)

        # Try to find user by email
        actor_user = None
        if actor_mbox:
            from accounts.models import User
            actor_user = User.objects.filter(email=actor_mbox).first()

        if not actor_user and credential and credential.created_by:
            # Use credential creator as fallback
            actor_user = credential.created_by

        if not actor_user:
            # Raise error - we need a user reference
            raise ValueError("Cannot determine actor user")

        # Create statement
        statement = XAPIStatement(
            actor_user=actor_user,
            actor_mbox=actor_mbox,
            actor_name=actor_name,
            verb_id=verb['id'],
            verb_display=verb.get('display', {}).get('en-US', verb['id'].split('/')[-1]),
            object_type=obj.get('objectType', 'Activity'),
            object_id=obj['id'],
            object_definition=obj.get('definition', {}),
        )

        # Set statement ID if provided
        if 'id' in validated_data:
            statement.id = validated_data['id']

        # Set result fields
        if result:
            statement.result_success = result.get('success')
            statement.result_response = result.get('response', '')
            statement.result_completion = result.get('completion')

            score = result.get('score', {})
            if score:
                statement.result_score_scaled = score.get('scaled')
                statement.result_score_raw = score.get('raw')
                statement.result_score_min = score.get('min')
                statement.result_score_max = score.get('max')

        # Set context fields
        if context:
            registration = context.get('registration')
            if registration:
                statement.context_registration = uuid.UUID(registration) if isinstance(registration, str) else registration
            statement.context_extensions = context.get('extensions', {})

        # Set timestamp if provided
        timestamp = validated_data.get('timestamp')
        if timestamp:
            statement.timestamp = timestamp

        statement.save()
        return statement


class AboutView(APIView):
    """
    xAPI About Resource.

    Returns information about the LRS including supported xAPI versions.
    """

    permission_classes = [AllowAny]

    def get(self, request):
        """Return LRS information."""
        data = {
            'version': [XAPI_VERSION, '1.0.2', '1.0.1', '1.0.0'],
            'extensions': {
                'name': 'LinguaPal LRS',
                'description': 'Learning Record Store for LinguaPal language learning platform',
                'conformanceLevel': 'lrs',
            }
        }

        serializer = LRSAboutSerializer(data)
        response = Response(serializer.data)
        response['X-Experience-API-Version'] = XAPI_VERSION
        return response
