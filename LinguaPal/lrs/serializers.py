"""
LRS Serializers

Serializers for xAPI statements, cmi5 sessions, and dashboard data.
"""

from rest_framework import serializers

from .models import XAPIStatement, CMI5Session, LRSCredential


class XAPIStatementSerializer(serializers.ModelSerializer):
    """Serializer for xAPI Statement model."""

    actor = serializers.SerializerMethodField()
    verb = serializers.SerializerMethodField()
    object = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()
    context = serializers.SerializerMethodField()

    class Meta:
        model = XAPIStatement
        fields = [
            'id', 'actor', 'verb', 'object', 'result', 'context',
            'timestamp', 'stored'
        ]

    def get_actor(self, obj):
        return {
            'objectType': 'Agent',
            'mbox': f'mailto:{obj.actor_mbox}',
            'name': obj.actor_name,
        }

    def get_verb(self, obj):
        return {
            'id': obj.verb_id,
            'display': {'en-US': obj.verb_display}
        }

    def get_object(self, obj):
        return {
            'objectType': obj.object_type,
            'id': obj.object_id,
            'definition': obj.object_definition
        }

    def get_result(self, obj):
        result = {}
        if obj.result_success is not None:
            result['success'] = obj.result_success
        if obj.result_response:
            result['response'] = obj.result_response
        if obj.result_completion is not None:
            result['completion'] = obj.result_completion

        if obj.result_score_scaled is not None:
            result['score'] = {'scaled': obj.result_score_scaled}
            if obj.result_score_raw is not None:
                result['score']['raw'] = obj.result_score_raw
            if obj.result_score_min is not None:
                result['score']['min'] = obj.result_score_min
            if obj.result_score_max is not None:
                result['score']['max'] = obj.result_score_max

        return result if result else None

    def get_context(self, obj):
        context = {}
        if obj.context_registration:
            context['registration'] = str(obj.context_registration)
        if obj.context_extensions:
            context['extensions'] = obj.context_extensions
        return context if context else None


class XAPIStatementInputSerializer(serializers.Serializer):
    """Serializer for incoming xAPI statements (POST)."""

    id = serializers.UUIDField(required=False)
    actor = serializers.DictField(required=True)
    verb = serializers.DictField(required=True)
    object = serializers.DictField(required=True)
    result = serializers.DictField(required=False)
    context = serializers.DictField(required=False)
    timestamp = serializers.DateTimeField(required=False)

    def validate_actor(self, value):
        """Validate actor field."""
        if 'mbox' not in value and 'account' not in value:
            raise serializers.ValidationError("Actor must have mbox or account")
        return value

    def validate_verb(self, value):
        """Validate verb field."""
        if 'id' not in value:
            raise serializers.ValidationError("Verb must have id")
        return value

    def validate_object(self, value):
        """Validate object field."""
        if 'id' not in value:
            raise serializers.ValidationError("Object must have id")
        return value


class CMI5SessionSerializer(serializers.ModelSerializer):
    """Serializer for cmi5 Session model."""

    actor_email = serializers.EmailField(source='actor_user.email', read_only=True)
    actor_name = serializers.CharField(source='actor_user.username', read_only=True)

    class Meta:
        model = CMI5Session
        fields = [
            'id', 'registration', 'actor_email', 'actor_name',
            'au_id', 'au_type', 'au_object_id', 'state',
            'mastery_score', 'launch_mode', 'move_on',
            'launched_at', 'initialized_at', 'terminated_at',
            'is_passed', 'is_completed', 'score_scaled'
        ]
        read_only_fields = ['id', 'registration', 'launched_at']


class LRSCredentialSerializer(serializers.ModelSerializer):
    """Serializer for LRS Credential model."""

    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)

    class Meta:
        model = LRSCredential
        fields = [
            'id', 'name', 'key', 'is_active', 'permissions',
            'created_by_email', 'created_at', 'last_used_at'
        ]
        read_only_fields = ['id', 'key', 'created_at', 'last_used_at']


class LRSCredentialCreateSerializer(serializers.Serializer):
    """Serializer for creating LRS credentials."""

    name = serializers.CharField(max_length=100)
    permissions = serializers.ListField(
        child=serializers.ChoiceField(choices=['read', 'write', 'delete']),
        default=['read', 'write']
    )


# Dashboard Serializers

class DashboardOverviewSerializer(serializers.Serializer):
    """Serializer for dashboard overview data."""

    total_users = serializers.IntegerField()
    active_users = serializers.IntegerField()
    total_quizzes = serializers.IntegerField()
    completed_quizzes = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    total_correct = serializers.IntegerField()
    overall_accuracy = serializers.FloatField()
    pass_rate = serializers.FloatField()
    quiz_type_breakdown = serializers.DictField()
    activity_breakdown = serializers.ListField(required=False, default=list)
    source = serializers.CharField(required=False, default='database')


class DashboardUserStatsSerializer(serializers.Serializer):
    """Serializer for per-user dashboard stats."""

    user_id = serializers.IntegerField()
    email = serializers.EmailField()
    username = serializers.CharField()
    total_quizzes = serializers.IntegerField()
    total_correct = serializers.IntegerField()
    total_questions = serializers.IntegerField()
    accuracy = serializers.FloatField()
    last_activity = serializers.DateTimeField()


class DashboardTrendSerializer(serializers.Serializer):
    """Serializer for trend data."""

    date = serializers.DateField()
    quizzes_completed = serializers.IntegerField()
    questions_answered = serializers.IntegerField()
    correct_answers = serializers.IntegerField()
    unique_users = serializers.IntegerField()


class StatementQuerySerializer(serializers.Serializer):
    """Serializer for statement query parameters."""

    statementId = serializers.UUIDField(required=False)
    agent = serializers.CharField(required=False)
    verb = serializers.URLField(required=False)
    activity = serializers.URLField(required=False)
    registration = serializers.UUIDField(required=False)
    since = serializers.DateTimeField(required=False)
    until = serializers.DateTimeField(required=False)
    limit = serializers.IntegerField(required=False, default=100, max_value=1000)
    ascending = serializers.BooleanField(required=False, default=False)


class LRSAboutSerializer(serializers.Serializer):
    """Serializer for LRS About resource."""

    version = serializers.ListField(child=serializers.CharField())
    extensions = serializers.DictField(required=False)
