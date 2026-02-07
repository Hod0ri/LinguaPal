from django.db import models
from django.conf import settings
from accounts.models import Language


class WordCategory(models.TextChoices):
    """단어 카테고리"""
    WORD = 'word', '단어'
    HIRAGANA = 'hiragana', '히라가나'
    KATAKANA = 'katakana', '가타카나'
    ALPHABET = 'alphabet', '알파벳'


class PartOfSpeech(models.TextChoices):
    """품사"""
    NOUN = 'noun', '명사'
    VERB = 'verb', '동사'
    ADJECTIVE = 'adjective', '형용사'
    ADVERB = 'adverb', '부사'
    PRONOUN = 'pronoun', '대명사'
    PREPOSITION = 'preposition', '전치사'
    CONJUNCTION = 'conjunction', '접속사'
    INTERJECTION = 'interjection', '감탄사'
    ARTICLE = 'article', '관사'
    DETERMINER = 'determiner', '한정사'
    NUMERAL = 'numeral', '수사'
    PARTICLE = 'particle', '조사/불변화사'
    PHRASE = 'phrase', '구/숙어'
    CHARACTER = 'character', '문자'
    OTHER = 'other', '기타'


class Word(models.Model):
    """단어 모델"""
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='words',
        verbose_name='언어'
    )
    category = models.CharField(
        max_length=20,
        choices=WordCategory.choices,
        default=WordCategory.WORD,
        verbose_name='카테고리',
        help_text='단어, 히라가나, 가타카나, 한자 등'
    )
    text = models.CharField(
        max_length=200,
        verbose_name='단어'
    )
    part_of_speech = models.CharField(
        max_length=20,
        choices=PartOfSpeech.choices,
        default=PartOfSpeech.OTHER,
        verbose_name='품사'
    )
    pronunciation = models.CharField(
        max_length=200,
        blank=True,
        verbose_name='발음 기호'
    )
    audio_url = models.URLField(
        blank=True,
        verbose_name='발음 파일 URL'
    )
    grammar = models.JSONField(
        default=dict,
        blank=True,
        verbose_name='문법 속성',
        help_text='동사변화, 성별, 복수형, 로마자(romanji), 행(row) 등'
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name='정렬 순서',
        help_text='문자 학습 시 순서 지정용'
    )
    difficulty_level = models.PositiveSmallIntegerField(
        default=1,
        verbose_name='난이도',
        help_text='1(초급) ~ 5(고급)'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='활성화'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '단어'
        verbose_name_plural = '단어 목록'
        ordering = ['order', '-created_at']
        indexes = [
            models.Index(fields=['language', 'text']),
            models.Index(fields=['category']),
            models.Index(fields=['part_of_speech']),
            models.Index(fields=['difficulty_level']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['language', 'text', 'category'],
                name='unique_word_per_language_category'
            )
        ]

    def __str__(self):
        return f'{self.text} ({self.language.code})'


class WordTranslation(models.Model):
    """단어 번역 모델"""
    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name='translations',
        verbose_name='원본 단어'
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='word_translations',
        verbose_name='번역 언어'
    )
    translated_text = models.CharField(
        max_length=500,
        verbose_name='번역'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='뉘앙스/설명',
        help_text='번역에 대한 추가 설명이나 뉘앙스'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '단어 번역'
        verbose_name_plural = '단어 번역 목록'
        constraints = [
            models.UniqueConstraint(
                fields=['word', 'language'],
                name='unique_translation_per_language'
            )
        ]

    def __str__(self):
        return f'{self.word.text} → {self.translated_text} ({self.language.code})'


class Example(models.Model):
    """예문 모델"""
    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name='examples',
        verbose_name='단어'
    )
    sentence = models.TextField(
        verbose_name='예문'
    )
    highlight_indices = models.JSONField(
        default=list,
        blank=True,
        verbose_name='하이라이트 위치',
        help_text='예문에서 단어가 나타나는 위치 [start, end]'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '예문'
        verbose_name_plural = '예문 목록'

    def __str__(self):
        return f'{self.word.text}: {self.sentence[:50]}...'


class ExampleTranslation(models.Model):
    """예문 번역 모델"""
    example = models.ForeignKey(
        Example,
        on_delete=models.CASCADE,
        related_name='translations',
        verbose_name='원본 예문'
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='example_translations',
        verbose_name='번역 언어'
    )
    translated_sentence = models.TextField(
        verbose_name='번역된 예문'
    )
    highlight_indices = models.JSONField(
        default=list,
        blank=True,
        verbose_name='하이라이트 인덱스',
        help_text='번역에서 단어 뜻에 해당하는 부분의 [시작, 끝] 인덱스'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '예문 번역'
        verbose_name_plural = '예문 번역 목록'
        constraints = [
            models.UniqueConstraint(
                fields=['example', 'language'],
                name='unique_example_translation_per_language'
            )
        ]

    def __str__(self):
        return f'{self.example.sentence[:30]}... → {self.translated_sentence[:30]}...'


# =============================================================================
# 퀴즈 관련 모델
# =============================================================================

class GanaCharacterSet(models.TextChoices):
    """가나 문자 세트"""
    HIRAGANA = 'hiragana', '히라가나'
    KATAKANA = 'katakana', '가타카나'
    ALL = 'all', '전체'


class GanaQuizType(models.TextChoices):
    """가나 퀴즈 유형"""
    GANA_TO_ROMAJI = 'gana_to_romaji', '가나 → 로마자'
    ROMAJI_TO_GANA_SELECT = 'romaji_to_gana_select', '로마자 → 가나 (선택)'
    ROMAJI_TO_GANA_INPUT = 'romaji_to_gana_input', '로마자 → 가나 (입력)'


class GanaQuizQuestionCount(models.IntegerChoices):
    """퀴즈 문제 수"""
    TEN = 10, '10문제'
    TWENTY_FIVE = 25, '25문제'
    ALL = 0, '전체'  # 0은 전체를 의미


class GanaQuiz(models.Model):
    """가나 퀴즈 세션"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gana_quizzes',
        verbose_name='사용자'
    )
    character_set = models.CharField(
        max_length=20,
        choices=GanaCharacterSet.choices,
        verbose_name='문자 세트'
    )
    quiz_type = models.CharField(
        max_length=30,
        choices=GanaQuizType.choices,
        verbose_name='퀴즈 유형'
    )
    question_count_setting = models.IntegerField(
        choices=GanaQuizQuestionCount.choices,
        verbose_name='문제 수 설정'
    )
    total_questions = models.PositiveIntegerField(
        verbose_name='총 문제 수',
        help_text='실제 출제된 문제 수'
    )
    correct_count = models.PositiveIntegerField(
        default=0,
        verbose_name='정답 수'
    )
    current_question = models.PositiveIntegerField(
        default=1,
        verbose_name='현재 문제 번호'
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name='완료 여부'
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='시작 시간'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='완료 시간'
    )

    class Meta:
        verbose_name = '가나 퀴즈'
        verbose_name_plural = '가나 퀴즈 목록'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', '-started_at']),
            models.Index(fields=['is_completed']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.get_character_set_display()} {self.get_quiz_type_display()}'

    @property
    def score_percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.correct_count / self.total_questions) * 100, 1)


class GanaQuizQuestion(models.Model):
    """가나 퀴즈 문제/답변 기록"""
    quiz = models.ForeignKey(
        GanaQuiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='퀴즈'
    )
    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name='quiz_questions',
        verbose_name='문자'
    )
    question_number = models.PositiveIntegerField(
        verbose_name='문제 번호'
    )
    choices = models.JSONField(
        default=list,
        blank=True,
        verbose_name='선택지',
        help_text='선택형 문제의 경우 선택지 목록'
    )
    user_answer = models.CharField(
        max_length=100,
        blank=True,
        verbose_name='사용자 답변'
    )
    is_correct = models.BooleanField(
        null=True,
        verbose_name='정답 여부'
    )
    answered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='답변 시간'
    )

    class Meta:
        verbose_name = '퀴즈 문제'
        verbose_name_plural = '퀴즈 문제 목록'
        ordering = ['question_number']
        constraints = [
            models.UniqueConstraint(
                fields=['quiz', 'question_number'],
                name='unique_question_number_per_quiz'
            )
        ]

    def __str__(self):
        return f'Quiz {self.quiz.id} - Q{self.question_number}: {self.word.text}'

    @property
    def correct_answer(self):
        """정답 반환 (퀴즈 유형에 따라)"""
        if self.quiz.quiz_type == GanaQuizType.GANA_TO_ROMAJI:
            return self.word.pronunciation
        else:
            return self.word.text


class UserGanaStats(models.Model):
    """사용자별 가나 문자 통계"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='gana_stats',
        verbose_name='사용자'
    )
    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name='user_stats',
        verbose_name='문자'
    )
    total_attempts = models.PositiveIntegerField(
        default=0,
        verbose_name='총 시도 횟수'
    )
    correct_count = models.PositiveIntegerField(
        default=0,
        verbose_name='정답 횟수'
    )
    incorrect_count = models.PositiveIntegerField(
        default=0,
        verbose_name='오답 횟수'
    )
    last_attempted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='마지막 시도 시간'
    )
    last_correct_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='마지막 정답 시간'
    )

    class Meta:
        verbose_name = '사용자 가나 통계'
        verbose_name_plural = '사용자 가나 통계 목록'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'word'],
                name='unique_user_word_stats'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'word']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.word.text}: {self.correct_count}/{self.total_attempts}'

    @property
    def accuracy(self):
        """정답률"""
        if self.total_attempts == 0:
            return 0
        return round((self.correct_count / self.total_attempts) * 100, 1)


