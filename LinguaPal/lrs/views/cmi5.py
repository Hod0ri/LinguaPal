"""
cmi5 Views

Endpoints for cmi5 Assignable Unit (AU) launch and session management.

cmi5 is a profile for xAPI that provides a standardized way to launch
content from an LMS and track learning experiences.

Endpoints:
- GET /cmi5/launch - Generate launch URL with parameters
- POST /cmi5/session/start - Start a new cmi5 session
- POST /cmi5/session/{id}/initialize - Initialize session (AU ready)
- POST /cmi5/session/{id}/terminate - Terminate session with results
- POST /cmi5/session/{id}/abandon - Abandon session
"""

import logging
import uuid
from urllib.parse import urlencode

from django.conf import settings
from django.utils import timezone
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import CMI5Session, XAPIStatement
from ..serializers import CMI5SessionSerializer
from ..services import CMI5SessionService, StatementBuilder
from ..constants import CMI5Verb, XAPIActivityType, LINGUAPAL_BASE_IRI
from ..tasks import index_statement_task, index_session_task

logger = logging.getLogger(__name__)


class CMI5LaunchView(APIView):
    """
    cmi5 Launch URL generator.

    Generates a launch URL with all required cmi5 parameters for
    starting an Assignable Unit.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """
        Generate cmi5 launch URL.

        Query parameters:
        - au_type: Type of AU (gana_quiz, word_quiz)
        - au_object_id: Quiz ID (optional)
        - return_url: URL to return after completion (optional)

        Returns:
        - launch_url: URL with cmi5 parameters
        - registration: Session registration UUID
        - session_id: CMI5Session ID
        """
        au_type = request.query_params.get('au_type')
        if not au_type:
            return Response(
                {'error': 'au_type parameter required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        au_object_id = request.query_params.get('au_object_id')
        if au_object_id:
            au_object_id = int(au_object_id)

        return_url = request.query_params.get('return_url', '')

        # Create cmi5 session
        session = CMI5SessionService.create_session(
            user=request.user,
            au_type=au_type,
            au_object_id=au_object_id,
        )

        # Build launch URL with cmi5 parameters
        base_url = getattr(settings, 'CMI5_AU_BASE_URL', f'{request.scheme}://{request.get_host()}')

        # Determine AU endpoint based on type
        au_endpoints = {
            'gana_quiz': '/quiz/gana',
            'word_quiz': '/quiz/word',
        }
        au_endpoint = au_endpoints.get(au_type, f'/quiz/{au_type}')

        if au_object_id:
            au_endpoint = f'{au_endpoint}/{au_object_id}'

        # cmi5 launch parameters
        params = {
            'endpoint': f'{base_url}/api/v1/lrs/xapi/',
            'fetch': f'{base_url}/api/v1/lrs/cmi5/auth-token',
            'registration': str(session.registration),
            'activityId': session.au_id,
            'actor': f'{{"mbox":"mailto:{request.user.email}","name":"{request.user.username}"}}',
        }

        if return_url:
            params['returnURL'] = return_url

        launch_url = f'{base_url}{au_endpoint}?{urlencode(params)}'

        # Create LAUNCHED statement
        statement = StatementBuilder(request.user) \
            .verb(CMI5Verb.LAUNCHED, 'launched') \
            .object_activity(
                session.au_id,
                f'{au_type.replace("_", " ").title()}',
                XAPIActivityType.ASSESSMENT
            ) \
            .context(registration=session.registration) \
            .build()

        # Queue ES indexing
        try:
            index_statement_task.delay(str(statement.id))
            index_session_task.delay(str(session.id))
        except Exception as exc:
            logger.warning(f"Could not queue indexing: {exc}")

        return Response({
            'launch_url': launch_url,
            'registration': str(session.registration),
            'session_id': str(session.id),
            'au_id': session.au_id,
        })


class CMI5SessionView(APIView):
    """
    cmi5 Session management.

    Handles session lifecycle:
    - start: Create new session (LAUNCHED)
    - initialize: Mark session as initialized
    - terminate: End session with results
    - abandon: Abandon session without completion
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, session_id=None, action=None):
        """
        Handle session actions.

        URL patterns:
        - POST /cmi5/session/start - Start new session
        - POST /cmi5/session/{id}/initialize - Initialize
        - POST /cmi5/session/{id}/terminate - Terminate with results
        - POST /cmi5/session/{id}/abandon - Abandon
        """
        if action == 'start' or (session_id is None and action is None):
            return self._start_session(request)

        if not session_id:
            return Response(
                {'error': 'session_id required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = CMI5Session.objects.get(
                id=session_id,
                actor_user=request.user
            )
        except CMI5Session.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        if action == 'initialize':
            return self._initialize_session(request, session)
        elif action == 'terminate':
            return self._terminate_session(request, session)
        elif action == 'abandon':
            return self._abandon_session(request, session)
        else:
            return Response(
                {'error': f'Unknown action: {action}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    def get(self, request, session_id=None):
        """Get session details."""
        if session_id:
            try:
                session = CMI5Session.objects.get(
                    id=session_id,
                    actor_user=request.user
                )
                serializer = CMI5SessionSerializer(session)
                return Response(serializer.data)
            except CMI5Session.DoesNotExist:
                return Response(
                    {'error': 'Session not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # List user's sessions
            sessions = CMI5Session.objects.filter(
                actor_user=request.user
            ).order_by('-launched_at')[:20]
            serializer = CMI5SessionSerializer(sessions, many=True)
            return Response(serializer.data)

    def _start_session(self, request):
        """Start a new cmi5 session."""
        au_type = request.data.get('au_type')
        if not au_type:
            return Response(
                {'error': 'au_type required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        au_object_id = request.data.get('au_object_id')

        # Check for existing active session
        existing = CMI5SessionService.get_active_session(
            request.user, au_type, au_object_id
        )
        if existing:
            return Response({
                'session_id': str(existing.id),
                'registration': str(existing.registration),
                'message': 'Existing active session found',
            })

        # Create new session
        session = CMI5SessionService.create_session(
            user=request.user,
            au_type=au_type,
            au_object_id=au_object_id,
        )

        # Create LAUNCHED statement
        statement = StatementBuilder(request.user) \
            .verb(CMI5Verb.LAUNCHED, 'launched') \
            .object_activity(
                session.au_id,
                f'{au_type.replace("_", " ").title()}',
                XAPIActivityType.ASSESSMENT
            ) \
            .context(registration=session.registration) \
            .build()

        # Queue indexing
        try:
            index_statement_task.delay(str(statement.id))
            index_session_task.delay(str(session.id))
        except Exception as exc:
            logger.warning(f"Could not queue indexing: {exc}")

        serializer = CMI5SessionSerializer(session)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    def _initialize_session(self, request, session):
        """Initialize a cmi5 session (AU is ready)."""
        if session.state != CMI5Session.SessionState.LAUNCHED:
            return Response(
                {'error': f'Cannot initialize session in state: {session.state}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update session state
        session.initialize()

        # Create INITIALIZED statement
        statement = StatementBuilder(request.user) \
            .verb(CMI5Verb.INITIALIZED, 'initialized') \
            .object_activity(
                session.au_id,
                f'{session.au_type.replace("_", " ").title()}',
                XAPIActivityType.ASSESSMENT
            ) \
            .context(registration=session.registration) \
            .build()

        # Queue indexing
        try:
            index_statement_task.delay(str(statement.id))
            index_session_task.delay(str(session.id))
        except Exception as exc:
            logger.warning(f"Could not queue indexing: {exc}")

        serializer = CMI5SessionSerializer(session)
        return Response(serializer.data)

    def _terminate_session(self, request, session):
        """Terminate a cmi5 session with results."""
        if session.state not in [
            CMI5Session.SessionState.LAUNCHED,
            CMI5Session.SessionState.INITIALIZED
        ]:
            return Response(
                {'error': f'Cannot terminate session in state: {session.state}'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get results from request
        is_passed = request.data.get('passed')
        is_completed = request.data.get('completed', True)
        score = request.data.get('score')

        if score is not None:
            score = float(score)

        # Update session
        session.terminate(
            is_passed=is_passed,
            is_completed=is_completed,
            score=score,
        )

        # Create TERMINATED statement
        result_kwargs = {}
        if score is not None:
            result_kwargs['score_scaled'] = score
        if is_completed is not None:
            result_kwargs['completion'] = is_completed
        if is_passed is not None:
            result_kwargs['success'] = is_passed

        statement = StatementBuilder(request.user) \
            .verb(CMI5Verb.TERMINATED, 'terminated') \
            .object_activity(
                session.au_id,
                f'{session.au_type.replace("_", " ").title()}',
                XAPIActivityType.ASSESSMENT
            ) \
            .result(**result_kwargs) \
            .context(registration=session.registration) \
            .build()

        # Queue indexing
        try:
            index_statement_task.delay(str(statement.id))
            index_session_task.delay(str(session.id))
        except Exception as exc:
            logger.warning(f"Could not queue indexing: {exc}")

        serializer = CMI5SessionSerializer(session)
        return Response(serializer.data)

    def _abandon_session(self, request, session):
        """Abandon a cmi5 session."""
        if session.state == CMI5Session.SessionState.TERMINATED:
            return Response(
                {'error': 'Session already terminated'},
                status=status.HTTP_400_BAD_REQUEST
            )

        if session.state == CMI5Session.SessionState.ABANDONED:
            return Response(
                {'error': 'Session already abandoned'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Update session state
        session.abandon()

        # Create ABANDONED statement
        statement = StatementBuilder(request.user) \
            .verb(CMI5Verb.ABANDONED, 'abandoned') \
            .object_activity(
                session.au_id,
                f'{session.au_type.replace("_", " ").title()}',
                XAPIActivityType.ASSESSMENT
            ) \
            .context(registration=session.registration) \
            .build()

        # Queue indexing
        try:
            index_statement_task.delay(str(statement.id))
            index_session_task.delay(str(session.id))
        except Exception as exc:
            logger.warning(f"Could not queue indexing: {exc}")

        serializer = CMI5SessionSerializer(session)
        return Response(serializer.data)


class CMI5AuthTokenView(APIView):
    """
    cmi5 Auth Token endpoint.

    Called by AU to retrieve authentication token for xAPI communication.
    This is the 'fetch' URL in cmi5 launch parameters.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Issue auth token for cmi5 AU.

        The AU calls this endpoint with the fetch URL to get credentials
        for making xAPI requests.
        """
        registration = request.data.get('registration')
        if not registration:
            return Response(
                {'error': 'registration required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            session = CMI5Session.objects.get(
                registration=registration,
                actor_user=request.user
            )
        except CMI5Session.DoesNotExist:
            return Response(
                {'error': 'Session not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # For cmi5, we typically use OAuth tokens, but since we're using
        # session-based auth, we'll return the necessary info for the AU
        # to make authenticated requests

        # In a production environment, you might want to generate
        # a short-lived token here
        return Response({
            'auth-token': request.auth.key if hasattr(request, 'auth') and request.auth else None,
            'registration': str(session.registration),
            'session_id': str(session.id),
            'endpoint': f'{request.scheme}://{request.get_host()}/api/v1/lrs/xapi/',
        })
