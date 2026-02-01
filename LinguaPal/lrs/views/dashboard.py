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
from ..permissions import HasAPIKey
from ..serializers import (
    XAPIStatementSerializer,
    CMI5SessionSerializer,
    LRSCredentialSerializer,
    LRSCredentialCreateSerializer,
    DashboardOverviewSerializer,
    DashboardUserStatsSerializer,
    DashboardTrendSerializer,
)
from ..constants import XAPIVerb, QuizType, get_activity_name
from ..elasticsearch import (
    get_client, STATEMENT_INDEX, ACTIVITY_INDEX,
    search_statements, search_activities, aggregate_stats
)

logger = logging.getLogger(__name__)

# Language code to name mapping (cached)
_language_cache = {}


def _get_language_name(code: str) -> str:
    """Get language name (Korean) for a language code."""
    global _language_cache
    if not _language_cache:
        try:
            from words.models import Language
            _language_cache = {
                lang.code: lang.name_ko
                for lang in Language.objects.all()
            }
        except Exception:
            pass
    return _language_cache.get(code, code)


def _get_display_name(category: str, subcategory: str, quiz_type: str = None) -> str:
    """Get human-readable display name for an activity."""
    if category == 'gana':
        char_name = {'hiragana': '히라가나', 'katakana': '가타카나', 'all': '전체 가나'}.get(subcategory, subcategory)
        if quiz_type:
            quiz_name = {
                'gana_to_romaji': '→ 로마자',
                'romaji_to_gana_select': '← 로마자 (선택)',
                'romaji_to_gana_input': '← 로마자 (입력)',
            }.get(quiz_type, quiz_type)
            return f"{char_name} {quiz_name}"
        return f"{char_name} 퀴즈"
    elif category == 'word':
        lang_name = _get_language_name(subcategory)
        if quiz_type:
            quiz_name = {
                'word_to_native': '외국어 → 모국어',
                'native_to_word_select': '모국어 → 외국어 (선택)',
                'native_to_word_input': '모국어 → 외국어 (입력)',
            }.get(quiz_type, quiz_type)
            return f"{lang_name} 단어 퀴즈 ({quiz_name})"
        return f"{lang_name} 단어 퀴즈"
    elif category == 'flashcard':
        # 플래시카드: subcategory는 이미 표시명 (일본어, 히라가나 등)
        # quiz_type은 "일반 학습"
        if quiz_type:
            return f"{subcategory} {quiz_type}"
        return f"{subcategory} 플래시카드"
    return f"{category}/{subcategory}"


def _get_user_display_name(user) -> str:
    """Get display name for a user (profile nickname or username)."""
    if hasattr(user, 'profile') and user.profile and user.profile.nickname:
        return user.profile.nickname
    return user.username or user.email


