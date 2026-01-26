"""
LRS Dashboard Views

Admin Dashboard APIs for learning analytics and statistics.

All endpoints require staff/admin authentication (IsStaffRole).

Endpoints:
- GET /dashboard/overview - Basic statistics
- GET /dashboard/users - User-specific stats
- GET /dashboard/trends - Time-based trends
- GET /dashboard/realtime - Real-time activity
- GET /statements - Statement list with filtering
- CRUD /credentials - LRS Credential management
"""

import logging
from datetime import timedelta

from django.db.models import Count, Avg, Q, F
from django.db.models.functions import TruncDate, TruncWeek, TruncMonth
from django.utils import timezone
from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.pagination import PageNumberPagination

from accounts.models import User
from ..models import XAPIStatement, CMI5Session, LRSCredential
from ..serializers import (
    XAPIStatementSerializer,
    CMI5SessionSerializer,
    LRSCredentialSerializer,
    LRSCredentialCreateSerializer,
    DashboardOverviewSerializer,
    DashboardUserStatsSerializer,
    DashboardTrendSerializer,
)
from ..constants import XAPIVerb, QuizType
from ..elasticsearch import get_client, STATEMENT_INDEX, search_statements

logger = logging.getLogger(__name__)


class IsStaffOrAdmin(IsAuthenticated):
    """Permission class for staff/admin users."""

    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        return request.user.is_staff or request.user.is_superuser


class StatementPagination(PageNumberPagination):
    """Pagination for statement list."""
    page_size = 50
    page_size_query_param = 'page_size'
    max_page_size = 200


class DashboardOverviewView(APIView):
    """
    Dashboard overview with basic statistics.

    Returns:
    - total_users: Total registered users
    - active_users: Users with activity in last 30 days
    - total_quizzes: Total completed quizzes
    - completed_quizzes: Successfully completed quizzes
    - total_questions: Total questions answered
    - total_correct: Total correct answers
    - overall_accuracy: Overall accuracy percentage
    - pass_rate: Quiz pass rate percentage
    - quiz_type_breakdown: Stats by quiz type
    """

    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        """Get dashboard overview statistics."""
        now = timezone.now()
        thirty_days_ago = now - timedelta(days=30)

        # User statistics
        total_users = User.objects.count()
        active_users = XAPIStatement.objects.filter(
            timestamp__gte=thirty_days_ago
        ).values('actor_user').distinct().count()

        # Quiz statistics (from COMPLETED statements)
        completed_stmt = XAPIStatement.objects.filter(
            verb_id=XAPIVerb.COMPLETED
        )
        total_quizzes = completed_stmt.count()

        # Pass/fail statistics
        passed_count = XAPIStatement.objects.filter(
            verb_id=XAPIVerb.PASSED
        ).count()
        failed_count = XAPIStatement.objects.filter(
            verb_id=XAPIVerb.FAILED
        ).count()

        # Question statistics (from ANSWERED statements)
        answered_stmt = XAPIStatement.objects.filter(
            verb_id=XAPIVerb.ANSWERED
        )
        total_questions = answered_stmt.count()
        total_correct = answered_stmt.filter(result_success=True).count()

        # Calculate rates
        overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
        pass_rate = (passed_count / (passed_count + failed_count) * 100) if (passed_count + failed_count) > 0 else 0

        # Quiz type breakdown
        quiz_type_breakdown = {}
        for quiz_type in [QuizType.GANA_QUIZ, QuizType.WORD_QUIZ]:
            type_completed = completed_stmt.filter(
                object_id__icontains=quiz_type
            ).count()
            type_passed = XAPIStatement.objects.filter(
                verb_id=XAPIVerb.PASSED,
                object_id__icontains=quiz_type
            ).count()
            type_questions = answered_stmt.filter(
                object_id__icontains=quiz_type
            ).count()
            type_correct = answered_stmt.filter(
                object_id__icontains=quiz_type,
                result_success=True
            ).count()

            quiz_type_breakdown[quiz_type] = {
                'completed': type_completed,
                'passed': type_passed,
                'questions': type_questions,
                'correct': type_correct,
                'accuracy': (type_correct / type_questions * 100) if type_questions > 0 else 0,
            }

        data = {
            'total_users': total_users,
            'active_users': active_users,
            'total_quizzes': total_quizzes,
            'completed_quizzes': passed_count + failed_count,
            'total_questions': total_questions,
            'total_correct': total_correct,
            'overall_accuracy': round(overall_accuracy, 2),
            'pass_rate': round(pass_rate, 2),
            'quiz_type_breakdown': quiz_type_breakdown,
        }

        serializer = DashboardOverviewSerializer(data)
        return Response(serializer.data)


