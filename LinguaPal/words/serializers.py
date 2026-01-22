from rest_framework import serializers
from .models import Word, WordTranslation, Example, ExampleTranslation, PartOfSpeech, WordCategory
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