def _es_available():
    """Check if Elasticsearch is available."""
    client = get_client()
    return client is not None


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

    Uses Elasticsearch for aggregations when available, falls back to DB.

    Returns:
    - total_users: Total registered users
    - active_users: Users with activity in last 30 days
    - total_quizzes: Total completed quizzes
    - completed_quizzes: Successfully completed quizzes
    - total_questions: Total questions answered
    - total_correct: Total correct answers
    - overall_accuracy: Overall accuracy percentage
    - pass_rate: Quiz pass rate percentage
    - quiz_type_breakdown: Stats by quiz type (gana/word)
    - activity_breakdown: Stats by activity (language/character_set)
    """

    permission_classes = [IsStaffOrAdmin, HasAPIKey]

    def get(self, request):
        """Get dashboard overview statistics using ES aggregations."""
        if _es_available():
            return self._get_from_es(request)
        return self._get_from_db(request)

    def _get_from_es(self, request):
        """Get statistics from Elasticsearch."""
        client = get_client()
        now = timezone.now()
        thirty_days_ago = (now - timedelta(days=30)).isoformat()

        # Total users (still from DB as it's authoritative)
        total_users = User.objects.count()

        # Build ES aggregation query
        aggs = {
            # Active users in last 30 days
            'active_users': {
                'filter': {'range': {'timestamp': {'gte': thirty_days_ago}}},
                'aggs': {
                    'unique_users': {'cardinality': {'field': 'actor.user_id'}}
                }
            },
            # Verb counts
            'by_verb': {
                'terms': {'field': 'verb.id', 'size': 10}
            },
            # Questions answered
            'answered_stats': {
                'filter': {'term': {'verb.id': XAPIVerb.ANSWERED}},
                'aggs': {
                    'total': {'value_count': {'field': 'id'}},
                    'correct': {
                        'filter': {'term': {'result.success': True}}
                    }
                }
            },
            # Category breakdown (gana vs word)
            'by_category': {
                'terms': {'field': 'activity.category', 'size': 10},
                'aggs': {
                    'completed': {
                        'filter': {'term': {'verb.id': XAPIVerb.COMPLETED}}
                    },
                    'passed': {
                        'filter': {'term': {'verb.id': XAPIVerb.PASSED}}
                    },
                    'answered': {
                        'filter': {'term': {'verb.id': XAPIVerb.ANSWERED}},
                        'aggs': {
                            'correct': {
                                'filter': {'term': {'result.success': True}}
                            }
                        }
                    }
                }
            },
            # Subcategory breakdown (language_code or character_set)
            'by_subcategory': {
                'terms': {'field': 'activity.subcategory', 'size': 20},
                'aggs': {
                    'category': {
                        'terms': {'field': 'activity.category', 'size': 1}
                    },
                    'quiz_types': {
                        'terms': {'field': 'activity.quiz_type', 'size': 10},
                        'aggs': {
                            'completed': {
                                'filter': {'term': {'verb.id': XAPIVerb.COMPLETED}}
                            },
                            'passed': {
                                'filter': {'term': {'verb.id': XAPIVerb.PASSED}}
                            },
                            'failed': {
                                'filter': {'term': {'verb.id': XAPIVerb.FAILED}}
                            },
                            'answered': {
                                'filter': {'term': {'verb.id': XAPIVerb.ANSWERED}},
                                'aggs': {
                                    'correct': {
                                        'filter': {'term': {'result.success': True}}
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }

        try:
            result = client.search(
                index=STATEMENT_INDEX,
                body={'size': 0, 'aggs': aggs}
            )
            agg_result = result.get('aggregations', {})
        except Exception as e:
            logger.error(f"ES aggregation error: {e}")
            return self._get_from_db(request)

        # Extract data from aggregations
        active_users = agg_result.get('active_users', {}).get('unique_users', {}).get('value', 0)

        # Verb counts
        verb_counts = {}
        for bucket in agg_result.get('by_verb', {}).get('buckets', []):
            verb_counts[bucket['key']] = bucket['doc_count']

        total_quizzes = verb_counts.get(XAPIVerb.COMPLETED, 0)
        passed_count = verb_counts.get(XAPIVerb.PASSED, 0)
        failed_count = verb_counts.get(XAPIVerb.FAILED, 0)

        # Questions stats
        answered_stats = agg_result.get('answered_stats', {})
        total_questions = answered_stats.get('total', {}).get('value', 0)
        total_correct = answered_stats.get('correct', {}).get('doc_count', 0)

        # Calculate rates
        overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
        pass_rate = (passed_count / (passed_count + failed_count) * 100) if (passed_count + failed_count) > 0 else 0

        # Category breakdown (gana/word)
        category_breakdown = {}
        category_display = {'gana': '가나 퀴즈', 'word': '단어 퀴즈'}
        for bucket in agg_result.get('by_category', {}).get('buckets', []):
            category = bucket['key']
            cat_answered = bucket.get('answered', {}).get('doc_count', 0)
            cat_correct = bucket.get('answered', {}).get('correct', {}).get('doc_count', 0)
            category_breakdown[category] = {
                'display_name': category_display.get(category, category),
                'completed': bucket.get('completed', {}).get('doc_count', 0),
                'passed': bucket.get('passed', {}).get('doc_count', 0),
                'questions': cat_answered,
                'correct': cat_correct,
                'accuracy': round((cat_correct / cat_answered * 100), 2) if cat_answered > 0 else 0,
            }

        # Activity breakdown (by subcategory AND quiz_type)
        activity_breakdown = []
        for bucket in agg_result.get('by_subcategory', {}).get('buckets', []):
            subcategory = bucket['key']
            cat_buckets = bucket.get('category', {}).get('buckets', [])
            category = cat_buckets[0]['key'] if cat_buckets else 'unknown'

            # Iterate over quiz types within this subcategory
            quiz_type_buckets = bucket.get('quiz_types', {}).get('buckets', [])
            
            if not quiz_type_buckets:
                # Fallback if no quiz_type aggregation found (legacy data?)
                continue

            for qt_bucket in quiz_type_buckets:
                quiz_type = qt_bucket['key']
                
                act_answered = qt_bucket.get('answered', {}).get('doc_count', 0)
                act_correct = qt_bucket.get('answered', {}).get('correct', {}).get('doc_count', 0)
                
                activity_breakdown.append({
                    'category': category,
                    'subcategory': subcategory,
                    'quiz_type': quiz_type,
                    'display_name': _get_display_name(category, subcategory, quiz_type),
                    'completed': qt_bucket.get('completed', {}).get('doc_count', 0),
                    'passed': qt_bucket.get('passed', {}).get('doc_count', 0),
                    'failed': qt_bucket.get('failed', {}).get('doc_count', 0),
                    'questions': act_answered,
                    'correct': act_correct,
                    'accuracy': round((act_correct / act_answered * 100), 2) if act_answered > 0 else 0,
                })

        data = {
            'total_users': total_users,
            'active_users': active_users,
            'total_quizzes': total_quizzes,
            'completed_quizzes': passed_count + failed_count,
            'total_questions': total_questions,
            'total_correct': total_correct,
            'overall_accuracy': round(overall_accuracy, 2),
            'pass_rate': round(pass_rate, 2),
            'quiz_type_breakdown': category_breakdown,
            'activity_breakdown': activity_breakdown,
            'source': 'elasticsearch',
        }

        serializer = DashboardOverviewSerializer(data)
        return Response(serializer.data)

    def _get_from_db(self, request):
        """Fallback: Get statistics from database."""
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

        # Activity breakdown (DB) 
        # Note: This is less efficient than ES and approximates groupings
        activity_breakdown = []
        
        # We'll use a simplified approach for DB: 
        # Group by context_extensions__subcategory and context_extensions__quiz_type
        # Only supported if JSONField querying is available (Postgres/SQLite)
        try:
            db_breakdown = completed_stmt.values(
                'context_extensions__category',
                'context_extensions__subcategory',
                'context_extensions__quiz_type'
            ).annotate(
                completed=Count('id'),
                passed=Count('id', filter=Q(verb_id=XAPIVerb.PASSED)),
                failed=Count('id', filter=Q(verb_id=XAPIVerb.FAILED))
            )
            
            # For questions stats, we need a separate query and manual merge
            # or subqueries. For performance, we'll do a separate query and merge in python.
            answered_breakdown = answered_stmt.values(
                'context_extensions__subcategory', 
                'context_extensions__quiz_type'
            ).annotate(
                questions=Count('id'),
                correct=Count('id', filter=Q(result_success=True))
            )
            
            # Convert answered stats to dict for lookup
            answered_map = {}
            for item in answered_breakdown:
                key = (item['context_extensions__subcategory'], item['context_extensions__quiz_type'])
                answered_map[key] = item

            for item in db_breakdown:
                cat = item.get('context_extensions__category')
                sub = item.get('context_extensions__subcategory')
                qt = item.get('context_extensions__quiz_type')
                
                if not (cat and sub and qt): 
                    continue
                    
                q_stats = answered_map.get((sub, qt), {'questions': 0, 'correct': 0})
                
                questions = q_stats['questions']
                correct = q_stats['correct']
                
                activity_breakdown.append({
                    'category': cat,
                    'subcategory': sub,
                    'quiz_type': qt,
                    'display_name': _get_display_name(cat, sub, qt),
                    'completed': item['completed'],
                    'passed': item['passed'],
                    'failed': item['failed'],
                    'questions': questions,
                    'correct': correct,
                    'accuracy': round((correct / questions * 100), 2) if questions > 0 else 0,
                })
                
        except Exception as e:
            logger.warning(f"DB activity breakdown failed (likely unsupported JSON lookup): {e}")
            activity_breakdown = []

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
            'activity_breakdown': activity_breakdown,
            'source': 'database',
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

    permission_classes = [IsStaffOrAdmin, HasAPIKey]

    def get(self, request):
        """Get per-user statistics."""
        sort_field = request.query_params.get('sort', 'quizzes')
        order = request.query_params.get('order', 'desc')
        try:
            limit = int(request.query_params.get('limit', 20))
        except (ValueError, TypeError):
            limit = 20

        # Get users with quiz activity
        users_with_activity = XAPIStatement.objects.filter(
            verb_id=XAPIVerb.COMPLETED
        ).values('actor_user').annotate(
            total_quizzes=Count('id')
        ).values_list('actor_user', flat=True)

        user_stats = []
        for user_id in users_with_activity[:100]:  # Limit to 100 for performance
            try:
                user = User.objects.select_related('profile').get(pk=user_id)
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

            # Get user's passed quizzes
            passed_quizzes = XAPIStatement.objects.filter(
                actor_user=user,
                verb_id=XAPIVerb.PASSED
            ).count()

            # Get last activity
            last_stmt = XAPIStatement.objects.filter(
                actor_user=user
            ).order_by('-timestamp').first()

            user_stats.append({
                'user_id': user.id,
                'email': user.email,
                'username': _get_user_display_name(user),
                'total_quizzes': total_quizzes,
                'passed_quizzes': passed_quizzes,
                'total_correct': total_correct,
                'total_questions': total_questions,
                'correct_answers': total_correct,
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

    Uses Elasticsearch date_histogram for efficient aggregations.

    Query parameters:
    - period: day, week, or month (default: day)
    - days: Number of days to include (default: 30)
    - category: Filter by category (gana, word)
    - subcategory: Filter by language_code or character_set
    """

    permission_classes = [IsStaffOrAdmin, HasAPIKey]

    def get(self, request):
        """Get time-based trends."""
        if _es_available():
            return self._get_from_es(request)
        return self._get_from_db(request)

    def _get_from_es(self, request):
        """Get trends from Elasticsearch using date_histogram."""
        client = get_client()
        period = request.query_params.get('period', 'day')
        try:
            days = int(request.query_params.get('days', 30))
        except (ValueError, TypeError):
            days = 30
        category = request.query_params.get('category')
        subcategory = request.query_params.get('subcategory')

        start_date = (timezone.now() - timedelta(days=days)).isoformat()

        # Map period to ES calendar_interval
        interval_map = {
            'day': 'day',
            'week': 'week',
            'month': 'month',
        }
        interval = interval_map.get(period, 'day')

        # Build filter
        must_filters = [{'range': {'timestamp': {'gte': start_date}}}]
        if category:
            must_filters.append({'term': {'activity.category': category}})
        if subcategory:
            must_filters.append({'term': {'activity.subcategory': subcategory}})

        # Build aggregation query
        aggs = {
            'trends': {
                'date_histogram': {
                    'field': 'timestamp',
                    'calendar_interval': interval,
                    'format': 'yyyy-MM-dd',
                    'min_doc_count': 0,
                },
                'aggs': {
                    'quizzes_completed': {
                        'filter': {'term': {'verb.id': XAPIVerb.COMPLETED}}
                    },
                    'quizzes_passed': {
                        'filter': {'term': {'verb.id': XAPIVerb.PASSED}}
                    },
                    'quizzes_failed': {
                        'filter': {'term': {'verb.id': XAPIVerb.FAILED}}
                    },
                    'questions_answered': {
                        'filter': {'term': {'verb.id': XAPIVerb.ANSWERED}},
                        'aggs': {
                            'correct': {
                                'filter': {'term': {'result.success': True}}
                            }
                        }
                    },
                    'unique_users': {
                        'cardinality': {'field': 'actor.user_id'}
                    },
                    'by_category': {
                        'terms': {'field': 'activity.category', 'size': 10},
                        'aggs': {
                            'completed': {
                                'filter': {'term': {'verb.id': XAPIVerb.COMPLETED}}
                            }
                        }
                    }
                }
            }
        }

        try:
            result = client.search(
                index=STATEMENT_INDEX,
                body={
                    'size': 0,
                    'query': {'bool': {'must': must_filters}},
                    'aggs': aggs
                }
            )
        except Exception as e:
            logger.error(f"ES trends error: {e}")
            return self._get_from_db(request)

        # Extract trends data
        trends = []
        for bucket in result.get('aggregations', {}).get('trends', {}).get('buckets', []):
            answered_data = bucket.get('questions_answered', {})
            answered_count = answered_data.get('doc_count', 0)
            correct_count = answered_data.get('correct', {}).get('doc_count', 0)

            # Category breakdown for this period
            category_data = {}
            for cat_bucket in bucket.get('by_category', {}).get('buckets', []):
                category_data[cat_bucket['key']] = {
                    'completed': cat_bucket.get('completed', {}).get('doc_count', 0)
                }

            trends.append({
                'date': bucket['key_as_string'],
                'quizzes_completed': bucket.get('quizzes_completed', {}).get('doc_count', 0),
                'quizzes_passed': bucket.get('quizzes_passed', {}).get('doc_count', 0),
                'quizzes_failed': bucket.get('quizzes_failed', {}).get('doc_count', 0),
                'questions_answered': answered_count,
                'correct_answers': correct_count,
                'accuracy': round((correct_count / answered_count * 100), 2) if answered_count > 0 else 0,
                'unique_users': bucket.get('unique_users', {}).get('value', 0),
                'by_category': category_data,
            })

        return Response({
            'period': period,
            'days': days,
            'trends': trends,
            'source': 'elasticsearch',
        })

    def _get_from_db(self, request):
        """Fallback: Get trends from database."""
        period = request.query_params.get('period', 'day')
        try:
            days = int(request.query_params.get('days', 30))
        except (ValueError, TypeError):
            days = 30

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

        return Response({
            'period': period,
            'days': days,
            'trends': trends,
            'source': 'database',
        })


