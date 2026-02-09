"""
XP Service

Business logic for the XP/Level gamification system.
Handles XP awards, penalties, level calculation, and daily caps.
"""

import logging
from datetime import date

from django.db import transaction

logger = logging.getLogger(__name__)

# Level thresholds: level -> cumulative XP required
LEVEL_THRESHOLDS = {
    1: 0,
    2: 30,
    3: 80,
    4: 150,
    5: 250,
    6: 400,
    7: 600,
    8: 850,
    9: 1150,
    10: 1500,
}

MAX_LEVEL = 10
MAX_DAILY_XP = 30
MAX_DAILY_FLASHCARD_WORDS = 50
FLASHCARD_XP_PER_10_WORDS = 3
QUIZ_PARTICIPATION_XP = 1
PASS_THRESHOLD = 80
MAX_LEVEL_DROP = 5

# Quiz types that award +5 XP on pass (select/choice types)
SELECT_QUIZ_TYPES = {
    'word_to_native', 'native_to_word_select',
    'gana_to_romaji', 'romaji_to_gana_select',
}
# Quiz types that award +7 XP on pass (input/mixed/blank types)
INPUT_QUIZ_TYPES = {
    'native_to_word_input', 'example_fill_in_blank',
    'mixed', 'romaji_to_gana_input',
}

# Absence penalty: days_absent -> penalty amount
ABSENCE_PENALTIES = {
    1: 0,
    2: -3,
    3: -5,
}
ABSENCE_PENALTY_MAX = -7  # 4+ days


def get_or_create_user_xp(user):
    """Get or create UserXP for the given user."""
    from .models import UserXP
    xp_profile, _ = UserXP.objects.select_for_update().get_or_create(user=user)
    return xp_profile


def _reset_daily_if_needed(xp_profile, today=None):
    """Reset daily counters if it's a new day."""
    today = today or date.today()
    if xp_profile.daily_xp_date != today:
        xp_profile.daily_xp_earned = 0
        xp_profile.daily_flashcard_words = 0
        xp_profile.daily_xp_date = today


def _calculate_level(total_xp, max_level_achieved):
    """Calculate level from total XP with max 5 level drop cap."""
    natural_level = 1
    for level in range(MAX_LEVEL, 0, -1):
        if total_xp >= LEVEL_THRESHOLDS[level]:
            natural_level = level
            break

    min_allowed_level = max(1, max_level_achieved - MAX_LEVEL_DROP)
    return max(natural_level, min_allowed_level)


def _apply_absence_penalty(xp_profile, today=None):
    """Apply absence penalty on return (lazy evaluation). Returns penalty amount."""
    from .models import XPTransaction

    today = today or date.today()

    if xp_profile.last_activity_date is None:
        return 0

    days_absent = (today - xp_profile.last_activity_date).days

    if days_absent <= 1:
        return 0

    if xp_profile.absence_penalty_applied:
        return 0

    penalty = ABSENCE_PENALTIES.get(days_absent, ABSENCE_PENALTY_MAX)
    if penalty == 0:
        return 0

    xp_profile.total_xp = max(0, xp_profile.total_xp + penalty)
    xp_profile.current_level = _calculate_level(
        xp_profile.total_xp, xp_profile.max_level_achieved
    )
    xp_profile.absence_penalty_applied = True

    XPTransaction.objects.create(
        user=xp_profile.user,
        source=XPTransaction.XPSource.ABSENCE_PENALTY,
        amount=penalty,
        description=f'{days_absent}일 부재 패널티',
    )

    return penalty


def _add_xp(xp_profile, amount, source, description='',
            related_object_type='', related_object_id=None):
    """Add XP respecting daily cap. Returns actual amount awarded."""
    from .models import XPTransaction

    today = date.today()
    _reset_daily_if_needed(xp_profile, today)

    remaining_daily = MAX_DAILY_XP - xp_profile.daily_xp_earned
    if remaining_daily <= 0:
        return 0

    actual_amount = min(amount, remaining_daily)

    xp_profile.total_xp += actual_amount
    xp_profile.daily_xp_earned += actual_amount
    xp_profile.last_activity_date = today
    xp_profile.absence_penalty_applied = False

    xp_profile.current_level = _calculate_level(
        xp_profile.total_xp, xp_profile.max_level_achieved
    )
    if xp_profile.current_level > xp_profile.max_level_achieved:
        xp_profile.max_level_achieved = xp_profile.current_level

    XPTransaction.objects.create(
        user=xp_profile.user,
        source=source,
        amount=actual_amount,
        description=description,
        related_object_type=related_object_type,
        related_object_id=related_object_id,
    )

    return actual_amount