class DashboardUsersView(APIView):
    """
    User-specific statistics and rankings.

    Query parameters:
    - sort: Sort field (quizzes, accuracy, last_activity) default: quizzes
    - order: asc or desc (default: desc)
    - limit: Number of users (default: 20)
    """

    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        """Get per-user statistics."""
        sort_field = request.query_params.get('sort', 'quizzes')
        order = request.query_params.get('order', 'desc')
        limit = int(request.query_params.get('limit', 20))

        # Get users with quiz activity
        users_with_activity = XAPIStatement.objects.filter(
            verb_id=XAPIVerb.COMPLETED
        ).values('actor_user').annotate(
            total_quizzes=Count('id')
        ).values_list('actor_user', flat=True)

        user_stats = []
        for user_id in users_with_activity[:100]:  # Limit to 100 for performance
            try:
                user = User.objects.get(pk=user_id)
            except User.DoesNotExist:
                continue

            # Get user's answered statements
            user_answered = XAPIStatement.objects.filter(
                actor_user=user,
                verb_id=XAPIVerb.ANSWERED
            )
            total_questions = user_answered.count()
            total_correct = user_answered.filter(result_success=True).count()

            # Get user's completed quizzes
            total_quizzes = XAPIStatement.objects.filter(
                actor_user=user,
                verb_id=XAPIVerb.COMPLETED
            ).count()

            # Get last activity
            last_stmt = XAPIStatement.objects.filter(
                actor_user=user
            ).order_by('-timestamp').first()

            user_stats.append({
                'user_id': user.id,
                'email': user.email,
                'username': user.username or user.email,
                'total_quizzes': total_quizzes,
                'total_correct': total_correct,
                'total_questions': total_questions,
                'accuracy': round((total_correct / total_questions * 100), 2) if total_questions > 0 else 0,
                'last_activity': last_stmt.timestamp if last_stmt else None,
            })

        # Sort results
        sort_key = {
            'quizzes': 'total_quizzes',
            'accuracy': 'accuracy',
            'last_activity': 'last_activity',
            'questions': 'total_questions',
        }.get(sort_field, 'total_quizzes')

        reverse = order == 'desc'
        user_stats.sort(
            key=lambda x: (x[sort_key] is not None, x[sort_key]),
            reverse=reverse
        )

        serializer = DashboardUserStatsSerializer(user_stats[:limit], many=True)
        return Response(serializer.data)


class DashboardTrendsView(APIView):
    """
    Time-based learning trends.

    Query parameters:
    - period: day, week, or month (default: day)
    - days: Number of days to include (default: 30)
    """

    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        """Get time-based trends."""
        period = request.query_params.get('period', 'day')
        days = int(request.query_params.get('days', 30))

        start_date = timezone.now() - timedelta(days=days)

        # Select truncation function based on period
        if period == 'week':
            trunc_func = TruncWeek('timestamp')
        elif period == 'month':
            trunc_func = TruncMonth('timestamp')
        else:
            trunc_func = TruncDate('timestamp')

        # Get quiz completion trends
        completion_trends = XAPIStatement.objects.filter(
            verb_id=XAPIVerb.COMPLETED,
            timestamp__gte=start_date
        ).annotate(
            date=trunc_func
        ).values('date').annotate(
            quizzes_completed=Count('id')
        ).order_by('date')

        # Get question answer trends
        answer_trends = XAPIStatement.objects.filter(
            verb_id=XAPIVerb.ANSWERED,
            timestamp__gte=start_date
        ).annotate(
            date=trunc_func
        ).values('date').annotate(
            questions_answered=Count('id'),
            correct_answers=Count('id', filter=Q(result_success=True))
        ).order_by('date')

        # Get unique user trends
        user_trends = XAPIStatement.objects.filter(
            timestamp__gte=start_date
        ).annotate(
            date=trunc_func
        ).values('date').annotate(
            unique_users=Count('actor_user', distinct=True)
        ).order_by('date')

        # Merge trends data
        trends_dict = {}
        for item in completion_trends:
            date_key = item['date']
            if date_key not in trends_dict:
                trends_dict[date_key] = {
                    'date': date_key,
                    'quizzes_completed': 0,
                    'questions_answered': 0,
                    'correct_answers': 0,
                    'unique_users': 0,
                }
            trends_dict[date_key]['quizzes_completed'] = item['quizzes_completed']

        for item in answer_trends:
            date_key = item['date']
            if date_key not in trends_dict:
                trends_dict[date_key] = {
                    'date': date_key,
                    'quizzes_completed': 0,
                    'questions_answered': 0,
                    'correct_answers': 0,
                    'unique_users': 0,
                }
            trends_dict[date_key]['questions_answered'] = item['questions_answered']
            trends_dict[date_key]['correct_answers'] = item['correct_answers']

        for item in user_trends:
            date_key = item['date']
            if date_key in trends_dict:
                trends_dict[date_key]['unique_users'] = item['unique_users']

        # Sort by date
        trends = sorted(trends_dict.values(), key=lambda x: x['date'])

        serializer = DashboardTrendSerializer(trends, many=True)
        return Response(serializer.data)


