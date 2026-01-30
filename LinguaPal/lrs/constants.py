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


class ActivityID:
    """
    Activity ID generator for LinguaPal quizzes.

    Activity IDs are structured to group by quiz type and language/character set.
    This allows for meaningful analytics and comparison.

    Patterns:
    - Gana Quiz: activity/gana/{character_set}/{quiz_type}
    - Word Quiz: activity/word/{language_code}/{quiz_type}
    """

    @classmethod
    def gana_quiz(cls, character_set: str, quiz_type: str) -> str:
        """
        Generate Activity ID for Gana Quiz.

        Args:
            character_set: 'hiragana', 'katakana', or 'all'
            quiz_type: 'gana_to_romaji', 'romaji_to_gana_select', 'romaji_to_gana_input'

        Returns:
            Full Activity IRI
        """
        return f"{LINGUAPAL_BASE_IRI}/activity/gana/{character_set}/{quiz_type}"

    @classmethod
    def gana_quiz_instance(cls, character_set: str, quiz_type: str, quiz_id: int) -> str:
        """Generate Activity ID for a specific Gana Quiz instance."""
        return f"{LINGUAPAL_BASE_IRI}/activity/gana/{character_set}/{quiz_type}/session/{quiz_id}"

    @classmethod
    def gana_question(cls, character_set: str, quiz_type: str, quiz_id: int, question_id: int) -> str:
        """Generate Activity ID for a Gana Quiz question."""
        return f"{LINGUAPAL_BASE_IRI}/activity/gana/{character_set}/{quiz_type}/session/{quiz_id}/question/{question_id}"

    @classmethod
    def word_quiz(cls, language_code: str, quiz_type: str) -> str:
        """
        Generate Activity ID for Word Quiz.

        Args:
            language_code: Language code (e.g., 'es', 'ja', 'ko')
            quiz_type: 'word_to_native', 'native_to_word_select', 'native_to_word_input'

        Returns:
            Full Activity IRI
        """
        return f"{LINGUAPAL_BASE_IRI}/activity/word/{language_code}/{quiz_type}"

    @classmethod
    def word_quiz_instance(cls, language_code: str, quiz_type: str, quiz_id: int) -> str:
        """Generate Activity ID for a specific Word Quiz instance."""
        return f"{LINGUAPAL_BASE_IRI}/activity/word/{language_code}/{quiz_type}/session/{quiz_id}"

    @classmethod
    def word_question(cls, language_code: str, quiz_type: str, quiz_id: int, question_id: int) -> str:
        """Generate Activity ID for a Word Quiz question."""
        return f"{LINGUAPAL_BASE_IRI}/activity/word/{language_code}/{quiz_type}/session/{quiz_id}/question/{question_id}"

    @classmethod
    def parse(cls, activity_id: str) -> dict:
        """
        Parse an Activity ID into its components.

        Returns:
            Dict with keys: category, subcategory, quiz_type, quiz_id, question_id
        """
        # Remove base IRI if present
        path = activity_id.replace(LINGUAPAL_BASE_IRI + '/', '')
        if path.startswith('activity/'):
            path = path[9:]  # Remove 'activity/'

        parts = path.split('/')
        result = {
            'category': parts[0] if len(parts) > 0 else None,  # 'gana' or 'word'
            'subcategory': parts[1] if len(parts) > 1 else None,  # character_set or language_code
            'quiz_type': parts[2] if len(parts) > 2 else None,
            'quiz_id': None,
            'question_id': None,
        }

        # Parse session/quiz_id
        if len(parts) > 4 and parts[3] == 'session':
            try:
                result['quiz_id'] = int(parts[4])
            except (ValueError, IndexError):
                pass

        # Parse question_id
        if len(parts) > 6 and parts[5] == 'question':
            try:
                result['question_id'] = int(parts[6])
            except (ValueError, IndexError):
                pass

        return result


# Activity name templates (multilingual)
ACTIVITY_NAMES = {
    # Gana Quiz
    'gana/hiragana/gana_to_romaji': {'ko': '히라가나 → 로마자', 'en': 'Hiragana to Romaji'},
    'gana/hiragana/romaji_to_gana_select': {'ko': '로마자 → 히라가나 (선택)', 'en': 'Romaji to Hiragana (Select)'},
    'gana/hiragana/romaji_to_gana_input': {'ko': '로마자 → 히라가나 (입력)', 'en': 'Romaji to Hiragana (Input)'},
    'gana/katakana/gana_to_romaji': {'ko': '가타카나 → 로마자', 'en': 'Katakana to Romaji'},
    'gana/katakana/romaji_to_gana_select': {'ko': '로마자 → 가타카나 (선택)', 'en': 'Romaji to Katakana (Select)'},
    'gana/katakana/romaji_to_gana_input': {'ko': '로마자 → 가타카나 (입력)', 'en': 'Romaji to Katakana (Input)'},
    'gana/all/gana_to_romaji': {'ko': '전체 가나 → 로마자', 'en': 'All Gana to Romaji'},
    'gana/all/romaji_to_gana_select': {'ko': '로마자 → 전체 가나 (선택)', 'en': 'Romaji to All Gana (Select)'},
    'gana/all/romaji_to_gana_input': {'ko': '로마자 → 전체 가나 (입력)', 'en': 'Romaji to All Gana (Input)'},

    # Word Quiz (template - language name will be inserted)
    'word/word_to_native': {'ko': '{language} → 모국어', 'en': '{language} to Native'},
    'word/native_to_word_select': {'ko': '모국어 → {language} (선택)', 'en': 'Native to {language} (Select)'},
    'word/native_to_word_input': {'ko': '모국어 → {language} (입력)', 'en': 'Native to {language} (Input)'},
}


def get_activity_name(category: str, subcategory: str, quiz_type: str, language_name: str = None, lang: str = 'ko') -> str:
    """
    Get the display name for an activity.

    Args:
        category: 'gana' or 'word'
        subcategory: character_set for gana, language_code for word
        quiz_type: The quiz type
        language_name: Language name for word quizzes (e.g., '스페인어')
        lang: Display language ('ko' or 'en')

    Returns:
        Activity display name
    """
    if category == 'gana':
        key = f"gana/{subcategory}/{quiz_type}"
        names = ACTIVITY_NAMES.get(key, {})
        return names.get(lang, f"{subcategory} {quiz_type}")
    elif category == 'word':
        key = f"word/{quiz_type}"
        names = ACTIVITY_NAMES.get(key, {})
        template = names.get(lang, f"{{language}} {quiz_type}")
        return template.format(language=language_name or subcategory)

    return f"{category}/{subcategory}/{quiz_type}"
