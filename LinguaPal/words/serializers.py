from rest_framework import serializers
from .models import (
    Word, WordTranslation, Example, ExampleTranslation,
    PartOfSpeech, WordCategory,
    GanaQuiz, GanaQuizQuestion, UserGanaStats,
    GanaCharacterSet, GanaQuizType, GanaQuizQuestionCount,
    WordQuiz, WordQuizQuestion, UserWordStats,
    WordQuizType, WordQuizQuestionCount,
    FlashcardSession, FlashcardRecord
)
from accounts.models import Language


# =============================================================================
# 기본 Serializers
# =============================================================================

class ExampleTranslationSerializer(serializers.ModelSerializer):
    """예문 번역 Serializer"""
    language_code = serializers.CharField(source='language.code', read_only=True)
    language_name = serializers.CharField(source='language.name_ko', read_only=True)

    class Meta:
        model = ExampleTranslation
        fields = ['id', 'language', 'language_code', 'language_name', 'translated_sentence']
        read_only_fields = ['id']


class ExampleSerializer(serializers.ModelSerializer):
    """예문 Serializer"""
    translations = ExampleTranslationSerializer(many=True, read_only=True)

    class Meta:
        model = Example
        fields = ['id', 'sentence', 'highlight_indices', 'translations']
        read_only_fields = ['id']


class WordTranslationSerializer(serializers.ModelSerializer):
    """단어 번역 Serializer"""
    language_code = serializers.CharField(source='language.code', read_only=True)
    language_name = serializers.CharField(source='language.name_ko', read_only=True)

    class Meta:
        model = WordTranslation
        fields = ['id', 'language', 'language_code', 'language_name', 'translated_text', 'notes']
        read_only_fields = ['id']


