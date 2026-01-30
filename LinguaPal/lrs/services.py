"""
LRS Services

xAPI Statement builder and helper services.
"""

import uuid
from typing import Optional, Dict, Any, List
from datetime import timedelta

from django.conf import settings
from django.utils import timezone

from .models import XAPIStatement, CMI5Session
from .constants import (
    XAPIVerb, CMI5Verb, XAPIActivityType, QuizType,
    LINGUAPAL_BASE_IRI, DEFAULT_MASTERY_SCORE,
    ActivityID, get_activity_name
)


class StatementBuilder:
    """
    Builder class for creating xAPI statements.

    Usage:
        statement = (
            StatementBuilder(user)
            .verb(XAPIVerb.ANSWERED)
            .object_activity('quiz/gana/123', 'Gana Quiz', XAPIActivityType.ASSESSMENT)
            .result(success=True, response='a', score=0.9)
            .context(quiz_type='gana_to_romaji', question_number=5)
            .build()
        )
    """

    def __init__(self, user):
        self.user = user
        self._verb_id: Optional[str] = None
        self._verb_display: Optional[str] = None
        self._object_id: Optional[str] = None
        self._object_type: str = 'Activity'
        self._object_definition: Dict = {}
        self._result: Dict = {}
        self._context_registration: Optional[uuid.UUID] = None
        self._context_extensions: Dict = {}
        self._timestamp: Optional[timezone.datetime] = None

    def verb(self, verb_id: str, display: str = None) -> 'StatementBuilder':
        """Set the verb for this statement."""
        self._verb_id = verb_id
        self._verb_display = display or XAPIVerb.get_display(verb_id)
        return self

    def object_activity(
        self,
        activity_id: str,
        name: str = None,
        activity_type: str = None,
        description: str = None
    ) -> 'StatementBuilder':
        """Set the object (Activity) for this statement."""
        if not activity_id.startswith('http'):
            activity_id = f"{LINGUAPAL_BASE_IRI}/{activity_id}"

        self._object_id = activity_id
        self._object_type = 'Activity'
        self._object_definition = {}

        if activity_type:
            self._object_definition['type'] = activity_type
        if name:
            self._object_definition['name'] = {'ko': name}
        if description:
            self._object_definition['description'] = {'ko': description}

        return self

    def result(
        self,
        success: bool = None,
        response: str = None,
        score_scaled: float = None,
        score_raw: float = None,
        score_min: float = None,
        score_max: float = None,
        completion: bool = None,
        duration: timedelta = None
    ) -> 'StatementBuilder':
        """Set the result for this statement."""
        if success is not None:
            self._result['success'] = success
        if response is not None:
            self._result['response'] = response
        if score_scaled is not None:
            self._result['score_scaled'] = score_scaled
        if score_raw is not None:
            self._result['score_raw'] = score_raw
        if score_min is not None:
            self._result['score_min'] = score_min
        if score_max is not None:
            self._result['score_max'] = score_max
        if completion is not None:
            self._result['completion'] = completion
        if duration is not None:
            self._result['duration'] = duration
        return self

    def context(
        self,
        registration: uuid.UUID = None,
        **extensions
    ) -> 'StatementBuilder':
        """Set the context for this statement."""
        if registration:
            self._context_registration = registration
        self._context_extensions.update(extensions)
        return self

    def timestamp(self, ts: timezone.datetime) -> 'StatementBuilder':
        """Set a custom timestamp."""
        self._timestamp = ts
        return self

    def build(self) -> XAPIStatement:
        """Build and save the xAPI statement."""
        if not self._verb_id:
            raise ValueError("Verb is required")
        if not self._object_id:
            raise ValueError("Object is required")

        statement = XAPIStatement(
            actor_user=self.user,
            actor_mbox=self.user.email,
            actor_name=self.user.username or self.user.email,
            verb_id=self._verb_id,
            verb_display=self._verb_display,
            object_type=self._object_type,
            object_id=self._object_id,
            object_definition=self._object_definition,
            context_registration=self._context_registration,
            context_extensions=self._context_extensions,
        )

        # Set result fields
        if 'success' in self._result:
            statement.result_success = self._result['success']
        if 'response' in self._result:
            statement.result_response = self._result['response']
        if 'score_scaled' in self._result:
            statement.result_score_scaled = self._result['score_scaled']
        if 'score_raw' in self._result:
            statement.result_score_raw = self._result['score_raw']
        if 'score_min' in self._result:
            statement.result_score_min = self._result['score_min']
        if 'score_max' in self._result:
            statement.result_score_max = self._result['score_max']
        if 'completion' in self._result:
            statement.result_completion = self._result['completion']
        if 'duration' in self._result:
            statement.result_duration = self._result['duration']

        # Set timestamp
        if self._timestamp:
            statement.timestamp = self._timestamp

        statement.save()
        return statement

    @classmethod
    def create_from_data(cls, data: Dict[str, Any]) -> XAPIStatement:
        """
        Create a statement from a dictionary.

        Used by Celery tasks for async statement creation.
        """
        from accounts.models import User

        user_id = data.get('actor_user_id')
        user = User.objects.get(pk=user_id)

        builder = cls(user)

        # Set verb
        verb = data.get('verb')
        if isinstance(verb, str):
            # Map short verb names to full IRIs
            verb_map = {
                'initialized': XAPIVerb.INITIALIZED,
                'answered': XAPIVerb.ANSWERED,
                'progressed': XAPIVerb.PROGRESSED,
                'completed': XAPIVerb.COMPLETED,
                'passed': XAPIVerb.PASSED,
                'failed': XAPIVerb.FAILED,
                'terminated': XAPIVerb.TERMINATED,
            }
            verb = verb_map.get(verb, verb)
        builder.verb(verb)

        # Set object
        object_id = data.get('object_id', '')
        object_name = data.get('object_name')
        object_type = data.get('object_type', XAPIActivityType.ASSESSMENT)
        object_desc = data.get('object_description')
        builder.object_activity(object_id, object_name, object_type, object_desc)

        # Set result if present
        result = data.get('result', {})
        if result:
            builder.result(
                success=result.get('success'),
                response=result.get('response'),
                score_scaled=result.get('score_scaled'),
                score_raw=result.get('score_raw'),
                score_min=result.get('score_min'),
                score_max=result.get('score_max'),
                completion=result.get('completion'),
            )

        # Set context
        context = data.get('context', {})
        registration = context.pop('registration', None)
        if registration:
            if isinstance(registration, str):
                registration = uuid.UUID(registration)
            builder.context(registration=registration, **context)
        elif context:
            builder.context(**context)

        return builder.build()


