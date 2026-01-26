"""
LRS App Tests

Tests for xAPI statements, cmi5 sessions, dashboard APIs, and LRS credentials.
"""

import uuid
from datetime import timedelta

from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status

from .models import XAPIStatement, CMI5Session, LRSCredential
from .services import StatementBuilder, QuizStatementService
from .constants import XAPIVerb, XAPIActivityType, QuizType, DEFAULT_MASTERY_SCORE


User = get_user_model()


class XAPIStatementModelTest(TestCase):
    """Tests for XAPIStatement model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )

    def test_create_statement(self):
        """Test creating a basic xAPI statement."""
        statement = XAPIStatement.objects.create(
            actor_user=self.user,
            actor_mbox=self.user.email,
            actor_name=self.user.username,
            verb_id=XAPIVerb.ANSWERED,
            verb_display='answered',
            object_id='https://linguapal.com/quiz/gana_quiz/1/question/1',
            object_definition={
                'type': XAPIActivityType.QUESTION,
                'name': {'ko': '문제 #1'}
            },
            result_success=True,
            result_response='a',
        )

        self.assertIsNotNone(statement.id)
        self.assertEqual(statement.actor_user, self.user)
        self.assertEqual(statement.verb_id, XAPIVerb.ANSWERED)
        self.assertTrue(statement.result_success)

    def test_to_xapi_format(self):
        """Test converting statement to xAPI JSON format."""
        registration = uuid.uuid4()
        statement = XAPIStatement.objects.create(
            actor_user=self.user,
            actor_mbox=self.user.email,
            actor_name=self.user.username,
            verb_id=XAPIVerb.COMPLETED,
            verb_display='completed',
            object_id='https://linguapal.com/quiz/gana_quiz/1',
            object_definition={
                'type': XAPIActivityType.ASSESSMENT,
                'name': {'ko': '가나 퀴즈 #1'}
            },
            result_completion=True,
            result_score_scaled=0.8,
            result_score_raw=8,
            result_score_min=0,
            result_score_max=10,
            context_registration=registration,
        )

        xapi_json = statement.to_xapi_format()

        self.assertEqual(xapi_json['id'], str(statement.id))
        self.assertEqual(xapi_json['actor']['mbox'], f'mailto:{self.user.email}')
        self.assertEqual(xapi_json['verb']['id'], XAPIVerb.COMPLETED)
        self.assertEqual(xapi_json['result']['score']['scaled'], 0.8)
        self.assertEqual(xapi_json['context']['registration'], str(registration))

    def test_statement_without_result(self):
        """Test creating statement without result."""
        statement = XAPIStatement.objects.create(
            actor_user=self.user,
            actor_mbox=self.user.email,
            actor_name=self.user.username,
            verb_id=XAPIVerb.INITIALIZED,
            verb_display='initialized',
            object_id='https://linguapal.com/quiz/gana_quiz/1',
            object_definition={
                'type': XAPIActivityType.ASSESSMENT,
            },
        )

        xapi_json = statement.to_xapi_format()
        self.assertNotIn('result', xapi_json)


class CMI5SessionModelTest(TestCase):
    """Tests for CMI5Session model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )

    def test_create_session(self):
        """Test creating a cmi5 session."""
        session = CMI5Session.objects.create(
            actor_user=self.user,
            au_id='https://linguapal.com/au/gana_quiz/1',
            au_type='gana_quiz',
            au_object_id=1,
        )

        self.assertIsNotNone(session.id)
        self.assertIsNotNone(session.registration)
        self.assertEqual(session.state, CMI5Session.SessionState.LAUNCHED)
        self.assertEqual(session.mastery_score, DEFAULT_MASTERY_SCORE)

    def test_session_initialize(self):
        """Test initializing a session."""
        session = CMI5Session.objects.create(
            actor_user=self.user,
            au_id='https://linguapal.com/au/gana_quiz/1',
            au_type='gana_quiz',
        )

        session.initialize()

        self.assertEqual(session.state, CMI5Session.SessionState.INITIALIZED)
        self.assertIsNotNone(session.initialized_at)

    def test_session_terminate(self):
        """Test terminating a session."""
        session = CMI5Session.objects.create(
            actor_user=self.user,
            au_id='https://linguapal.com/au/gana_quiz/1',
            au_type='gana_quiz',
        )
        session.initialize()

        session.terminate(is_passed=True, is_completed=True, score=0.9)

        self.assertEqual(session.state, CMI5Session.SessionState.TERMINATED)
        self.assertIsNotNone(session.terminated_at)
        self.assertTrue(session.is_passed)
        self.assertTrue(session.is_completed)
        self.assertEqual(session.score_scaled, 0.9)

    def test_session_abandon(self):
        """Test abandoning a session."""
        session = CMI5Session.objects.create(
            actor_user=self.user,
            au_id='https://linguapal.com/au/gana_quiz/1',
            au_type='gana_quiz',
        )

        session.abandon()

        self.assertEqual(session.state, CMI5Session.SessionState.ABANDONED)
        self.assertIsNotNone(session.terminated_at)