# =============================================================================
# 단어 퀴즈 관련 모델
# =============================================================================

class WordQuizType(models.TextChoices):
    """단어 퀴즈 유형"""
    WORD_TO_NATIVE = 'word_to_native', '단어 → 모국어'
    NATIVE_TO_WORD_SELECT = 'native_to_word_select', '모국어 → 단어 (선택)'
    NATIVE_TO_WORD_INPUT = 'native_to_word_input', '모국어 → 단어 (입력)'
    EXAMPLE_FILL_IN_BLANK = 'example_fill_in_blank', '예문 빈칸 채우기'
    MIXED = 'mixed', '혼합 문제'


class WordQuizQuestionCount(models.IntegerChoices):
    """단어 퀴즈 문제 수"""
    TEN = 10, '10문제'
    TWENTY_FIVE = 25, '25문제'
    ALL = 0, '전체'


class WordQuiz(models.Model):
    """단어 퀴즈 세션"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='word_quizzes',
        verbose_name='사용자'
    )
    learning_language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='word_quizzes_as_learning',
        verbose_name='학습 언어'
    )
    native_language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='word_quizzes_as_native',
        verbose_name='모국어'
    )
    quiz_type = models.CharField(
        max_length=30,
        choices=WordQuizType.choices,
        verbose_name='퀴즈 유형'
    )
    question_count_setting = models.IntegerField(
        choices=WordQuizQuestionCount.choices,
        verbose_name='문제 수 설정'
    )
    total_questions = models.PositiveIntegerField(
        verbose_name='총 문제 수',
        help_text='실제 출제된 문제 수'
    )
    correct_count = models.PositiveIntegerField(
        default=0,
        verbose_name='정답 수'
    )
    current_question = models.PositiveIntegerField(
        default=1,
        verbose_name='현재 문제 번호'
    )
    is_completed = models.BooleanField(
        default=False,
        verbose_name='완료 여부'
    )
    started_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='시작 시간'
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='완료 시간'
    )

    class Meta:
        verbose_name = '단어 퀴즈'
        verbose_name_plural = '단어 퀴즈 목록'
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', '-started_at']),
            models.Index(fields=['is_completed']),
            models.Index(fields=['user', 'learning_language']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.learning_language.code} {self.get_quiz_type_display()}'

    @property
    def score_percentage(self):
        if self.total_questions == 0:
            return 0
        return round((self.correct_count / self.total_questions) * 100, 1)


class WordQuizQuestion(models.Model):
    """단어 퀴즈 문제/답변 기록"""
    quiz = models.ForeignKey(
        WordQuiz,
        on_delete=models.CASCADE,
        related_name='questions',
        verbose_name='퀴즈'
    )
    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name='word_quiz_questions',
        verbose_name='단어'
    )
    question_number = models.PositiveIntegerField(
        verbose_name='문제 번호'
    )
    choices = models.JSONField(
        default=list,
        blank=True,
        verbose_name='선택지',
        help_text='선택형 문제의 경우 선택지 목록'
    )
    user_answer = models.CharField(
        max_length=500,
        blank=True,
        verbose_name='사용자 답변'
    )
    is_correct = models.BooleanField(
        null=True,
        verbose_name='정답 여부'
    )
    answered_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='답변 시간'
    )

    class Meta:
        verbose_name = '단어 퀴즈 문제'
        verbose_name_plural = '단어 퀴즈 문제 목록'
        ordering = ['question_number']
        constraints = [
            models.UniqueConstraint(
                fields=['quiz', 'question_number'],
                name='unique_word_question_number_per_quiz'
            )
        ]

    def __str__(self):
        return f'WordQuiz {self.quiz.id} - Q{self.question_number}: {self.word.text}'

    def get_correct_answer(self, native_language):
        """정답 반환 (퀴즈 유형에 따라)"""
        quiz_type = self.quiz.quiz_type

        # 혼합 퀴즈인 경우 타입 판단
        if quiz_type == WordQuizType.MIXED:
            if self.word.examples.exists():
                quiz_type = WordQuizType.EXAMPLE_FILL_IN_BLANK
            elif self.choices:
                quiz_type = WordQuizType.NATIVE_TO_WORD_SELECT
            else:
                quiz_type = WordQuizType.WORD_TO_NATIVE  # 기본값

        if quiz_type == WordQuizType.WORD_TO_NATIVE:
            # 단어 보고 모국어 뜻 입력 -> 정답은 번역
            translation = self.word.translations.filter(language=native_language).first()
            return translation.translated_text if translation else ''
        else:
            # 모국어 보고 단어 입력/선택, 예문 빈칸 채우기 -> 정답은 단어 텍스트
            return self.word.text


class UserWordStats(models.Model):
    """사용자별 단어 통계"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='word_stats',
        verbose_name='사용자'
    )
    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name='user_word_stats',
        verbose_name='단어'
    )
    total_attempts = models.PositiveIntegerField(
        default=0,
        verbose_name='총 시도 횟수'
    )
    correct_count = models.PositiveIntegerField(
        default=0,
        verbose_name='정답 횟수'
    )
    incorrect_count = models.PositiveIntegerField(
        default=0,
        verbose_name='오답 횟수'
    )
    last_attempted_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='마지막 시도 시간'
    )
    last_correct_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name='마지막 정답 시간'
    )

    class Meta:
        verbose_name = '사용자 단어 통계'
        verbose_name_plural = '사용자 단어 통계 목록'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'word'],
                name='unique_user_word_word_stats'
            )
        ]
        indexes = [
            models.Index(fields=['user', 'word']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.word.text}: {self.correct_count}/{self.total_attempts}'

    @property
    def accuracy(self):
        """정답률"""
        if self.total_attempts == 0:
            return 0
        return round((self.correct_count / self.total_attempts) * 100, 1)


# =============================================================================
# Flashcard Study Models
# =============================================================================

class FlashcardSession(models.Model):
    """플래시카드 학습 세션"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='flashcard_sessions',
        verbose_name='사용자'
    )
    learning_language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='flashcard_sessions',
        verbose_name='학습 언어'
    )
    category = models.CharField(
        max_length=20,
        choices=WordCategory.choices,
        blank=True,
        verbose_name='카테고리',
        help_text='빈값이면 전체'
    )
    total_cards = models.PositiveIntegerField(default=0, verbose_name='전체 카드 수')
    known_count = models.PositiveIntegerField(default=0, verbose_name='알아요 수')
    unknown_count = models.PositiveIntegerField(default=0, verbose_name='몰라요 수')
    current_index = models.PositiveIntegerField(default=0, verbose_name='현재 카드 인덱스')
    is_completed = models.BooleanField(default=False, verbose_name='완료 여부')
    started_at = models.DateTimeField(auto_now_add=True, verbose_name='시작 시간')
    completed_at = models.DateTimeField(null=True, blank=True, verbose_name='완료 시간')

    class Meta:
        verbose_name = '플래시카드 세션'
        verbose_name_plural = '플래시카드 세션 목록'
        ordering = ['-started_at']

    def __str__(self):
        return f'{self.user.email} - {self.learning_language.code} ({self.known_count}/{self.total_cards})'

    @property
    def progress_percentage(self):
        """진행률"""
        if self.total_cards == 0:
            return 0
        return round(((self.known_count + self.unknown_count) / self.total_cards) * 100, 1)


class FlashcardRecord(models.Model):
    """플래시카드 학습 기록 (카드별)"""
    session = models.ForeignKey(
        FlashcardSession,
        on_delete=models.CASCADE,
        related_name='records',
        verbose_name='세션'
    )
    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name='flashcard_records',
        verbose_name='단어'
    )
    card_index = models.PositiveIntegerField(verbose_name='카드 순서')
    is_known = models.BooleanField(null=True, verbose_name='알아요 여부')
    viewed_at = models.DateTimeField(null=True, blank=True, verbose_name='조회 시간')
    answered_at = models.DateTimeField(null=True, blank=True, verbose_name='응답 시간')

    class Meta:
        verbose_name = '플래시카드 기록'
        verbose_name_plural = '플래시카드 기록 목록'
        ordering = ['card_index']
        constraints = [
            models.UniqueConstraint(
                fields=['session', 'word'],
                name='unique_session_word'
            )
        ]

    def __str__(self):
        status = '알아요' if self.is_known else ('몰라요' if self.is_known is False else '미응답')
        return f'{self.word.text} - {status}'


# =============================================================================
# 단어장 관련 모델
# =============================================================================

class Vocabulary(models.Model):
    """사용자 단어장"""
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='vocabularies',
        verbose_name='사용자'
    )
    name = models.CharField(
        max_length=100,
        verbose_name='단어장 이름'
    )
    description = models.TextField(
        blank=True,
        verbose_name='설명'
    )
    language = models.ForeignKey(
        Language,
        on_delete=models.CASCADE,
        related_name='vocabularies',
        verbose_name='언어',
        help_text='이 단어장의 주요 학습 언어'
    )
    words = models.ManyToManyField(
        Word,
        through='VocabularyWord',
        related_name='vocabularies',
        verbose_name='단어 목록'
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name='활성화'
    )
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '단어장'
        verbose_name_plural = '단어장 목록'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'language']),
        ]

    def __str__(self):
        return f'{self.user.email} - {self.name}'


class VocabularyWord(models.Model):
    """단어장에 포함된 단어"""
    vocabulary = models.ForeignKey(
        Vocabulary,
        on_delete=models.CASCADE,
        related_name='vocabulary_words',
        verbose_name='단어장'
    )
    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name='in_vocabularies',
        verbose_name='단어'
    )
    notes = models.TextField(
        blank=True,
        verbose_name='개인 메모',
        help_text='이 단어에 대한 개인적인 메모나 암기 팁'
    )
    added_at = models.DateTimeField(auto_now_add=True, verbose_name='추가일')

    class Meta:
        verbose_name = '단어장 단어'
        verbose_name_plural = '단어장 단어 목록'
        ordering = ['-added_at']
        constraints = [
            models.UniqueConstraint(
                fields=['vocabulary', 'word'],
                name='unique_vocabulary_word'
            )
        ]
        indexes = [
            models.Index(fields=['vocabulary', 'word']),
        ]

    def __str__(self):
        return f'{self.vocabulary.name} - {self.word.text}'