class DashboardRealtimeView(APIView):
    """
    Real-time activity dashboard.

    Returns:
    - active_sessions: Currently active cmi5 sessions
    - recent_completions: Recently completed quizzes
    - recent_activity: Recent xAPI statements
    - stats_24h: Statistics for last 24 hours
    """

    permission_classes = [IsStaffOrAdmin]

    def get(self, request):
        """Get real-time activity data."""
        now = timezone.now()
        twenty_four_hours_ago = now - timedelta(hours=24)
        one_hour_ago = now - timedelta(hours=1)

        # Active cmi5 sessions
        active_sessions = CMI5Session.objects.filter(
            state__in=[
                CMI5Session.SessionState.LAUNCHED,
                CMI5Session.SessionState.INITIALIZED
            ],
            launched_at__gte=twenty_four_hours_ago
        ).count()

        # Recently completed quizzes (last hour)
        recent_completions = XAPIStatement.objects.filter(
            verb_id=XAPIVerb.COMPLETED,
            timestamp__gte=one_hour_ago
        ).select_related('actor_user').order_by('-timestamp')[:10]

        # Recent activity (last hour)
        recent_activity = XAPIStatement.objects.filter(
            timestamp__gte=one_hour_ago
        ).select_related('actor_user').order_by('-timestamp')[:20]

        # 24-hour statistics
        stats_24h = {
            'quizzes_started': XAPIStatement.objects.filter(
                verb_id=XAPIVerb.INITIALIZED,
                timestamp__gte=twenty_four_hours_ago
            ).count(),
            'quizzes_completed': XAPIStatement.objects.filter(
                verb_id=XAPIVerb.COMPLETED,
                timestamp__gte=twenty_four_hours_ago
            ).count(),
            'questions_answered': XAPIStatement.objects.filter(
                verb_id=XAPIVerb.ANSWERED,
                timestamp__gte=twenty_four_hours_ago
            ).count(),
            'unique_users': XAPIStatement.objects.filter(
                timestamp__gte=twenty_four_hours_ago
            ).values('actor_user').distinct().count(),
            'passed': XAPIStatement.objects.filter(
                verb_id=XAPIVerb.PASSED,
                timestamp__gte=twenty_four_hours_ago
            ).count(),
            'failed': XAPIStatement.objects.filter(
                verb_id=XAPIVerb.FAILED,
                timestamp__gte=twenty_four_hours_ago
            ).count(),
        }

        return Response({
            'active_sessions': active_sessions,
            'recent_completions': XAPIStatementSerializer(recent_completions, many=True).data,
            'recent_activity': XAPIStatementSerializer(recent_activity, many=True).data,
            'stats_24h': stats_24h,
        })


class StatementListView(APIView):
    """
    Statement list with filtering and pagination.

    Query parameters:
    - user_id: Filter by user
    - verb: Filter by verb ID
    - activity: Filter by object ID
    - since: Filter by timestamp (ISO format)
    - until: Filter by timestamp (ISO format)
    - page: Page number
    - page_size: Results per page (max 200)
    """

    permission_classes = [IsStaffOrAdmin]
    pagination_class = StatementPagination

    def get(self, request):
        """Get filtered statement list."""
        queryset = XAPIStatement.objects.all()

        # Apply filters
        user_id = request.query_params.get('user_id')
        if user_id:
            queryset = queryset.filter(actor_user_id=user_id)

        verb = request.query_params.get('verb')
        if verb:
            queryset = queryset.filter(verb_id=verb)

        activity = request.query_params.get('activity')
        if activity:
            queryset = queryset.filter(object_id__icontains=activity)

        since = request.query_params.get('since')
        if since:
            queryset = queryset.filter(timestamp__gte=since)

        until = request.query_params.get('until')
        if until:
            queryset = queryset.filter(timestamp__lte=until)

        # Order by timestamp descending
        queryset = queryset.order_by('-timestamp')

        # Paginate
        paginator = self.pagination_class()
        page = paginator.paginate_queryset(queryset, request)

        if page is not None:
            serializer = XAPIStatementSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)

        serializer = XAPIStatementSerializer(queryset[:100], many=True)
        return Response(serializer.data)


class LRSCredentialViewSet(viewsets.ModelViewSet):
    """
    LRS Credential management.

    Admin-only CRUD operations for managing LRS API credentials.
    """

    permission_classes = [IsAdminUser]
    serializer_class = LRSCredentialSerializer
    queryset = LRSCredential.objects.all()

    def get_serializer_class(self):
        if self.action == 'create':
            return LRSCredentialCreateSerializer
        return LRSCredentialSerializer

    def create(self, request, *args, **kwargs):
        """Create a new LRS credential."""
        serializer = LRSCredentialCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                serializer.errors,
                status=status.HTTP_400_BAD_REQUEST
            )

        name = serializer.validated_data['name']
        permissions = serializer.validated_data.get('permissions', ['read', 'write'])

        # Generate credential
        credential, secret = LRSCredential.generate_credentials(
            name=name,
            permissions=permissions,
            created_by=request.user,
        )

        # Return credential with plain secret (only time it's available)
        return Response({
            'id': str(credential.id),
            'name': credential.name,
            'key': credential.key,
            'secret': secret,  # Only returned on creation!
            'permissions': credential.permissions,
            'created_at': credential.created_at,
            'message': 'Save the secret now - it cannot be retrieved later!',
        }, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """Deactivate a credential instead of deleting."""
        instance = self.get_object()
        instance.is_active = False
        instance.save(update_fields=['is_active'])
        return Response(status=status.HTTP_204_NO_CONTENT)