class LRSCredentialModelTest(TestCase):
    """Tests for LRSCredential model."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            username='admin',
            role='admin'
        )

    def test_generate_credentials(self):
        """Test generating credentials."""
        credential, secret = LRSCredential.generate_credentials(
            name='Test Credential',
            permissions=['read', 'write'],
            created_by=self.user
        )

        self.assertIsNotNone(credential.id)
        self.assertIsNotNone(credential.key)
        self.assertIsNotNone(secret)
        self.assertTrue(credential.is_active)
        self.assertEqual(credential.permissions, ['read', 'write'])

    def test_check_secret(self):
        """Test verifying credential secret."""
        credential, secret = LRSCredential.generate_credentials(
            name='Test Credential',
            created_by=self.user
        )

        self.assertTrue(credential.check_secret(secret))
        self.assertFalse(credential.check_secret('wrong_secret'))

    def test_has_permission(self):
        """Test permission checking."""
        credential, _ = LRSCredential.generate_credentials(
            name='Read Only',
            permissions=['read'],
            created_by=self.user
        )

        self.assertTrue(credential.has_permission('read'))
        self.assertFalse(credential.has_permission('write'))


class StatementBuilderServiceTest(TestCase):
    """Tests for StatementBuilder service."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )

    def test_build_statement(self):
        """Test building a statement with StatementBuilder."""
        statement = (
            StatementBuilder(self.user)
            .verb(XAPIVerb.ANSWERED)
            .object_activity(
                'quiz/gana_quiz/1/question/1',
                '문제 #1',
                XAPIActivityType.QUESTION
            )
            .result(success=True, response='a')
            .context(quiz_type='gana_to_romaji')
            .build()
        )

        self.assertIsNotNone(statement.id)
        self.assertEqual(statement.verb_id, XAPIVerb.ANSWERED)
        self.assertTrue(statement.result_success)
        self.assertEqual(statement.result_response, 'a')
        self.assertEqual(statement.context_extensions.get('quiz_type'), 'gana_to_romaji')

    def test_build_without_verb_raises_error(self):
        """Test that building without verb raises error."""
        builder = (
            StatementBuilder(self.user)
            .object_activity('quiz/1', 'Quiz')
        )

        with self.assertRaises(ValueError):
            builder.build()

    def test_build_without_object_raises_error(self):
        """Test that building without object raises error."""
        builder = StatementBuilder(self.user).verb(XAPIVerb.ANSWERED)

        with self.assertRaises(ValueError):
            builder.build()

    def test_create_from_data(self):
        """Test creating statement from dictionary data."""
        data = {
            'actor_user_id': self.user.id,
            'verb': 'answered',
            'object_id': 'quiz/gana_quiz/1/question/1',
            'object_name': '문제 #1',
            'object_type': XAPIActivityType.QUESTION,
            'result': {
                'success': True,
                'response': 'a',
            },
            'context': {
                'quiz_type': 'gana_to_romaji',
            }
        }

        statement = StatementBuilder.create_from_data(data)

        self.assertIsNotNone(statement.id)
        self.assertEqual(statement.verb_id, XAPIVerb.ANSWERED)
        self.assertTrue(statement.result_success)