class DashboardRealtimeView(APIView):
    """
    Real-time activity dashboard.

    Uses Elasticsearch for fast queries.

    Returns:
    - active_sessions: Currently active cmi5 sessions
    - recent_completions: Recently completed quizzes
    - recent_activity: Recent xAPI statements
    - stats_24h: Statistics for last 24 hours
    """

    permission_classes = [IsStaffOrAdmin, HasAPIKey]

    def get(self, request):
        """Get real-time activity data."""
        if _es_available():
            return self._get_from_es(request)
        return self._get_from_db(request)

    def _get_from_es(self, request):
        """Get realtime data from Elasticsearch."""
        client = get_client()
        now = timezone.now()
        twenty_four_hours_ago = (now - timedelta(hours=24)).isoformat()
        one_hour_ago = (now - timedelta(hours=1)).isoformat()

        # Active sessions (still from DB as they're managed there)
        active_sessions = CMI5Session.objects.filter(
            state__in=[
                CMI5Session.SessionState.LAUNCHED,
                CMI5Session.SessionState.INITIALIZED
            ],
            launched_at__gte=now - timedelta(hours=24)
        ).count()

        # ES query for 24h stats
        try:
            stats_result = client.search(
                index=STATEMENT_INDEX,
                body={
                    'size': 0,
                    'query': {
                        'range': {'timestamp': {'gte': twenty_four_hours_ago}}
                    },
                    'aggs': {
                        'by_verb': {
                            'terms': {'field': 'verb.id', 'size': 10}
                        },
                        'unique_users': {
                            'cardinality': {'field': 'actor.user_id'}
                        },
                        'by_category': {
                            'terms': {'field': 'activity.category', 'size': 10},
                            'aggs': {
                                'completed': {
                                    'filter': {'term': {'verb.id': XAPIVerb.COMPLETED}}
                                }
                            }
                        }
                    }
                }
            )

            # Extract 24h stats
            verb_counts = {}
            for bucket in stats_result['aggregations']['by_verb']['buckets']:
                verb_counts[bucket['key']] = bucket['doc_count']

            category_stats = {}
            for bucket in stats_result['aggregations']['by_category']['buckets']:
                category_stats[bucket['key']] = {
                    'completed': bucket['completed']['doc_count']
                }

            stats_24h = {
                'quizzes_started': verb_counts.get(XAPIVerb.INITIALIZED, 0),
                'quizzes_completed': verb_counts.get(XAPIVerb.COMPLETED, 0),
                'questions_answered': verb_counts.get(XAPIVerb.ANSWERED, 0),
                'unique_users': stats_result['aggregations']['unique_users']['value'],
                'passed': verb_counts.get(XAPIVerb.PASSED, 0),
                'failed': verb_counts.get(XAPIVerb.FAILED, 0),
                'by_category': category_stats,
            }

            # Recent completions
            completions_result = client.search(
                index=STATEMENT_INDEX,
                body={
                    'size': 10,
                    'query': {
                        'bool': {
                            'must': [
                                {'term': {'verb.id': XAPIVerb.COMPLETED}},
                                {'range': {'timestamp': {'gte': one_hour_ago}}}
                            ]
                        }
                    },
                    'sort': [{'timestamp': 'desc'}]
                }
            )
            recent_completions_raw = [hit['_source'] for hit in completions_result['hits']['hits']]

            # Recent activity
            activity_result = client.search(
                index=STATEMENT_INDEX,
                body={
                    'size': 20,
                    'query': {
                        'range': {'timestamp': {'gte': one_hour_ago}}
                    },
                    'sort': [{'timestamp': 'desc'}]
                }
            )
            recent_activity_raw = [hit['_source'] for hit in activity_result['hits']['hits']]

            # Enrich with user display names and activity display names
            all_items = recent_completions_raw + recent_activity_raw
            user_ids = set()
            for item in all_items:
                actor = item.get('actor', {})
                if actor.get('user_id'):
                    user_ids.add(actor['user_id'])

            # Fetch user display names from DB
            user_display_names = {}
            if user_ids:
                users = User.objects.select_related('profile').filter(id__in=user_ids)
                for user in users:
                    user_display_names[user.id] = _get_user_display_name(user)

            def enrich_item(item):
                """Add display names to an activity item."""
                enriched = item.copy()
                actor = enriched.get('actor', {})
                user_id = actor.get('user_id')
                if user_id and user_id in user_display_names:
                    enriched['actor']['display_name'] = user_display_names[user_id]
                else:
                    enriched['actor']['display_name'] = actor.get('name', 'Unknown')

                # Add activity display name
                activity = enriched.get('activity', {})
                category = activity.get('category', '')
                subcategory = activity.get('subcategory', '')
                quiz_type = activity.get('quiz_type', '')
                if category:
                    enriched['activity']['display_name'] = _get_display_name(category, subcategory, quiz_type)

                return enriched

            recent_completions = [enrich_item(item) for item in recent_completions_raw]
            recent_activity = [enrich_item(item) for item in recent_activity_raw]

        except Exception as e:
            logger.error(f"ES realtime error: {e}")
            return self._get_from_db(request)

        return Response({
            'active_sessions': active_sessions,
            'recent_completions': recent_completions,
            'recent_activity': recent_activity,
            'stats_24h': stats_24h,
            'source': 'elasticsearch',
        })

    def _get_from_db(self, request):
        """Fallback: Get realtime data from database."""
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
        recent_completions_qs = XAPIStatement.objects.filter(
            verb_id=XAPIVerb.COMPLETED,
            timestamp__gte=one_hour_ago
        ).select_related('actor_user', 'actor_user__profile').order_by('-timestamp')[:10]

        # Recent activity (last hour)
        recent_activity_qs = XAPIStatement.objects.filter(
            timestamp__gte=one_hour_ago
        ).select_related('actor_user', 'actor_user__profile').order_by('-timestamp')[:20]

        # Serialize with display names
        def serialize_with_display_name(statements):
            """Serialize statements with user display names and activity display names."""
            result = []
            for stmt in statements:
                data = XAPIStatementSerializer(stmt).data
                # Add user display name
                if stmt.actor_user:
                    data['actor_display_name'] = _get_user_display_name(stmt.actor_user)
                else:
                    data['actor_display_name'] = stmt.actor_name

                # Parse activity info from object_id for display name
                from ..services import ActivityID
                activity_info = ActivityID.parse(stmt.object_id)
                if activity_info.get('category'):
                    data['activity_display_name'] = _get_display_name(
                        activity_info.get('category', ''),
                        activity_info.get('subcategory', ''),
                        activity_info.get('quiz_type', '')
                    )
                result.append(data)
            return result

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
            'recent_completions': serialize_with_display_name(recent_completions_qs),
            'recent_activity': serialize_with_display_name(recent_activity_qs),
            'stats_24h': stats_24h,
            'source': 'database',
        })