class QuizStatementService:
    """
    Service for creating quiz-related xAPI statements.

    Uses ActivityID to generate structured Activity IRIs that group by:
    - Gana Quiz: character_set + quiz_type (e.g., hiragana + gana_to_romaji)
    - Word Quiz: language_code + quiz_type (e.g., es + word_to_native)
    """

    @staticmethod
    def _get_activity_info(quiz) -> Dict[str, Any]:
        """
        Extract activity information from a quiz.

        Returns:
            Dict with category, subcategory, quiz_type, activity_id, activity_name
        """
        is_gana = hasattr(quiz, 'character_set')

        if is_gana:
            character_set = quiz.character_set
            quiz_type = quiz.quiz_type
            activity_id = ActivityID.gana_quiz_instance(character_set, quiz_type, quiz.id)
            activity_name = get_activity_name('gana', character_set, quiz_type)
            return {
                'category': 'gana',
                'subcategory': character_set,
                'quiz_type': quiz_type,
                'activity_id': activity_id,
                'activity_name': activity_name,
                'language_code': None,
                'language_name': None,
            }
        else:
            language_code = quiz.learning_language.code
            language_name = quiz.learning_language.name_ko  # Use Korean name
            quiz_type = quiz.quiz_type
            activity_id = ActivityID.word_quiz_instance(language_code, quiz_type, quiz.id)
            activity_name = get_activity_name('word', language_code, quiz_type, language_name)
            return {
                'category': 'word',
                'subcategory': language_code,
                'quiz_type': quiz_type,
                'activity_id': activity_id,
                'activity_name': activity_name,
                'language_code': language_code,
                'language_name': language_name,
            }

    @staticmethod
    def _get_question_activity_id(quiz, question) -> str:
        """Generate Activity ID for a question."""
        is_gana = hasattr(quiz, 'character_set')

        if is_gana:
            return ActivityID.gana_question(
                quiz.character_set, quiz.quiz_type, quiz.id, question.id
            )
        else:
            return ActivityID.word_question(
                quiz.learning_language.code, quiz.quiz_type, quiz.id, question.id
            )

    @staticmethod
    def quiz_initialized(
        user,
        quiz,
        quiz_type: str,
        registration: uuid.UUID = None
    ) -> Dict[str, Any]:
        """
        Create data for INITIALIZED statement when quiz starts.

        Returns data dict for async task.
        """
        activity_info = QuizStatementService._get_activity_info(quiz)

        return {
            'actor_user_id': user.id,
            'verb': 'initialized',
            'object_id': activity_info['activity_id'],
            'object_name': activity_info['activity_name'],
            'object_type': XAPIActivityType.ASSESSMENT,
            'context': {
                'registration': str(registration) if registration else str(uuid.uuid4()),
                'quiz_type': quiz_type,
                'total_questions': quiz.total_questions,
                'category': activity_info['category'],
                'subcategory': activity_info['subcategory'],
                'language_code': activity_info.get('language_code'),
                'language_name': activity_info.get('language_name'),
            }
        }

    @staticmethod
    def question_answered(
        user,
        quiz,
        question,
        user_answer: str,
        is_correct: bool,
        correct_answer: str,
        registration: uuid.UUID = None
    ) -> Dict[str, Any]:
        """
        Create data for ANSWERED statement when question is answered.
        """
        activity_info = QuizStatementService._get_activity_info(quiz)
        question_activity_id = QuizStatementService._get_question_activity_id(quiz, question)

        return {
            'actor_user_id': user.id,
            'verb': 'answered',
            'object_id': question_activity_id,
            'object_name': f"문제 #{question.question_number}",
            'object_type': XAPIActivityType.QUESTION,
            'result': {
                'success': is_correct,
                'response': user_answer,
            },
            'context': {
                'registration': str(registration) if registration else None,
                'quiz_type': getattr(quiz, 'quiz_type', None),
                'question_number': question.question_number,
                'correct_answer': correct_answer,
                'category': activity_info['category'],
                'subcategory': activity_info['subcategory'],
                'language_code': activity_info.get('language_code'),
            }
        }

    @staticmethod
    def quiz_completed(
        user,
        quiz,
        registration: uuid.UUID = None
    ) -> List[Dict[str, Any]]:
        """
        Create data for completion statements (COMPLETED, PASSED/FAILED).

        Returns list of statement data dicts.
        """
        activity_info = QuizStatementService._get_activity_info(quiz)

        score_scaled = quiz.correct_count / quiz.total_questions if quiz.total_questions > 0 else 0
        mastery_score = getattr(settings, 'LRS_MASTERY_SCORE', DEFAULT_MASTERY_SCORE)
        passed = score_scaled >= mastery_score

        reg_str = str(registration) if registration else None

        statements = []

        # COMPLETED statement
        statements.append({
            'actor_user_id': user.id,
            'verb': 'completed',
            'object_id': activity_info['activity_id'],
            'object_name': activity_info['activity_name'],
            'object_type': XAPIActivityType.ASSESSMENT,
            'result': {
                'completion': True,
                'score_scaled': score_scaled,
                'score_raw': quiz.correct_count,
                'score_min': 0,
                'score_max': quiz.total_questions,
            },
            'context': {
                'registration': reg_str,
                'quiz_type': getattr(quiz, 'quiz_type', None),
                'category': activity_info['category'],
                'subcategory': activity_info['subcategory'],
                'language_code': activity_info.get('language_code'),
            }
        })

        # PASSED or FAILED statement
        statements.append({
            'actor_user_id': user.id,
            'verb': 'passed' if passed else 'failed',
            'object_id': activity_info['activity_id'],
            'object_name': activity_info['activity_name'],
            'object_type': XAPIActivityType.ASSESSMENT,
            'result': {
                'success': passed,
                'score_scaled': score_scaled,
            },
            'context': {
                'registration': reg_str,
                'mastery_score': mastery_score,
                'category': activity_info['category'],
                'subcategory': activity_info['subcategory'],
                'language_code': activity_info.get('language_code'),
            }
        })

        return statements


class CMI5SessionService:
    """
    Service for managing cmi5 sessions.
    """

    @staticmethod
    def create_session(
        user,
        au_type: str,
        au_object_id: int = None,
        mastery_score: float = DEFAULT_MASTERY_SCORE
    ) -> CMI5Session:
        """Create a new cmi5 session."""
        au_id = f"{LINGUAPAL_BASE_IRI}/au/{au_type}/{au_object_id or 'new'}"

        session = CMI5Session.objects.create(
            actor_user=user,
            au_id=au_id,
            au_type=au_type,
            au_object_id=au_object_id,
            mastery_score=mastery_score,
        )
        return session

    @staticmethod
    def get_active_session(user, au_type: str, au_object_id: int = None) -> Optional[CMI5Session]:
        """Get an active (non-terminated) session."""
        queryset = CMI5Session.objects.filter(
            actor_user=user,
            au_type=au_type,
            state__in=[CMI5Session.SessionState.LAUNCHED, CMI5Session.SessionState.INITIALIZED]
        )
        if au_object_id:
            queryset = queryset.filter(au_object_id=au_object_id)
        return queryset.first()