class DashboardAPITest(APITestCase):
    """Tests for Dashboard API endpoints."""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            username='admin',
            role='admin'  # Sets is_staff and is_superuser via User.save()
        )
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            username='regularuser'
        )
        self.client = APIClient()

        # Create some test statements
        for i in range(5):
            XAPIStatement.objects.create(
                actor_user=self.regular_user,
                actor_mbox=self.regular_user.email,
                actor_name=self.regular_user.username,
                verb_id=XAPIVerb.ANSWERED,
                verb_display='answered',
                object_id=f'https://linguapal.com/quiz/gana_quiz/1/question/{i+1}',
                object_definition={'type': XAPIActivityType.QUESTION},
                result_success=i % 2 == 0,  # Alternate correct/incorrect
            )

        # Create a completed quiz statement
        XAPIStatement.objects.create(
            actor_user=self.regular_user,
            actor_mbox=self.regular_user.email,
            actor_name=self.regular_user.username,
            verb_id=XAPIVerb.COMPLETED,
            verb_display='completed',
            object_id='https://linguapal.com/quiz/gana_quiz/1',
            object_definition={'type': XAPIActivityType.ASSESSMENT},
            result_completion=True,
            result_score_scaled=0.6,
        )

    def test_dashboard_overview_requires_staff(self):
        """Test that dashboard overview requires staff permission."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.get('/api/v1/lrs/dashboard/overview')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_dashboard_overview_success(self):
        """Test dashboard overview with admin user."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/lrs/dashboard/overview')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_users', response.data)
        self.assertIn('total_questions', response.data)
        self.assertIn('overall_accuracy', response.data)

    def test_dashboard_users_list(self):
        """Test dashboard users endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/lrs/dashboard/users')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_dashboard_trends(self):
        """Test dashboard trends endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/lrs/dashboard/trends?days=7')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIsInstance(response.data, list)

    def test_dashboard_realtime(self):
        """Test dashboard realtime endpoint."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/lrs/dashboard/realtime')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('stats_24h', response.data)


class StatementListAPITest(APITestCase):
    """Tests for Statement List API."""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            username='admin',
            role='admin'
        )
        self.user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            username='user'
        )
        self.client = APIClient()

        # Create test statements
        for i in range(15):
            XAPIStatement.objects.create(
                actor_user=self.user,
                actor_mbox=self.user.email,
                actor_name=self.user.username,
                verb_id=XAPIVerb.ANSWERED if i % 2 == 0 else XAPIVerb.COMPLETED,
                verb_display='answered' if i % 2 == 0 else 'completed',
                object_id=f'https://linguapal.com/quiz/gana_quiz/{i+1}',
                object_definition={'type': XAPIActivityType.ASSESSMENT},
            )

    def test_statement_list_paginated(self):
        """Test statement list returns paginated results."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/lrs/statements?page_size=5')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('results', response.data)
        self.assertEqual(len(response.data['results']), 5)

    def test_statement_list_filter_by_verb(self):
        """Test filtering statements by verb."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f'/api/v1/lrs/statements?verb={XAPIVerb.ANSWERED}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for stmt in response.data['results']:
            self.assertEqual(stmt['verb']['id'], XAPIVerb.ANSWERED)

    def test_statement_list_filter_by_user(self):
        """Test filtering statements by user."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get(f'/api/v1/lrs/statements?user_id={self.user.id}')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        for stmt in response.data['results']:
            self.assertEqual(stmt['actor']['mbox'], f'mailto:{self.user.email}')


