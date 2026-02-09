"""
User Stats Views

Personal learning stats APIs for authenticated users.

Endpoints:
- GET /user/streak-recommendation - Streak + recommended card
"""

import logging
from datetime import timedelta

from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import XAPIStatement

logger = logging.getLogger(__name__)


class UserStreakRecommendationView(APIView):
    """
    Returns the current user's learning streak and a recommended card.

    Response:
    {
      "streak": {
        "current_streak": 5,
        "max_streak": 12,
        "last_activity_date": "2026-02-08",
        "is_active_today": true,
        "days_since_last_study": 0
      },
      "recommendation": {
        "card_id": "flashcard",
        "reason_key": "reviewWords",
        "reason_params": {},
        "priority": "high"
      }
    }
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        streak = self._calculate_streak(user)
        recommendation = self._calculate_recommendation(user)

        from ..xp_service import get_xp_status
        xp = get_xp_status(user)

        return Response({
            'success': True,
            'message': 'Streak, recommendation, and XP retrieved',
            'data': {
                'streak': streak,
                'recommendation': recommendation,
                'xp': xp,
            },
        })

    def _calculate_streak(self, user):
        """Calculate learning streak from XAPIStatement activity dates."""
        now = timezone.now()
        today = now.date()
        start_date = now - timedelta(days=90)

        active_days = list(
            XAPIStatement.objects.filter(
                actor_user=user,
                timestamp__gte=start_date,
            ).annotate(
                day=TruncDate('timestamp')
            ).values_list('day', flat=True).distinct().order_by('-day')
        )

        if not active_days:
            return {
                'current_streak': 0,
                'max_streak': 0,
                'last_activity_date': None,
                'is_active_today': False,
                'days_since_last_study': None,
            }

        last_activity_date = active_days[0]
        is_active_today = last_activity_date == today
        days_since = (today - last_activity_date).days

        # Calculate current streak (from today/yesterday backwards)
        days_set = set(active_days)
        current_streak = 0
        check_date = today if is_active_today else today - timedelta(days=1)

        # Only count current streak if active today or yesterday
        if check_date in days_set:
            while check_date in days_set:
                current_streak += 1
                check_date -= timedelta(days=1)

        # Calculate max streak
        sorted_days = sorted(active_days)
        max_streak = 1
        streak = 1
        for i in range(1, len(sorted_days)):
            if (sorted_days[i] - sorted_days[i - 1]).days == 1:
                streak += 1
                max_streak = max(max_streak, streak)
            else:
                streak = 1

        return {
            'current_streak': current_streak,
            'max_streak': max(max_streak, current_streak),
            'last_activity_date': last_activity_date.isoformat(),
            'is_active_today': is_active_today,
            'days_since_last_study': days_since,
        }

    def _calculate_recommendation(self, user):
        """Calculate recommended card using weighted scoring."""
        from words.models import (
            FlashcardSession, WordQuiz, GanaQuiz,
            UserWordStats, Vocabulary,
        )

        now = timezone.now()
        today = now.date()

        # Gather input data
        last_flashcard = FlashcardSession.objects.filter(
            user=user, is_completed=True
        ).order_by('-completed_at').values_list('completed_at', flat=True).first()

        last_word_quiz = WordQuiz.objects.filter(
            user=user, is_completed=True
        ).order_by('-completed_at').values_list('completed_at', flat=True).first()

        last_gana_quiz = GanaQuiz.objects.filter(
            user=user, is_completed=True
        ).order_by('-completed_at').values_list('completed_at', flat=True).first()

        # days_since_quiz = min of word quiz and gana quiz
        quiz_dates = [d for d in [last_word_quiz, last_gana_quiz] if d]
        last_quiz_date = max(quiz_dates) if quiz_dates else None

        days_since_flashcard = (today - last_flashcard.date()).days if last_flashcard else 999
        days_since_quiz = (today - last_quiz_date.date()).days if last_quiz_date else 999

        # Quiz accuracy
        word_quiz_stats = WordQuiz.objects.filter(
            user=user, is_completed=True
        ).aggregate(
            total_correct=Sum('correct_count'),
            total_questions=Sum('total_questions'),
        )
        gana_quiz_stats = GanaQuiz.objects.filter(
            user=user, is_completed=True
        ).aggregate(
            total_correct=Sum('correct_count'),
            total_questions=Sum('total_questions'),
        )

        total_correct = (word_quiz_stats['total_correct'] or 0) + (gana_quiz_stats['total_correct'] or 0)
        total_questions = (word_quiz_stats['total_questions'] or 0) + (gana_quiz_stats['total_questions'] or 0)
        quiz_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0
        total_quiz_attempts = total_questions

        # Learned words count
        learned_words_count = UserWordStats.objects.filter(
            user=user, total_attempts__gte=1
        ).count()

        # Has vocabularies
        has_vocabularies = Vocabulary.objects.filter(
            user=user, is_active=True
        ).exists()

        # Calculate scores for each card
        scores = {}

        # Flashcard score
        fc_score = min(days_since_flashcard * 10, 30)
        if total_quiz_attempts == 0:
            fc_score += 30  # New user bonus
        elif total_quiz_attempts >= 10 and quiz_accuracy < 70:
            fc_score += max(0, (70 - quiz_accuracy) * 0.5)
        scores['flashcard'] = fc_score

        # Quiz score
        q_score = min(days_since_quiz * 5, 35)
        if days_since_flashcard < 3:
            q_score += 20  # Recently studied → test yourself
        if quiz_accuracy > 70:
            q_score += 10
        scores['quiz'] = q_score

        # Learned words score
        lw_score = min(learned_words_count / 2, 20)
        if days_since_flashcard < 3:
            lw_score += 10
        scores['learnedWords'] = lw_score

        # Vocabulary score
        v_score = 10 if has_vocabularies else 0
        v_score += min(days_since_flashcard * 2, 10) if days_since_flashcard != 999 else 0
        scores['vocabulary'] = v_score

        # Word browse score
        wb_score = 5
        if learned_words_count < 10:
            wb_score += 10
        scores['wordBrowse'] = wb_score

        # Find best card
        best_card = max(scores, key=scores.get)
        priority = 'high' if scores[best_card] >= 30 else 'medium' if scores[best_card] >= 15 else 'low'

        # Determine reason
        reason_key, reason_params = self._get_reason(
            best_card, days_since_flashcard, days_since_quiz,
            quiz_accuracy, total_quiz_attempts, learned_words_count,
        )

        return {
            'card_id': best_card,
            'reason_key': reason_key,
            'reason_params': reason_params,
            'priority': priority,
        }

    def _get_reason(self, card_id, days_fc, days_quiz, accuracy, attempts, learned_count):
        """Determine the recommendation reason key and params."""
        if card_id == 'flashcard':
            if attempts == 0:
                return 'startLearning', {}
            if attempts >= 10 and accuracy < 70:
                return 'lowAccuracy', {'accuracy': round(accuracy, 1)}
            return 'reviewWords', {'days': days_fc}

        if card_id == 'quiz':
            if days_fc < 3:
                return 'testYourself', {}
            return 'keepPracticing', {}

        if card_id == 'learnedWords':
            return 'checkProgress', {'count': learned_count}

        if card_id == 'vocabulary':
            return 'organizeWords', {}

        # wordBrowse
        return 'exploreNewWords', {}
