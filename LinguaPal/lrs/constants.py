"""
xAPI and cmi5 Constants

Defines verb IDs, activity types, and other constants following
the xAPI specification and cmi5 profile.
"""


class XAPIVerb:
    """
    ADLNet Standard Verbs for xAPI.
    Reference: https://github.com/adlnet/xAPI-Spec
    """
    # Core verbs
    INITIALIZED = 'http://adlnet.gov/expapi/verbs/initialized'
    TERMINATED = 'http://adlnet.gov/expapi/verbs/terminated'
    COMPLETED = 'http://adlnet.gov/expapi/verbs/completed'
    PASSED = 'http://adlnet.gov/expapi/verbs/passed'
    FAILED = 'http://adlnet.gov/expapi/verbs/failed'

    # Quiz-specific verbs
    ANSWERED = 'http://adlnet.gov/expapi/verbs/answered'
    PROGRESSED = 'http://adlnet.gov/expapi/verbs/progressed'
    EXPERIENCED = 'http://adlnet.gov/expapi/verbs/experienced'
    ATTEMPTED = 'http://adlnet.gov/expapi/verbs/attempted'

    # Display names (multilingual)
    DISPLAY = {
        INITIALIZED: {'en-US': 'initialized', 'ko': '시작함'},
        TERMINATED: {'en-US': 'terminated', 'ko': '종료함'},
        COMPLETED: {'en-US': 'completed', 'ko': '완료함'},
        PASSED: {'en-US': 'passed', 'ko': '통과함'},
        FAILED: {'en-US': 'failed', 'ko': '불합격'},
        ANSWERED: {'en-US': 'answered', 'ko': '답변함'},
        PROGRESSED: {'en-US': 'progressed', 'ko': '진행함'},
        EXPERIENCED: {'en-US': 'experienced', 'ko': '경험함'},
        ATTEMPTED: {'en-US': 'attempted', 'ko': '시도함'},
    }

    @classmethod
    def get_display(cls, verb_id: str, lang: str = 'en-US') -> str:
        """Get display name for a verb in the specified language."""
        displays = cls.DISPLAY.get(verb_id, {})
        return displays.get(lang, displays.get('en-US', verb_id.split('/')[-1]))


class CMI5Verb:
    """
    cmi5 Profile Verbs (9 defined verbs).
    Reference: https://github.com/AICC/CMI-5_Spec_Current
    """
    # cmi5-specific verbs
    LAUNCHED = 'https://w3id.org/xapi/adl/verbs/launched'
    INITIALIZED = 'https://w3id.org/xapi/adl/verbs/initialized'
    ABANDONED = 'https://w3id.org/xapi/adl/verbs/abandoned'
    WAIVED = 'https://w3id.org/xapi/adl/verbs/waived'
    SATISFIED = 'https://w3id.org/xapi/adl/verbs/satisfied'

    # Shared with ADLNet (same IRI)
    COMPLETED = 'http://adlnet.gov/expapi/verbs/completed'
    PASSED = 'http://adlnet.gov/expapi/verbs/passed'
    FAILED = 'http://adlnet.gov/expapi/verbs/failed'
    TERMINATED = 'http://adlnet.gov/expapi/verbs/terminated'

    # All cmi5 verbs
    ALL = [
        LAUNCHED, INITIALIZED, COMPLETED, PASSED, FAILED,
        ABANDONED, WAIVED, SATISFIED, TERMINATED
    ]

    # Display names
    DISPLAY = {
        LAUNCHED: {'en-US': 'launched', 'ko': '시작됨'},
        INITIALIZED: {'en-US': 'initialized', 'ko': '초기화됨'},
        COMPLETED: {'en-US': 'completed', 'ko': '완료함'},
        PASSED: {'en-US': 'passed', 'ko': '통과함'},
        FAILED: {'en-US': 'failed', 'ko': '불합격'},
        ABANDONED: {'en-US': 'abandoned', 'ko': '중단됨'},
        WAIVED: {'en-US': 'waived', 'ko': '면제됨'},
        SATISFIED: {'en-US': 'satisfied', 'ko': '충족함'},
        TERMINATED: {'en-US': 'terminated', 'ko': '종료됨'},
    }

    @classmethod
    def get_display(cls, verb_id: str, lang: str = 'en-US') -> str:
        """Get display name for a verb in the specified language."""
        displays = cls.DISPLAY.get(verb_id, {})
        return displays.get(lang, displays.get('en-US', verb_id.split('/')[-1]))


class XAPIActivityType:
    """
    xAPI Activity Types.
    Reference: https://registry.tincanapi.com/
    """
    # Assessment types
    ASSESSMENT = 'http://adlnet.gov/expapi/activities/assessment'
    QUESTION = 'http://adlnet.gov/expapi/activities/question'

    # Content types
    COURSE = 'http://adlnet.gov/expapi/activities/course'
    MODULE = 'http://adlnet.gov/expapi/activities/module'
    LESSON = 'http://adlnet.gov/expapi/activities/lesson'

    # Interaction types
    INTERACTION = 'http://adlnet.gov/expapi/activities/interaction'

    # cmi5 types
    CMI5_AU = 'https://w3id.org/xapi/cmi5/activitytype/course'
    CMI5_BLOCK = 'https://w3id.org/xapi/cmi5/activitytype/block'


class XAPIInteractionType:
    """
    xAPI Interaction Types for questions.
    """
    TRUE_FALSE = 'true-false'
    CHOICE = 'choice'
    FILL_IN = 'fill-in'
    LONG_FILL_IN = 'long-fill-in'
    MATCHING = 'matching'
    PERFORMANCE = 'performance'
    SEQUENCING = 'sequencing'
    LIKERT = 'likert'
    NUMERIC = 'numeric'
    OTHER = 'other'


class QuizType:
    """
    LinguaPal Quiz Types for context extension.
    """
    GANA_QUIZ = 'gana_quiz'
    WORD_QUIZ = 'word_quiz'

    # Gana quiz subtypes
    HIRAGANA_TO_ROMAJI = 'hiragana_to_romaji'
    KATAKANA_TO_ROMAJI = 'katakana_to_romaji'
    ROMAJI_TO_HIRAGANA = 'romaji_to_hiragana'
    ROMAJI_TO_KATAKANA = 'romaji_to_katakana'

    # Word quiz subtypes
    WORD_TO_MEANING = 'word_to_meaning'
    MEANING_TO_WORD = 'meaning_to_word'
    LISTENING = 'listening'


class CMI5LaunchMode:
    """
    cmi5 Launch Modes.
    """
    NORMAL = 'Normal'
    BROWSE = 'Browse'
    REVIEW = 'Review'


class CMI5MoveOn:
    """
    cmi5 moveOn values.
    """
    PASSED = 'Passed'
    COMPLETED = 'Completed'
    COMPLETED_AND_PASSED = 'CompletedAndPassed'
    COMPLETED_OR_PASSED = 'CompletedOrPassed'
    NOT_APPLICABLE = 'NotApplicable'


# LinguaPal base IRI for xAPI objects
LINGUAPAL_BASE_IRI = 'https://linguapal.com'

# Default mastery score (80%)
DEFAULT_MASTERY_SCORE = 0.8