class XAPIEndpointTest(APITestCase):
    """Tests for xAPI LRS endpoints."""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            username='admin',
            role='admin'
        )
        self.client = APIClient()

        # Create LRS credential
        self.credential, self.secret = LRSCredential.generate_credentials(
            name='Test LRS',
            permissions=['read', 'write'],
            created_by=self.admin_user
        )

    def test_about_endpoint(self):
        """Test xAPI about endpoint."""
        response = self.client.get('/api/v1/lrs/xapi/about')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('version', response.data)

    def test_post_statement_without_auth(self):
        """Test posting statement without authentication fails."""
        statement_data = {
            'actor': {
                'mbox': 'mailto:test@example.com',
                'name': 'Test User'
            },
            'verb': {
                'id': XAPIVerb.ANSWERED,
                'display': {'en-US': 'answered'}
            },
            'object': {
                'id': 'https://linguapal.com/quiz/1',
                'definition': {'type': XAPIActivityType.ASSESSMENT}
            }
        }

        response = self.client.post(
            '/api/v1/lrs/xapi/statements',
            statement_data,
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LRSCredentialAPITest(APITestCase):
    """Tests for LRS Credential API."""

    def setUp(self):
        self.admin_user = User.objects.create_user(
            email='admin@example.com',
            password='adminpass123',
            username='admin',
            role='admin'
        )
        self.regular_user = User.objects.create_user(
            email='user@example.com',
            password='userpass123',
            username='user'
        )
        self.client = APIClient()

    def test_create_credential_requires_admin(self):
        """Test that creating credentials requires admin."""
        self.client.force_authenticate(user=self.regular_user)
        response = self.client.post(
            '/api/v1/lrs/credentials/',
            {'name': 'Test Credential'},
            format='json'
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_create_credential_success(self):
        """Test creating credential as admin."""
        self.client.force_authenticate(user=self.admin_user)
        response = self.client.post(
            '/api/v1/lrs/credentials/',
            {'name': 'Test Credential', 'permissions': ['read', 'write']},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('key', response.data)
        self.assertIn('secret', response.data)
        self.assertIn('message', response.data)

    def test_list_credentials(self):
        """Test listing credentials."""
        # Create some credentials
        LRSCredential.generate_credentials('Cred 1', created_by=self.admin_user)
        LRSCredential.generate_credentials('Cred 2', created_by=self.admin_user)

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.get('/api/v1/lrs/credentials/')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 2)

    def test_delete_credential_deactivates(self):
        """Test that deleting a credential deactivates it."""
        credential, _ = LRSCredential.generate_credentials(
            'To Delete',
            created_by=self.admin_user
        )

        self.client.force_authenticate(user=self.admin_user)
        response = self.client.delete(f'/api/v1/lrs/credentials/{credential.id}/')

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify it's deactivated, not deleted
        credential.refresh_from_db()
        self.assertFalse(credential.is_active)


class CMI5SessionAPITest(APITestCase):
    """Tests for cmi5 Session API."""

    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123',
            username='testuser'
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_start_session(self):
        """Test starting a cmi5 session."""
        response = self.client.post(
            '/api/v1/lrs/cmi5/session/start',
            {
                'au_type': 'gana_quiz',
                'au_object_id': 1,
            },
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)
        self.assertIn('registration', response.data)
        self.assertEqual(response.data['state'], 'launched')

    def test_initialize_session(self):
        """Test initializing a cmi5 session."""
        # First create a session
        session = CMI5Session.objects.create(
            actor_user=self.user,
            au_id='https://linguapal.com/au/gana_quiz/1',
            au_type='gana_quiz',
        )

        response = self.client.post(
            f'/api/v1/lrs/cmi5/session/{session.id}/initialize'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['state'], 'initialized')

    def test_terminate_session(self):
        """Test terminating a cmi5 session."""
        session = CMI5Session.objects.create(
            actor_user=self.user,
            au_id='https://linguapal.com/au/gana_quiz/1',
            au_type='gana_quiz',
        )
        session.initialize()

        response = self.client.post(
            f'/api/v1/lrs/cmi5/session/{session.id}/terminate',
            {'score': 0.85, 'is_completed': True},
            format='json'
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['state'], 'terminated')
        self.assertTrue(response.data['is_passed'])
