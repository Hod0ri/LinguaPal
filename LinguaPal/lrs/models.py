"""
LRS Models

xAPI Statement storage and cmi5 session management models.
"""

import uuid
import hashlib
from django.db import models
from django.conf import settings
from django.utils import timezone

from .constants import CMI5LaunchMode, CMI5MoveOn, DEFAULT_MASTERY_SCORE


class XAPIStatement(models.Model):
    """
    xAPI Statement model following the xAPI 1.0.3 specification.

    Stores learning experience statements with actor, verb, object,
    result, and context components.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Actor (Agent)
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='xapi_statements',
        help_text='The user who performed the action'
    )
    actor_mbox = models.EmailField(
        help_text='Actor email in mbox format (mailto:user@example.com)'
    )
    actor_name = models.CharField(
        max_length=100,
        help_text='Display name of the actor'
    )

    # Verb
    verb_id = models.URLField(
        help_text='Verb IRI (e.g., http://adlnet.gov/expapi/verbs/answered)'
    )
    verb_display = models.CharField(
        max_length=50,
        help_text='Human-readable verb name'
    )

    # Object (Activity)
    object_type = models.CharField(
        max_length=50,
        default='Activity',
        help_text='Object type (usually Activity)'
    )
    object_id = models.URLField(
        help_text='Activity IRI (e.g., https://linguapal.com/quiz/gana/123)'
    )
    object_definition = models.JSONField(
        default=dict,
        help_text='Activity definition (type, name, description, etc.)'
    )

    # Result (optional)
    result_success = models.BooleanField(
        null=True,
        blank=True,
        help_text='Whether the attempt was successful'
    )
    result_response = models.TextField(
        blank=True,
        default='',
        help_text='The response given by the actor'
    )
    result_score_scaled = models.FloatField(
        null=True,
        blank=True,
        help_text='Score between -1 and 1'
    )
    result_score_raw = models.FloatField(
        null=True,
        blank=True,
        help_text='Raw score value'
    )
    result_score_min = models.FloatField(
        null=True,
        blank=True,
        help_text='Minimum possible score'
    )
    result_score_max = models.FloatField(
        null=True,
        blank=True,
        help_text='Maximum possible score'
    )
    result_completion = models.BooleanField(
        null=True,
        blank=True,
        help_text='Whether the activity was completed'
    )
    result_duration = models.DurationField(
        null=True,
        blank=True,
        help_text='Duration of the activity (ISO 8601 duration)'
    )

    # Context (optional)
    context_registration = models.UUIDField(
        null=True,
        blank=True,
        help_text='Registration UUID for grouping related statements'
    )
    context_extensions = models.JSONField(
        default=dict,
        help_text='Additional context data (quiz_type, character_set, etc.)'
    )

    # Metadata
    timestamp = models.DateTimeField(
        default=timezone.now,
        help_text='When the experience occurred'
    )
    stored = models.DateTimeField(
        auto_now_add=True,
        help_text='When the statement was stored'
    )

    class Meta:
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['actor_user', '-timestamp']),
            models.Index(fields=['verb_id']),
            models.Index(fields=['object_id']),
            models.Index(fields=['timestamp']),
            models.Index(fields=['context_registration']),
        ]
        verbose_name = 'xAPI Statement'
        verbose_name_plural = 'xAPI Statements'

    def __str__(self):
        return f"{self.actor_name} {self.verb_display} {self.object_id}"

    def to_xapi_format(self) -> dict:
        """Convert to xAPI JSON format."""
        statement = {
            'id': str(self.id),
            'actor': {
                'objectType': 'Agent',
                'mbox': f'mailto:{self.actor_mbox}',
                'name': self.actor_name,
            },
            'verb': {
                'id': self.verb_id,
                'display': {'en-US': self.verb_display},
            },
            'object': {
                'objectType': self.object_type,
                'id': self.object_id,
                'definition': self.object_definition,
            },
            'timestamp': self.timestamp.isoformat(),
            'stored': self.stored.isoformat() if self.stored else None,
        }

        # Add result if present
        if any([
            self.result_success is not None,
            self.result_response,
            self.result_score_scaled is not None,
            self.result_completion is not None,
        ]):
            result = {}
            if self.result_success is not None:
                result['success'] = self.result_success
            if self.result_response:
                result['response'] = self.result_response
            if self.result_completion is not None:
                result['completion'] = self.result_completion
            if self.result_duration:
                result['duration'] = self._duration_to_iso8601(self.result_duration)

            # Add score if present
            if self.result_score_scaled is not None:
                result['score'] = {'scaled': self.result_score_scaled}
                if self.result_score_raw is not None:
                    result['score']['raw'] = self.result_score_raw
                if self.result_score_min is not None:
                    result['score']['min'] = self.result_score_min
                if self.result_score_max is not None:
                    result['score']['max'] = self.result_score_max

            statement['result'] = result

        # Add context if present
        if self.context_registration or self.context_extensions:
            context = {}
            if self.context_registration:
                context['registration'] = str(self.context_registration)
            if self.context_extensions:
                context['extensions'] = self.context_extensions
            statement['context'] = context

        return statement

    @staticmethod
    def _duration_to_iso8601(duration) -> str:
        """Convert timedelta to ISO 8601 duration format."""
        total_seconds = int(duration.total_seconds())
        hours, remainder = divmod(total_seconds, 3600)
        minutes, seconds = divmod(remainder, 60)
        return f'PT{hours}H{minutes}M{seconds}S'


class CMI5Session(models.Model):
    """
    cmi5 Learning Session model.

    Tracks the lifecycle of a cmi5 Assignable Unit (AU) session
    from launch through termination or abandonment.
    """

    class SessionState(models.TextChoices):
        LAUNCHED = 'launched', 'Launched'
        INITIALIZED = 'initialized', 'Initialized'
        TERMINATED = 'terminated', 'Terminated'
        ABANDONED = 'abandoned', 'Abandoned'

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    # Registration (cmi5 required)
    registration = models.UUIDField(
        unique=True,
        default=uuid.uuid4,
        help_text='cmi5 registration UUID'
    )

    # Actor
    actor_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cmi5_sessions',
        help_text='The learner'
    )

    # AU (Assignable Unit) information
    au_id = models.CharField(
        max_length=500,
        help_text='Activity ID of the AU'
    )
    au_type = models.CharField(
        max_length=50,
        help_text='Type of AU (gana_quiz, word_quiz)'
    )
    au_object_id = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Quiz ID reference'
    )

    # Session state
    state = models.CharField(
        max_length=20,
        choices=SessionState.choices,
        default=SessionState.LAUNCHED,
        help_text='Current session state'
    )

    # cmi5 context
    mastery_score = models.FloatField(
        default=DEFAULT_MASTERY_SCORE,
        help_text='Required score to pass (0.0 to 1.0)'
    )
    launch_mode = models.CharField(
        max_length=20,
        default=CMI5LaunchMode.NORMAL,
        help_text='Launch mode (Normal, Browse, Review)'
    )
    move_on = models.CharField(
        max_length=30,
        default=CMI5MoveOn.COMPLETED_AND_PASSED,
        help_text='Condition to move on'
    )

    # Timestamps
    launched_at = models.DateTimeField(
        auto_now_add=True,
        help_text='When the session was launched'
    )
    initialized_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the AU was initialized'
    )
    terminated_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='When the session ended'
    )

    # Result
    is_passed = models.BooleanField(
        null=True,
        blank=True,
        help_text='Whether the learner passed'
    )
    is_completed = models.BooleanField(
        null=True,
        blank=True,
        help_text='Whether the AU was completed'
    )
    score_scaled = models.FloatField(
        null=True,
        blank=True,
        help_text='Final score (0.0 to 1.0)'
    )

    class Meta:
        ordering = ['-launched_at']
        indexes = [
            models.Index(fields=['actor_user', '-launched_at']),
            models.Index(fields=['registration']),
            models.Index(fields=['state']),
            models.Index(fields=['au_type']),
        ]
        verbose_name = 'cmi5 Session'
        verbose_name_plural = 'cmi5 Sessions'

    def __str__(self):
        return f"{self.actor_user} - {self.au_type} ({self.state})"

    def initialize(self):
        """Mark session as initialized."""
        self.state = self.SessionState.INITIALIZED
        self.initialized_at = timezone.now()
        self.save(update_fields=['state', 'initialized_at'])

    def terminate(self, is_passed: bool = None, is_completed: bool = None, score: float = None):
        """Mark session as terminated with results."""
        self.state = self.SessionState.TERMINATED
        self.terminated_at = timezone.now()
        if is_passed is not None:
            self.is_passed = is_passed
        if is_completed is not None:
            self.is_completed = is_completed
        if score is not None:
            self.score_scaled = score
            # Auto-determine passed based on mastery score
            if self.is_passed is None:
                self.is_passed = score >= self.mastery_score
        self.save()

    def abandon(self):
        """Mark session as abandoned."""
        self.state = self.SessionState.ABANDONED
        self.terminated_at = timezone.now()
        self.save(update_fields=['state', 'terminated_at'])


class LRSCredential(models.Model):
    """
    LRS API Credentials for external xAPI statement submission.

    Provides Basic Auth credentials for external systems to
    submit statements to the LRS.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)

    name = models.CharField(
        max_length=100,
        help_text='Descriptive name for this credential'
    )
    key = models.CharField(
        max_length=100,
        unique=True,
        help_text='API key (username for Basic Auth)'
    )
    secret_hash = models.CharField(
        max_length=128,
        help_text='Hashed API secret'
    )

    is_active = models.BooleanField(
        default=True,
        help_text='Whether this credential is active'
    )
    permissions = models.JSONField(
        default=list,
        help_text='Allowed permissions (read, write, delete)'
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_lrs_credentials',
        help_text='User who created this credential'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_used_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text='Last time this credential was used'
    )

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'LRS Credential'
        verbose_name_plural = 'LRS Credentials'

    def __str__(self):
        return f"{self.name} ({self.key})"

    def set_secret(self, secret: str):
        """Hash and store the secret."""
        self.secret_hash = self._hash_secret(secret)

    def check_secret(self, secret: str) -> bool:
        """Verify the secret against the stored hash."""
        return self.secret_hash == self._hash_secret(secret)

    @staticmethod
    def _hash_secret(secret: str) -> str:
        """Hash the secret using SHA-256."""
        return hashlib.sha256(secret.encode()).hexdigest()

    def has_permission(self, permission: str) -> bool:
        """Check if credential has the specified permission."""
        return permission in self.permissions

    def update_last_used(self):
        """Update the last_used_at timestamp."""
        self.last_used_at = timezone.now()
        self.save(update_fields=['last_used_at'])

    @classmethod
    def generate_credentials(cls, name: str, permissions: list = None, created_by=None):
        """Generate a new credential with random key and secret."""
        key = uuid.uuid4().hex[:20]
        secret = uuid.uuid4().hex

        credential = cls(
            name=name,
            key=key,
            permissions=permissions or ['read', 'write'],
            created_by=created_by,
        )
        credential.set_secret(secret)
        credential.save()

        # Return both credential and plain secret (only time secret is available)
        return credential, secret
