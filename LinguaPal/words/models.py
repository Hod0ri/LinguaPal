from django.db import models
from accounts.models import Language


class WordCategory(models.TextChoices):
    """단어 카테고리"""
    WORD = 'word', '단어'
    HIRAGANA = 'hiragana', '히라가나'
    KATAKANA = 'katakana', '가타카나'
    KANJI = 'kanji', '한자'
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