class ActivityListView(APIView):
    """
    List all activities with their statistics.

    Query parameters:
    - category: Filter by category (gana, word)
    - subcategory: Filter by language_code or character_set
    - sort: Sort field (attempts, completions, passes, avg_score)
    - order: asc or desc (default: desc)
    - limit: Number of results (default: 50)
    """

    permission_classes = [IsStaffOrAdmin, HasAPIKey]

    def get(self, request):
        """Get activity list with statistics from ES."""
        if not _es_available():
            return Response({
                'error': 'Elasticsearch not available',
                'activities': []
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        client = get_client()
        category = request.query_params.get('category')
        subcategory = request.query_params.get('subcategory')
        sort_field = request.query_params.get('sort', 'stats.total_attempts')
        order = request.query_params.get('order', 'desc')
        limit = int(request.query_params.get('limit', 50))

        # Build filter
        must_filters = []
        if category:
            must_filters.append({'term': {'category': category}})
        if subcategory:
            must_filters.append({'term': {'subcategory': subcategory}})

        query = {'bool': {'must': must_filters}} if must_filters else {'match_all': {}}

        # Sort field mapping
        sort_mapping = {
            'attempts': 'stats.total_attempts',
            'completions': 'stats.total_completions',
            'passes': 'stats.total_passes',
            'avg_score': 'stats.avg_score',
            'users': 'stats.unique_users',
        }
        es_sort = sort_mapping.get(sort_field, sort_field)

        try:
            result = client.search(
                index=ACTIVITY_INDEX,
                body={
                    'size': limit,
                    'query': query,
                    'sort': [{es_sort: order}]
                }
            )

            activities = [hit['_source'] for hit in result['hits']['hits']]

            return Response({
                'total': result['hits']['total']['value'],
                'activities': activities,
                'source': 'elasticsearch',
            })

        except Exception as e:
            logger.error(f"Activity list error: {e}")
            return Response({
                'error': str(e),
                'activities': []
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


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

    permission_classes = [IsStaffOrAdmin, HasAPIKey]
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


class DifficultyAnalysisView(APIView):
    """
    Difficulty analysis - hardest and easiest items.

    Returns:
    - hardest_items: Top 10 items with lowest accuracy
    - easiest_items: Top 10 items with highest accuracy
    - wrong_answer_patterns: Common mistake patterns
    """

    permission_classes = [IsStaffOrAdmin, HasAPIKey]

    def get(self, request):
        category = request.query_params.get('category')  # gana or word
        limit = int(request.query_params.get('limit', 10))

        if _es_available():
            return self._get_from_es(request, category, limit)
        return self._get_from_db(request, category, limit)

    def _get_from_es(self, request, category, limit):
        """Get difficulty analysis from Elasticsearch."""
        client = get_client()

        # Build filter
        must_filters = [{'term': {'verb.id': XAPIVerb.ANSWERED}}]
        if category:
            must_filters.append({'term': {'activity.category': category}})

        # Aggregate by question (object.id) to find hardest/easiest
        aggs = {
            'by_question': {
                'terms': {
                    'field': 'object.id',
                    'size': 1000,  # Get many to sort
                },
                'aggs': {
                    'total': {'value_count': {'field': 'id'}},
                    'correct': {
                        'filter': {'term': {'result.success': True}}
                    },
                    'incorrect': {
                        'filter': {'term': {'result.success': False}}
                    },
                    'accuracy': {
                        'bucket_script': {
                            'buckets_path': {
                                'correct': 'correct._count',
                                'total': '_count'
                            },
                            'script': 'params.total > 0 ? (params.correct / params.total) * 100 : 0'
                        }
                    },
                    'category': {
                        'terms': {'field': 'activity.category', 'size': 1}
                    },
                    'subcategory': {
                        'terms': {'field': 'activity.subcategory', 'size': 1}
                    }
                }
            },
            # Wrong answer patterns
            'wrong_patterns': {
                'filter': {'term': {'result.success': False}},
                'aggs': {
                    'by_response': {
                        'terms': {'field': 'result.response', 'size': 20}
                    }
                }
            }
        }

        try:
            result = client.search(
                index=STATEMENT_INDEX,
                body={
                    'size': 0,
                    'query': {'bool': {'must': must_filters}},
                    'aggs': aggs
                }
            )
        except Exception as e:
            logger.error(f"ES difficulty analysis error: {e}")
            return self._get_from_db(request, category, limit)

        # Process results
        questions = result.get('aggregations', {}).get('by_question', {}).get('buckets', [])

        # Calculate accuracy and sort
        items_with_accuracy = []
        for q in questions:
            total = q['doc_count']
            if total < 3:  # Skip items with too few attempts
                continue

            correct = q['correct']['doc_count']
            accuracy = (correct / total * 100) if total > 0 else 0

            cat_buckets = q.get('category', {}).get('buckets', [])
            sub_buckets = q.get('subcategory', {}).get('buckets', [])

            items_with_accuracy.append({
                'item_id': q['key'],
                'item_name': q['key'].split('/')[-1] if '/' in q['key'] else q['key'],
                'category': cat_buckets[0]['key'] if cat_buckets else None,
                'subcategory': sub_buckets[0]['key'] if sub_buckets else None,
                'total_attempts': total,
                'correct_count': correct,
                'accuracy': round(accuracy, 2),
            })

        # Sort for hardest (lowest accuracy) and easiest (highest accuracy)
        hardest = sorted(items_with_accuracy, key=lambda x: x['accuracy'])[:limit]
        easiest = sorted(items_with_accuracy, key=lambda x: x['accuracy'], reverse=True)[:limit]

        # Wrong answer patterns
        wrong_patterns = []
        for bucket in result.get('aggregations', {}).get('wrong_patterns', {}).get('by_response', {}).get('buckets', []):
            wrong_patterns.append({
                'answer': bucket['key'],
                'count': bucket['doc_count'],
            })

        return Response({
            'hardest_items': hardest,
            'easiest_items': easiest,
            'wrong_answer_patterns': wrong_patterns[:10],
            'total_items_analyzed': len(items_with_accuracy),
            'source': 'elasticsearch',
        })

    def _get_from_db(self, request, category, limit):
        """Fallback: Get difficulty analysis from database."""
        # Filter by answered verb
        queryset = XAPIStatement.objects.filter(verb_id=XAPIVerb.ANSWERED)

        if category:
            queryset = queryset.filter(object_id__contains=f'/activity/{category}/')

        # Aggregate by object_id
        question_stats = queryset.values('object_id').annotate(
            total=Count('id'),
            correct=Count('id', filter=Q(result_success=True)),
        ).filter(total__gte=3)  # At least 3 attempts

        items_with_accuracy = []
        for item in question_stats:
            accuracy = (item['correct'] / item['total'] * 100) if item['total'] > 0 else 0
            items_with_accuracy.append({
                'item_id': item['object_id'],
                'item_name': item['object_id'].split('/')[-1] if '/' in item['object_id'] else item['object_id'],
                'total_attempts': item['total'],
                'correct_count': item['correct'],
                'accuracy': round(accuracy, 2),
            })

        hardest = sorted(items_with_accuracy, key=lambda x: x['accuracy'])[:limit]
        easiest = sorted(items_with_accuracy, key=lambda x: x['accuracy'], reverse=True)[:limit]

        return Response({
            'hardest_items': hardest,
            'easiest_items': easiest,
            'wrong_answer_patterns': [],
            'total_items_analyzed': len(items_with_accuracy),
            'source': 'database',
        })


class EngagementMetricsView(APIView):
    """
    Learning engagement metrics.

    Returns:
    - abandonment_rate: Quizzes started but not completed
    - avg_quiz_duration: Average time to complete quiz
    - hourly_activity: Activity distribution by hour (0-23)
    - daily_activity: Activity distribution by day of week
    """

    permission_classes = [IsStaffOrAdmin, HasAPIKey]

    def get(self, request):
        days = int(request.query_params.get('days', 30))

        if _es_available():
            return self._get_from_es(request, days)
        return self._get_from_db(request, days)

    def _get_from_es(self, request, days):
        """Get engagement metrics from Elasticsearch."""
        client = get_client()
        start_date = (timezone.now() - timedelta(days=days)).isoformat()

        # Aggregations
        aggs = {
            # Quiz completion stats
            'initialized': {
                'filter': {'term': {'verb.id': XAPIVerb.INITIALIZED}}
            },
            'completed': {
                'filter': {'term': {'verb.id': XAPIVerb.COMPLETED}}
            },
            # Hourly distribution
            'hourly': {
                'date_histogram': {
                    'field': 'timestamp',
                    'calendar_interval': 'hour',
                    'format': 'HH',
                    'min_doc_count': 0
                }
            },
            # Duration stats (from completed quizzes with duration)
            'avg_duration': {
                'filter': {
                    'bool': {
                        'must': [
                            {'term': {'verb.id': XAPIVerb.COMPLETED}},
                            {'exists': {'field': 'result.duration_seconds'}}
                        ]
                    }
                },
                'aggs': {
                    'duration': {'avg': {'field': 'result.duration_seconds'}}
                }
            }
        }

        try:
            result = client.search(
                index=STATEMENT_INDEX,
                body={
                    'size': 0,
                    'query': {'range': {'timestamp': {'gte': start_date}}},
                    'aggs': aggs
                }
            )
        except Exception as e:
            logger.error(f"ES engagement error: {e}")
            return self._get_from_db(request, days)

        agg_result = result.get('aggregations', {})

        # Calculate abandonment rate
        initialized = agg_result.get('initialized', {}).get('doc_count', 0)
        completed = agg_result.get('completed', {}).get('doc_count', 0)
        abandonment_rate = ((initialized - completed) / initialized * 100) if initialized > 0 else 0

        # Average duration
        avg_duration = agg_result.get('avg_duration', {}).get('duration', {}).get('value')
        avg_duration_minutes = round(avg_duration / 60, 2) if avg_duration else None

        # Hourly distribution (aggregate by hour of day)
        hourly_buckets = agg_result.get('hourly', {}).get('buckets', [])
        hourly_distribution = {str(i).zfill(2): 0 for i in range(24)}
        for bucket in hourly_buckets:
            hour = bucket['key_as_string']
            hourly_distribution[hour] = hourly_distribution.get(hour, 0) + bucket['doc_count']

        return Response({
            'period_days': days,
            'abandonment_rate': round(abandonment_rate, 2),
            'quizzes_started': initialized,
            'quizzes_completed': completed,
            'quizzes_abandoned': initialized - completed,
            'avg_quiz_duration_minutes': avg_duration_minutes,
            'hourly_activity': hourly_distribution,
            'peak_hour': max(hourly_distribution, key=hourly_distribution.get) if hourly_distribution else None,
            'source': 'elasticsearch',
        })

    def _get_from_db(self, request, days):
        """Fallback: Get engagement metrics from database."""
        start_date = timezone.now() - timedelta(days=days)

        # Quiz completion stats
        initialized = XAPIStatement.objects.filter(
            verb_id=XAPIVerb.INITIALIZED,
            timestamp__gte=start_date
        ).count()

        completed = XAPIStatement.objects.filter(
            verb_id=XAPIVerb.COMPLETED,
            timestamp__gte=start_date
        ).count()

        abandonment_rate = ((initialized - completed) / initialized * 100) if initialized > 0 else 0

        # Average duration
        duration_agg = XAPIStatement.objects.filter(
            verb_id=XAPIVerb.COMPLETED,
            timestamp__gte=start_date,
            result_duration__isnull=False
        ).aggregate(avg_duration=Avg('result_duration'))

        avg_duration = duration_agg['avg_duration']
        avg_duration_minutes = round(avg_duration.total_seconds() / 60, 2) if avg_duration else None

        # Hourly distribution
        from django.db.models.functions import ExtractHour
        hourly = XAPIStatement.objects.filter(
            timestamp__gte=start_date
        ).annotate(
            hour=ExtractHour('timestamp')
        ).values('hour').annotate(count=Count('id')).order_by('hour')

        hourly_distribution = {str(i).zfill(2): 0 for i in range(24)}
        for item in hourly:
            hourly_distribution[str(item['hour']).zfill(2)] = item['count']

        return Response({
            'period_days': days,
            'abandonment_rate': round(abandonment_rate, 2),
            'quizzes_started': initialized,
            'quizzes_completed': completed,
            'quizzes_abandoned': initialized - completed,
            'avg_quiz_duration_minutes': avg_duration_minutes,
            'hourly_activity': hourly_distribution,
            'peak_hour': max(hourly_distribution, key=hourly_distribution.get) if hourly_distribution else None,
            'source': 'database',
        })


class RetentionMetricsView(APIView):
    """
    User retention metrics.

    Returns:
    - retention_7d: 7-day retention rate
    - retention_30d: 30-day retention rate
    - user_streaks: Users with longest learning streaks
    - new_vs_returning: New vs returning user counts by day
    """

    permission_classes = [IsStaffOrAdmin, HasAPIKey]

    def get(self, request):
        if _es_available():
            return self._get_from_es(request)
        return self._get_from_db(request)

    def _get_from_es(self, request):
        """Get retention metrics from Elasticsearch."""
        client = get_client()
        now = timezone.now()

        # Calculate retention: users who were active in week 1 and returned in week 2
        week_1_start = (now - timedelta(days=14)).isoformat()
        week_1_end = (now - timedelta(days=7)).isoformat()
        week_2_start = week_1_end
        week_2_end = now.isoformat()

        try:
            # Users active in week 1
            week1_result = client.search(
                index=STATEMENT_INDEX,
                body={
                    'size': 0,
                    'query': {
                        'range': {'timestamp': {'gte': week_1_start, 'lt': week_1_end}}
                    },
                    'aggs': {
                        'users': {'terms': {'field': 'actor.user_id', 'size': 10000}}
                    }
                }
            )
            week1_users = set(b['key'] for b in week1_result['aggregations']['users']['buckets'])

            # Users active in week 2
            week2_result = client.search(
                index=STATEMENT_INDEX,
                body={
                    'size': 0,
                    'query': {
                        'range': {'timestamp': {'gte': week_2_start, 'lte': week_2_end}}
                    },
                    'aggs': {
                        'users': {'terms': {'field': 'actor.user_id', 'size': 10000}}
                    }
                }
            )
            week2_users = set(b['key'] for b in week2_result['aggregations']['users']['buckets'])

            # Retention = users in both weeks / users in week 1
            retained_users = week1_users & week2_users
            retention_7d = (len(retained_users) / len(week1_users) * 100) if week1_users else 0

            # 30-day retention (similar logic)
            month_1_start = (now - timedelta(days=60)).isoformat()
            month_1_end = (now - timedelta(days=30)).isoformat()

            month1_result = client.search(
                index=STATEMENT_INDEX,
                body={
                    'size': 0,
                    'query': {'range': {'timestamp': {'gte': month_1_start, 'lt': month_1_end}}},
                    'aggs': {'users': {'terms': {'field': 'actor.user_id', 'size': 10000}}}
                }
            )
            month1_users = set(b['key'] for b in month1_result['aggregations']['users']['buckets'])

            month2_result = client.search(
                index=STATEMENT_INDEX,
                body={
                    'size': 0,
                    'query': {'range': {'timestamp': {'gte': month_1_end}}},
                    'aggs': {'users': {'terms': {'field': 'actor.user_id', 'size': 10000}}}
                }
            )
            month2_users = set(b['key'] for b in month2_result['aggregations']['users']['buckets'])

            retained_month = month1_users & month2_users
            retention_30d = (len(retained_month) / len(month1_users) * 100) if month1_users else 0

            # User streaks (consecutive days with activity)
            streaks = self._calculate_streaks_es(client)

        except Exception as e:
            logger.error(f"ES retention error: {e}")
            return self._get_from_db(request)

        return Response({
            'retention_7d': round(retention_7d, 2),
            'retention_7d_users': {
                'week1_active': len(week1_users),
                'retained': len(retained_users),
            },
            'retention_30d': round(retention_30d, 2),
            'retention_30d_users': {
                'month1_active': len(month1_users),
                'retained': len(retained_month),
            },
            'top_streaks': streaks[:10],
            'source': 'elasticsearch',
        })

    def _calculate_streaks_es(self, client):
        """Calculate user learning streaks from ES."""
        now = timezone.now()
        start_date = (now - timedelta(days=90)).isoformat()

        # Get daily activity by user
        result = client.search(
            index=STATEMENT_INDEX,
            body={
                'size': 0,
                'query': {'range': {'timestamp': {'gte': start_date}}},
                'aggs': {
                    'by_user': {
                        'terms': {'field': 'actor.user_id', 'size': 1000},
                        'aggs': {
                            'by_day': {
                                'date_histogram': {
                                    'field': 'timestamp',
                                    'calendar_interval': 'day',
                                    'format': 'yyyy-MM-dd'
                                }
                            }
                        }
                    }
                }
            }
        )

        # Fetch user display names from DB
        user_ids = [bucket['key'] for bucket in result['aggregations']['by_user']['buckets']]
        user_display_names = {}
        if user_ids:
            users = User.objects.select_related('profile').filter(id__in=user_ids)
            for user in users:
                user_display_names[user.id] = _get_user_display_name(user)

        user_streaks = []
        for user_bucket in result['aggregations']['by_user']['buckets']:
            user_id = user_bucket['key']
            username = user_display_names.get(user_id, f'User {user_id}')

            days = sorted([b['key_as_string'] for b in user_bucket['by_day']['buckets'] if b['doc_count'] > 0])

            if not days:
                continue

            # Calculate max streak
            max_streak = 1
            current_streak = 1
            from datetime import datetime

            for i in range(1, len(days)):
                prev = datetime.strptime(days[i - 1], '%Y-%m-%d')
                curr = datetime.strptime(days[i], '%Y-%m-%d')
                if (curr - prev).days == 1:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 1

            user_streaks.append({
                'user_id': user_id,
                'username': username,
                'max_streak': max_streak,
                'total_active_days': len(days),
            })

        return sorted(user_streaks, key=lambda x: x['max_streak'], reverse=True)

    def _get_from_db(self, request):
        """Fallback: Get retention metrics from database."""
        now = timezone.now()

        # 7-day retention
        week_1_start = now - timedelta(days=14)
        week_1_end = now - timedelta(days=7)

        week1_users = set(XAPIStatement.objects.filter(
            timestamp__gte=week_1_start,
            timestamp__lt=week_1_end
        ).values_list('actor_user_id', flat=True).distinct())

        week2_users = set(XAPIStatement.objects.filter(
            timestamp__gte=week_1_end
        ).values_list('actor_user_id', flat=True).distinct())

        retained = week1_users & week2_users
        retention_7d = (len(retained) / len(week1_users) * 100) if week1_users else 0

        # 30-day retention
        month_1_start = now - timedelta(days=60)
        month_1_end = now - timedelta(days=30)

        month1_users = set(XAPIStatement.objects.filter(
            timestamp__gte=month_1_start,
            timestamp__lt=month_1_end
        ).values_list('actor_user_id', flat=True).distinct())

        month2_users = set(XAPIStatement.objects.filter(
            timestamp__gte=month_1_end
        ).values_list('actor_user_id', flat=True).distinct())

        retained_month = month1_users & month2_users
        retention_30d = (len(retained_month) / len(month1_users) * 100) if month1_users else 0

        # Streaks
        streaks = self._calculate_streaks_db()

        return Response({
            'retention_7d': round(retention_7d, 2),
            'retention_7d_users': {
                'week1_active': len(week1_users),
                'retained': len(retained),
            },
            'retention_30d': round(retention_30d, 2),
            'retention_30d_users': {
                'month1_active': len(month1_users),
                'retained': len(retained_month),
            },
            'top_streaks': streaks[:10],
            'source': 'database',
        })

    def _calculate_streaks_db(self):
        """Calculate user learning streaks from database."""
        from django.db.models.functions import TruncDate

        now = timezone.now()
        start_date = now - timedelta(days=90)

        # Get active days per user
        user_days = XAPIStatement.objects.filter(
            timestamp__gte=start_date
        ).annotate(
            day=TruncDate('timestamp')
        ).values('actor_user_id', 'day').distinct()

        # Group by user
        user_activity = {}
        for item in user_days:
            user_id = item['actor_user_id']
            if user_id not in user_activity:
                user_activity[user_id] = {'days': set()}
            user_activity[user_id]['days'].add(item['day'])

        # Fetch user display names from DB
        user_display_names = {}
        if user_activity:
            users = User.objects.select_related('profile').filter(id__in=user_activity.keys())
            for user in users:
                user_display_names[user.id] = _get_user_display_name(user)

        # Calculate streaks
        user_streaks = []
        for user_id, data in user_activity.items():
            days = sorted(data['days'])
            if not days:
                continue

            max_streak = 1
            current_streak = 1

            for i in range(1, len(days)):
                if (days[i] - days[i - 1]).days == 1:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 1

            user_streaks.append({
                'user_id': user_id,
                'username': user_display_names.get(user_id, f'User {user_id}'),
                'max_streak': max_streak,
                'total_active_days': len(days),
            })

        return sorted(user_streaks, key=lambda x: x['max_streak'], reverse=True)


class GrowthMetricsView(APIView):
    """
    User growth and improvement metrics.

    Returns:
    - improvement_trend: User performance improvement over time
    - first_vs_retry: First attempt vs retry accuracy
    - mastery_stats: Items mastered (>90% accuracy)
    """

    permission_classes = [IsStaffOrAdmin, HasAPIKey]

    def get(self, request):
        user_id = request.query_params.get('user_id')
        days = int(request.query_params.get('days', 30))

        if _es_available():
            return self._get_from_es(request, user_id, days)
        return self._get_from_db(request, user_id, days)

    def _get_from_es(self, request, user_id, days):
        """Get growth metrics from Elasticsearch."""
        client = get_client()
        start_date = (timezone.now() - timedelta(days=days)).isoformat()

        # Build filter
        must_filters = [
            {'range': {'timestamp': {'gte': start_date}}},
            {'term': {'verb.id': XAPIVerb.COMPLETED}}
        ]
        if user_id:
            must_filters.append({'term': {'actor.user_id': int(user_id)}})

        try:
            # Score improvement over time
            result = client.search(
                index=STATEMENT_INDEX,
                body={
                    'size': 0,
                    'query': {'bool': {'must': must_filters}},
                    'aggs': {
                        'by_week': {
                            'date_histogram': {
                                'field': 'timestamp',
                                'calendar_interval': 'week',
                                'format': 'yyyy-MM-dd'
                            },
                            'aggs': {
                                'avg_score': {'avg': {'field': 'result.score_scaled'}},
                                'quiz_count': {'value_count': {'field': 'id'}}
                            }
                        },
                        'overall_avg': {'avg': {'field': 'result.score_scaled'}}
                    }
                }
            )

            # Process improvement trend
            improvement_trend = []
            for bucket in result['aggregations']['by_week']['buckets']:
                avg_score = bucket['avg_score']['value']
                improvement_trend.append({
                    'week': bucket['key_as_string'],
                    'avg_score': round(avg_score * 100, 2) if avg_score else 0,
                    'quiz_count': bucket['quiz_count']['value'],
                })

            overall_avg = result['aggregations']['overall_avg']['value']

            # Mastery stats (items with >90% accuracy)
            mastery_result = client.search(
                index=STATEMENT_INDEX,
                body={
                    'size': 0,
                    'query': {
                        'bool': {
                            'must': [
                                {'term': {'verb.id': XAPIVerb.ANSWERED}},
                                {'range': {'timestamp': {'gte': start_date}}}
                            ] + ([{'term': {'actor.user_id': int(user_id)}}] if user_id else [])
                        }
                    },
                    'aggs': {
                        'by_item': {
                            'terms': {'field': 'object.id', 'size': 1000},
                            'aggs': {
                                'correct': {'filter': {'term': {'result.success': True}}},
                                'total': {'value_count': {'field': 'id'}}
                            }
                        }
                    }
                }
            )

            mastered = 0
            learning = 0
            struggling = 0

            for bucket in mastery_result['aggregations']['by_item']['buckets']:
                total = bucket['doc_count']
                if total < 3:
                    continue
                correct = bucket['correct']['doc_count']
                accuracy = correct / total if total > 0 else 0

                if accuracy >= 0.9:
                    mastered += 1
                elif accuracy >= 0.6:
                    learning += 1
                else:
                    struggling += 1

        except Exception as e:
            logger.error(f"ES growth metrics error: {e}")
            return self._get_from_db(request, user_id, days)

        return Response({
            'period_days': days,
            'improvement_trend': improvement_trend,
            'overall_avg_score': round(overall_avg * 100, 2) if overall_avg else 0,
            'mastery_stats': {
                'mastered': mastered,  # >90% accuracy
                'learning': learning,   # 60-90% accuracy
                'struggling': struggling,  # <60% accuracy
                'total_items': mastered + learning + struggling,
            },
            'source': 'elasticsearch',
        })

    def _get_from_db(self, request, user_id, days):
        """Fallback: Get growth metrics from database."""
        start_date = timezone.now() - timedelta(days=days)

        # Base queryset
        completed_qs = XAPIStatement.objects.filter(
            verb_id=XAPIVerb.COMPLETED,
            timestamp__gte=start_date
        )
        if user_id:
            completed_qs = completed_qs.filter(actor_user_id=user_id)

        # Weekly improvement
        from django.db.models.functions import TruncWeek
        weekly_stats = completed_qs.annotate(
            week=TruncWeek('timestamp')
        ).values('week').annotate(
            avg_score=Avg('result_score_scaled'),
            quiz_count=Count('id')
        ).order_by('week')

        improvement_trend = []
        for item in weekly_stats:
            improvement_trend.append({
                'week': item['week'].strftime('%Y-%m-%d') if item['week'] else None,
                'avg_score': round(item['avg_score'] * 100, 2) if item['avg_score'] else 0,
                'quiz_count': item['quiz_count'],
            })

        # Overall average
        overall = completed_qs.aggregate(avg=Avg('result_score_scaled'))
        overall_avg = overall['avg']

        # Mastery stats
        answered_qs = XAPIStatement.objects.filter(
            verb_id=XAPIVerb.ANSWERED,
            timestamp__gte=start_date
        )
        if user_id:
            answered_qs = answered_qs.filter(actor_user_id=user_id)

        item_stats = answered_qs.values('object_id').annotate(
            total=Count('id'),
            correct=Count('id', filter=Q(result_success=True))
        ).filter(total__gte=3)

        mastered = 0
        learning = 0
        struggling = 0

        for item in item_stats:
            accuracy = item['correct'] / item['total'] if item['total'] > 0 else 0
            if accuracy >= 0.9:
                mastered += 1
            elif accuracy >= 0.6:
                learning += 1
            else:
                struggling += 1

        return Response({
            'period_days': days,
            'improvement_trend': improvement_trend,
            'overall_avg_score': round(overall_avg * 100, 2) if overall_avg else 0,
            'mastery_stats': {
                'mastered': mastered,
                'learning': learning,
                'struggling': struggling,
                'total_items': mastered + learning + struggling,
            },
            'source': 'database',
        })