@transaction.atomic
def award_flashcard_xp(user, session):
    """Award XP for flashcard completion. 10 words per 3 XP, daily max 50 words."""
    from .models import XPTransaction

    xp_profile = get_or_create_user_xp(user)
    today = date.today()
    _reset_daily_if_needed(xp_profile, today)
    _apply_absence_penalty(xp_profile, today)

    remaining_words = MAX_DAILY_FLASHCARD_WORDS - xp_profile.daily_flashcard_words
    eligible_words = min(session.total_cards, max(0, remaining_words))

    if eligible_words <= 0:
        xp_profile.save()
        return 0

    xp_profile.daily_flashcard_words += eligible_words
    xp_amount = (eligible_words // 10) * FLASHCARD_XP_PER_10_WORDS

    if xp_amount <= 0:
        xp_profile.save()
        return 0

    awarded = _add_xp(
        xp_profile, xp_amount,
        source=XPTransaction.XPSource.FLASHCARD,
        description=f'플래시카드 {eligible_words}단어 학습',
        related_object_type='FlashcardSession',
        related_object_id=session.id,
    )

    xp_profile.save()
    return awarded


@transaction.atomic
def award_quiz_xp(user, quiz, quiz_model_name):
    """Award XP for quiz completion. 1 XP participation + bonus if passed."""
    from .models import XPTransaction

    xp_profile = get_or_create_user_xp(user)
    today = date.today()
    _reset_daily_if_needed(xp_profile, today)
    _apply_absence_penalty(xp_profile, today)

    total_awarded = 0

    # Participation XP (always 1)
    participation = _add_xp(
        xp_profile, QUIZ_PARTICIPATION_XP,
        source=XPTransaction.XPSource.QUIZ_PARTICIPATION,
        description=f'퀴즈 참여 ({quiz_model_name})',
        related_object_type=quiz_model_name,
        related_object_id=quiz.id,
    )
    total_awarded += participation

    # Pass bonus
    score = quiz.score_percentage
    if score >= PASS_THRESHOLD:
        quiz_type = quiz.quiz_type

        if quiz_type in INPUT_QUIZ_TYPES:
            bonus = 7
        elif quiz_type in SELECT_QUIZ_TYPES:
            bonus = 5
        else:
            bonus = 0

        if bonus > 0:
            pass_awarded = _add_xp(
                xp_profile, bonus,
                source=XPTransaction.XPSource.QUIZ_PASS,
                description=f'퀴즈 통과 ({quiz_type}, {score:.0f}%)',
                related_object_type=quiz_model_name,
                related_object_id=quiz.id,
            )
            total_awarded += pass_awarded

    xp_profile.save()
    return total_awarded


def get_xp_status(user):
    """Get full XP status for the API response."""
    from .models import UserXP

    xp_profile, _ = UserXP.objects.get_or_create(user=user)
    today = date.today()
    _reset_daily_if_needed(xp_profile, today)

    current_level = xp_profile.current_level
    current_threshold = LEVEL_THRESHOLDS.get(current_level, 0)
    next_level = min(current_level + 1, MAX_LEVEL)
    next_threshold = LEVEL_THRESHOLDS.get(next_level, LEVEL_THRESHOLDS[MAX_LEVEL])

    if current_level >= MAX_LEVEL:
        xp_in_level = xp_profile.total_xp - current_threshold
        xp_for_next = 0
        progress_percentage = 100.0
    else:
        xp_in_level = xp_profile.total_xp - current_threshold
        xp_for_next = next_threshold - current_threshold
        progress_percentage = (xp_in_level / xp_for_next * 100) if xp_for_next > 0 else 100.0

    # Save if daily counters were reset
    if xp_profile.daily_xp_date == today and xp_profile.pk:
        xp_profile.save()

    return {
        'total_xp': xp_profile.total_xp,
        'current_level': current_level,
        'max_level_achieved': xp_profile.max_level_achieved,
        'daily_xp_earned': xp_profile.daily_xp_earned,
        'daily_xp_max': MAX_DAILY_XP,
        'xp_in_level': xp_in_level,
        'xp_for_next_level': xp_for_next,
        'progress_percentage': round(progress_percentage, 1),
        'next_level': next_level if current_level < MAX_LEVEL else None,
    }