class WordSerializer(serializers.ModelSerializer):
    """단어 Serializer (조회용)"""
    language_code = serializers.CharField(source='language.code', read_only=True)
    language_name = serializers.CharField(source='language.name_ko', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    part_of_speech_display = serializers.CharField(source='get_part_of_speech_display', read_only=True)
    translations = WordTranslationSerializer(many=True, read_only=True)
    examples = ExampleSerializer(many=True, read_only=True)

    class Meta:
        model = Word
        fields = [
            'id', 'language', 'language_code', 'language_name',
            'category', 'category_display',
            'text', 'part_of_speech', 'part_of_speech_display',
            'pronunciation', 'audio_url', 'grammar',
            'order', 'difficulty_level', 'is_active',
            'translations', 'examples',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# =============================================================================
# Admin API용 Serializers (생성/수정)
# =============================================================================

class ExampleTranslationCreateSerializer(serializers.ModelSerializer):
    """예문 번역 생성 Serializer"""
    class Meta:
        model = ExampleTranslation
        fields = ['language', 'translated_sentence']


class ExampleCreateSerializer(serializers.ModelSerializer):
    """예문 생성 Serializer"""
    translations = ExampleTranslationCreateSerializer(many=True, required=False)

    class Meta:
        model = Example
        fields = ['sentence', 'highlight_indices', 'translations']

    def create(self, validated_data):
        translations_data = validated_data.pop('translations', [])
        example = Example.objects.create(**validated_data)

        for trans_data in translations_data:
            ExampleTranslation.objects.create(example=example, **trans_data)

        return example


class WordTranslationCreateSerializer(serializers.ModelSerializer):
    """단어 번역 생성 Serializer"""
    notes = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')

    class Meta:
        model = WordTranslation
        fields = ['language', 'translated_text', 'notes']

    def validate_notes(self, value):
        if value is None:
            return ''
        return value


class WordCreateSerializer(serializers.ModelSerializer):
    """단어 생성 Serializer"""
    translations = WordTranslationCreateSerializer(many=True, required=False)
    examples = ExampleCreateSerializer(many=True, required=False)
    pronunciation = serializers.CharField(required=False, allow_blank=True, allow_null=True, default='')
    audio_url = serializers.URLField(required=False, allow_blank=True, allow_null=True, default='')
    grammar = serializers.JSONField(required=False, allow_null=True, default=dict)

    class Meta:
        model = Word
        fields = [
            'language', 'category', 'text', 'part_of_speech',
            'pronunciation', 'audio_url', 'grammar',
            'order', 'difficulty_level', 'is_active',
            'translations', 'examples'
        ]

    def validate_difficulty_level(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('난이도는 1~5 사이여야 합니다.')
        return value

    def validate_pronunciation(self, value):
        if value is None:
            return ''
        return value

    def validate_audio_url(self, value):
        if value is None:
            return ''
        return value

    def validate_grammar(self, value):
        if value is None:
            return {}
        if not isinstance(value, dict):
            raise serializers.ValidationError('grammar는 JSON 객체여야 합니다.')
        return value

    def create(self, validated_data):
        translations_data = validated_data.pop('translations', [])
        examples_data = validated_data.pop('examples', [])

        word = Word.objects.create(**validated_data)

        # 번역 생성
        for trans_data in translations_data:
            WordTranslation.objects.create(word=word, **trans_data)

        # 예문 생성
        for example_data in examples_data:
            example_translations = example_data.pop('translations', [])
            example = Example.objects.create(word=word, **example_data)

            for ex_trans_data in example_translations:
                ExampleTranslation.objects.create(example=example, **ex_trans_data)

        return word


class WordUpdateSerializer(serializers.ModelSerializer):
    """단어 수정 Serializer"""
    class Meta:
        model = Word
        fields = [
            'category', 'text', 'part_of_speech',
            'pronunciation', 'audio_url', 'grammar',
            'order', 'difficulty_level', 'is_active'
        ]

    def validate_difficulty_level(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError('난이도는 1~5 사이여야 합니다.')
        return value


# =============================================================================
# 목록 조회용 간소화 Serializer
# =============================================================================

class WordListSerializer(serializers.ModelSerializer):
    """단어 목록 Serializer (간소화)"""
    language_code = serializers.CharField(source='language.code', read_only=True)
    category_display = serializers.CharField(source='get_category_display', read_only=True)
    part_of_speech_display = serializers.CharField(source='get_part_of_speech_display', read_only=True)
    translation_count = serializers.SerializerMethodField()
    example_count = serializers.SerializerMethodField()

    class Meta:
        model = Word
        fields = [
            'id', 'language', 'language_code',
            'category', 'category_display',
            'text', 'part_of_speech', 'part_of_speech_display',
            'order', 'difficulty_level', 'is_active',
            'translation_count', 'example_count',
            'created_at'
        ]

    def get_translation_count(self, obj):
        return obj.translations.count()

    def get_example_count(self, obj):
        return obj.examples.count()


# =============================================================================
# 퀴즈 API Serializers
# =============================================================================

class GanaQuizStartRequestSerializer(serializers.Serializer):
    """퀴즈 시작 요청 Serializer"""
    character_set = serializers.ChoiceField(
        choices=GanaCharacterSet.choices,
        help_text='문자 세트: hiragana, katakana, all'
    )
    quiz_type = serializers.ChoiceField(
        choices=GanaQuizType.choices,
        help_text='퀴즈 유형: gana_to_romaji, romaji_to_gana_select, romaji_to_gana_input'
    )
    question_count = serializers.ChoiceField(
        choices=GanaQuizQuestionCount.choices,
        help_text='문제 수: 10, 25, 0(전체)'
    )


class GanaQuizQuestionSerializer(serializers.ModelSerializer):
    """퀴즈 문제 Serializer (출제용)"""
    question = serializers.SerializerMethodField()
    correct_answer = serializers.SerializerMethodField()

    class Meta:
        model = GanaQuizQuestion
        fields = ['id', 'question_number', 'question', 'choices', 'user_answer', 'is_correct', 'correct_answer', 'answered_at']

    def get_question(self, obj):
        """문제 내용 반환 (퀴즈 유형에 따라)"""
        if obj.quiz.quiz_type == GanaQuizType.GANA_TO_ROMAJI:
            return obj.word.text  # 가나 문자 보여주기
        else:
            return obj.word.pronunciation  # 로마자 보여주기

    def get_correct_answer(self, obj):
        """정답 반환 (퀴즈 완료 후에만)"""
        if obj.quiz.is_completed or obj.is_correct is not None:
            return obj.correct_answer
        return None


class GanaQuizQuestionCurrentSerializer(serializers.ModelSerializer):
    """현재 문제 Serializer (정답 숨김)"""
    question = serializers.SerializerMethodField()

    class Meta:
        model = GanaQuizQuestion
        fields = ['id', 'question_number', 'question', 'choices']

    def get_question(self, obj):
        if obj.quiz.quiz_type == GanaQuizType.GANA_TO_ROMAJI:
            return obj.word.text
        else:
            return obj.word.pronunciation


class GanaQuizSerializer(serializers.ModelSerializer):
    """퀴즈 세션 Serializer"""
    character_set_display = serializers.CharField(source='get_character_set_display', read_only=True)
    quiz_type_display = serializers.CharField(source='get_quiz_type_display', read_only=True)
    score_percentage = serializers.FloatField(read_only=True)
    questions = GanaQuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = GanaQuiz
        fields = [
            'id', 'character_set', 'character_set_display',
            'quiz_type', 'quiz_type_display',
            'question_count_setting', 'total_questions',
            'correct_count', 'current_question',
            'is_completed', 'score_percentage',
            'started_at', 'completed_at',
            'questions'
        ]


class GanaQuizListSerializer(serializers.ModelSerializer):
    """퀴즈 목록 Serializer (간소화)"""
    character_set_display = serializers.CharField(source='get_character_set_display', read_only=True)
    quiz_type_display = serializers.CharField(source='get_quiz_type_display', read_only=True)
    score_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = GanaQuiz
        fields = [
            'id', 'character_set', 'character_set_display',
            'quiz_type', 'quiz_type_display',
            'total_questions', 'correct_count',
            'is_completed', 'score_percentage',
            'started_at', 'completed_at'
        ]


class GanaQuizAnswerRequestSerializer(serializers.Serializer):
    """퀴즈 답변 요청 Serializer"""
    question_id = serializers.IntegerField(help_text='문제 ID')
    answer = serializers.CharField(help_text='사용자 답변')


class GanaQuizAnswerResponseSerializer(serializers.Serializer):
    """퀴즈 답변 응답 Serializer"""
    is_correct = serializers.BooleanField()
    correct_answer = serializers.CharField()
    user_answer = serializers.CharField()
    next_question = GanaQuizQuestionCurrentSerializer(allow_null=True)
    quiz_completed = serializers.BooleanField()
    current_score = serializers.IntegerField()
    total_answered = serializers.IntegerField()


class UserGanaStatsSerializer(serializers.ModelSerializer):
    """사용자 가나 통계 Serializer"""
    character = serializers.CharField(source='word.text', read_only=True)
    pronunciation = serializers.CharField(source='word.pronunciation', read_only=True)
    category = serializers.CharField(source='word.category', read_only=True)
    accuracy = serializers.FloatField(read_only=True)

    class Meta:
        model = UserGanaStats
        fields = [
            'id', 'character', 'pronunciation', 'category',
            'total_attempts', 'correct_count', 'incorrect_count',
            'accuracy', 'last_attempted_at', 'last_correct_at'
        ]


class UserGanaStatsSummarySerializer(serializers.Serializer):
    """사용자 가나 통계 요약 Serializer"""
    total_quizzes = serializers.IntegerField()
    completed_quizzes = serializers.IntegerField()
    total_questions_answered = serializers.IntegerField()
    total_correct = serializers.IntegerField()
    overall_accuracy = serializers.FloatField()
    hiragana_stats = serializers.DictField()
    katakana_stats = serializers.DictField()
    weakest_characters = UserGanaStatsSerializer(many=True)
    strongest_characters = UserGanaStatsSerializer(many=True)


# =============================================================================
# 단어 퀴즈 API Serializers
# =============================================================================

class WordQuizStartRequestSerializer(serializers.Serializer):
    """단어 퀴즈 시작 요청 Serializer"""
    learning_language = serializers.CharField(
        help_text='배우고자 하는 언어 코드 (예: ja, en, es)'
    )
    quiz_type = serializers.ChoiceField(
        choices=WordQuizType.choices,
        help_text='퀴즈 유형: word_to_native, native_to_word_select, native_to_word_input'
    )
    question_count = serializers.IntegerField(
        help_text='문제 수: 10, 25, 0(전체)'
    )

    def validate_learning_language(self, value):
        try:
            language = Language.objects.get(code=value)
            return language.id
        except Language.DoesNotExist:
            raise serializers.ValidationError(f'존재하지 않는 언어 코드입니다: {value}')


class WordQuizQuestionSerializer(serializers.ModelSerializer):
    """단어 퀴즈 문제 Serializer"""
    question = serializers.SerializerMethodField()
    correct_answer = serializers.SerializerMethodField()

    class Meta:
        model = WordQuizQuestion
        fields = ['id', 'question_number', 'question', 'choices', 'user_answer', 'is_correct', 'correct_answer', 'answered_at']

    def get_question(self, obj):
        """문제 내용 반환 (퀴즈 유형에 따라)"""
        if obj.quiz.quiz_type == WordQuizType.WORD_TO_NATIVE:
            return obj.word.text  # 외국어 단어 보여주기
        else:
            # 모국어 뜻 보여주기
            translation = obj.word.translations.filter(language=obj.quiz.native_language).first()
            return translation.translated_text if translation else obj.word.text

    def get_correct_answer(self, obj):
        """정답 반환 (퀴즈 완료 후에만)"""
        if obj.quiz.is_completed or obj.is_correct is not None:
            return obj.get_correct_answer(obj.quiz.native_language)
        return None


class WordQuizQuestionCurrentSerializer(serializers.ModelSerializer):
    """현재 문제 Serializer (정답 숨김)"""
    question = serializers.SerializerMethodField()

    class Meta:
        model = WordQuizQuestion
        fields = ['id', 'question_number', 'question', 'choices']

    def get_question(self, obj):
        if obj.quiz.quiz_type == WordQuizType.WORD_TO_NATIVE:
            return obj.word.text
        else:
            translation = obj.word.translations.filter(language=obj.quiz.native_language).first()
            return translation.translated_text if translation else obj.word.text


class WordQuizSerializer(serializers.ModelSerializer):
    """단어 퀴즈 세션 Serializer"""
    learning_language_code = serializers.CharField(source='learning_language.code', read_only=True)
    learning_language_name = serializers.CharField(source='learning_language.name_ko', read_only=True)
    native_language_code = serializers.CharField(source='native_language.code', read_only=True)
    native_language_name = serializers.CharField(source='native_language.name_ko', read_only=True)
    quiz_type_display = serializers.CharField(source='get_quiz_type_display', read_only=True)
    score_percentage = serializers.FloatField(read_only=True)
    questions = WordQuizQuestionSerializer(many=True, read_only=True)

    class Meta:
        model = WordQuiz
        fields = [
            'id', 'learning_language', 'learning_language_code', 'learning_language_name',
            'native_language', 'native_language_code', 'native_language_name',
            'quiz_type', 'quiz_type_display',
            'question_count_setting', 'total_questions',
            'correct_count', 'current_question',
            'is_completed', 'score_percentage',
            'started_at', 'completed_at',
            'questions'
        ]


class WordQuizListSerializer(serializers.ModelSerializer):
    """단어 퀴즈 목록 Serializer (간소화)"""
    learning_language_code = serializers.CharField(source='learning_language.code', read_only=True)
    learning_language_name = serializers.CharField(source='learning_language.name_ko', read_only=True)
    quiz_type_display = serializers.CharField(source='get_quiz_type_display', read_only=True)
    score_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = WordQuiz
        fields = [
            'id', 'learning_language', 'learning_language_code', 'learning_language_name',
            'quiz_type', 'quiz_type_display',
            'total_questions', 'correct_count',
            'is_completed', 'score_percentage',
            'started_at', 'completed_at'
        ]


class WordQuizAnswerRequestSerializer(serializers.Serializer):
    """단어 퀴즈 답변 요청 Serializer"""
    question_id = serializers.IntegerField(help_text='문제 ID')
    answer = serializers.CharField(help_text='사용자 답변')


class WordQuizAnswerResponseSerializer(serializers.Serializer):
    """단어 퀴즈 답변 응답 Serializer"""
    is_correct = serializers.BooleanField()
    correct_answer = serializers.CharField()
    user_answer = serializers.CharField()
    next_question = WordQuizQuestionCurrentSerializer(allow_null=True)
    quiz_completed = serializers.BooleanField()
    current_score = serializers.IntegerField()
    total_answered = serializers.IntegerField()


class UserWordStatsSerializer(serializers.ModelSerializer):
    """사용자 단어 통계 Serializer"""
    word_text = serializers.CharField(source='word.text', read_only=True)
    word_language = serializers.CharField(source='word.language.name_ko', read_only=True)
    accuracy = serializers.FloatField(read_only=True)

    class Meta:
        model = UserWordStats
        fields = [
            'id', 'word_text', 'word_language',
            'total_attempts', 'correct_count', 'incorrect_count',
            'accuracy', 'last_attempted_at', 'last_correct_at'
        ]


class WordQuizStatsSummarySerializer(serializers.Serializer):
    """사용자 단어 퀴즈 통계 요약 Serializer"""
    total_quizzes = serializers.IntegerField()
    completed_quizzes = serializers.IntegerField()
    total_questions_answered = serializers.IntegerField()
    total_correct = serializers.IntegerField()
    overall_accuracy = serializers.FloatField()
    language_stats = serializers.DictField()
    weakest_words = UserWordStatsSerializer(many=True)
    strongest_words = UserWordStatsSerializer(many=True)


# =============================================================================
# Flashcard Serializers
# =============================================================================

class FlashcardWordSerializer(serializers.Serializer):
    """플래시카드용 단어 Serializer (프론트엔드 형식에 맞춤)"""
    id = serializers.IntegerField()
    word_text = serializers.CharField(source='text')
    word_pronunciation = serializers.CharField(source='pronunciation', allow_null=True)
    category = serializers.CharField()
    difficulty = serializers.IntegerField(source='difficulty_level')
    translation = serializers.SerializerMethodField()
    example = serializers.SerializerMethodField()
    example_translation = serializers.SerializerMethodField()
    example_highlight = serializers.SerializerMethodField()
    example_translation_highlight = serializers.SerializerMethodField()

    def get_translation(self, obj):
        """사용자 모국어로 된 번역 반환"""
        native_language_id = self.context.get('native_language_id')
        if native_language_id:
            trans = obj.translations.filter(language_id=native_language_id).first()
            if trans:
                return trans.translated_text
        # 첫 번째 번역이라도 반환
        first_trans = obj.translations.first()
        return first_trans.translated_text if first_trans else None

    def get_example(self, obj):
        """첫 번째 예문 반환"""
        example = obj.examples.first()
        return example.sentence if example else None

    def get_example_translation(self, obj):
        """예문의 번역 반환"""
        native_language_id = self.context.get('native_language_id')
        example = obj.examples.first()
        if example and native_language_id:
            trans = example.translations.filter(language_id=native_language_id).first()
            if trans:
                return trans.translated_sentence
        return None

    def get_example_highlight(self, obj):
        """예문의 하이라이트 인덱스 반환"""
        example = obj.examples.first()
        return example.highlight_indices if example else None

    def get_example_translation_highlight(self, obj):
        """예문 번역의 하이라이트 인덱스 반환"""
        native_language_id = self.context.get('native_language_id')
        example = obj.examples.first()
        if example and native_language_id:
            trans = example.translations.filter(language_id=native_language_id).first()
            if trans:
                return trans.highlight_indices
        return None


class FlashcardRecordSerializer(serializers.ModelSerializer):
    """플래시카드 기록 Serializer"""
    word = serializers.SerializerMethodField()

    class Meta:
        model = FlashcardRecord
        fields = ['id', 'word', 'card_index', 'is_known', 'viewed_at', 'answered_at']

    def get_word(self, obj):
        """단어 정보를 사용자 컨텍스트와 함께 직렬화"""
        return FlashcardWordSerializer(
            obj.word,
            context=self.context
        ).data


class FlashcardSessionSerializer(serializers.ModelSerializer):
    """플래시카드 세션 Serializer"""
    learning_language_code = serializers.CharField(source='learning_language.code', read_only=True)
    learning_language_name = serializers.CharField(source='learning_language.name_ko', read_only=True)
    progress_percentage = serializers.FloatField(read_only=True)

    class Meta:
        model = FlashcardSession
        fields = [
            'id', 'learning_language', 'learning_language_code', 'learning_language_name',
            'category', 'total_cards', 'known_count', 'unknown_count',
            'current_index', 'is_completed', 'progress_percentage',
            'started_at', 'completed_at'
        ]


class FlashcardSessionDetailSerializer(FlashcardSessionSerializer):
    """플래시카드 세션 상세 Serializer"""
    records = FlashcardRecordSerializer(many=True, read_only=True)

    class Meta(FlashcardSessionSerializer.Meta):
        fields = FlashcardSessionSerializer.Meta.fields + ['records']


class FlashcardStartRequestSerializer(serializers.Serializer):
    """플래시카드 시작 요청 Serializer"""
    learning_language = serializers.CharField(help_text='학습할 언어 코드 (예: ja, ko, en)')
    category = serializers.ChoiceField(
        choices=[('', '전체')] + list(WordCategory.choices),
        required=False,
        allow_blank=True,
        help_text='카테고리 (빈값이면 전체)'
    )
    card_count = serializers.IntegerField(
        min_value=5,
        max_value=100,
        default=20,
        help_text='카드 수 (5-100)'
    )

    def validate_learning_language(self, value):
        """언어 코드를 언어 ID로 변환"""
        from accounts.models import Language
        try:
            language = Language.objects.get(code=value)
            return language.id
        except Language.DoesNotExist:
            raise serializers.ValidationError('존재하지 않는 언어 코드입니다.')


class FlashcardAnswerRequestSerializer(serializers.Serializer):
    """플래시카드 응답 요청 Serializer"""
    record_id = serializers.IntegerField(help_text='플래시카드 기록 ID')
    is_known = serializers.BooleanField(help_text='알아요 여부')
