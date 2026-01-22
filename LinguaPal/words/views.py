from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from accounts.permissions import IsStaffRole
from accounts.utils import APIResponse, ErrorCode
from .models import Word, WordTranslation, Example, ExampleTranslation
from .serializers import (
    WordSerializer,
    WordListSerializer,
    WordCreateSerializer,
    WordUpdateSerializer,
    WordTranslationSerializer,
    WordTranslationCreateSerializer,
    ExampleSerializer,
    ExampleCreateSerializer,
    ExampleTranslationSerializer,
    ExampleTranslationCreateSerializer,
)


# =============================================================================
# Word Admin API
# =============================================================================

@extend_schema(
    tags=['관리자 - 단어'],
    summary="단어 목록 조회",
    description="등록된 단어 목록을 조회합니다. 언어, 카테고리, 품사, 난이도로 필터링 가능합니다.",
    parameters=[
        OpenApiParameter(name='language', description='언어 ID', required=False, type=int),
        OpenApiParameter(name='category', description='카테고리 (word, hiragana, katakana, kanji, alphabet)', required=False, type=str),
        OpenApiParameter(name='part_of_speech', description='품사', required=False, type=str),
        OpenApiParameter(name='difficulty_level', description='난이도 (1-5)', required=False, type=int),
        OpenApiParameter(name='is_active', description='활성화 여부', required=False, type=bool),
        OpenApiParameter(name='search', description='검색어 (단어 텍스트)', required=False, type=str),
    ],
    responses={200: WordListSerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_word_list(request):
    """단어 목록 조회 (Admin/Staff 전용)"""
    queryset = Word.objects.select_related('language').all()

    # 필터링
    language_id = request.query_params.get('language')
    if language_id:
        queryset = queryset.filter(language_id=language_id)

    category = request.query_params.get('category')
    if category:
        queryset = queryset.filter(category=category)

    part_of_speech = request.query_params.get('part_of_speech')
    if part_of_speech:
        queryset = queryset.filter(part_of_speech=part_of_speech)

    difficulty_level = request.query_params.get('difficulty_level')
    if difficulty_level:
        queryset = queryset.filter(difficulty_level=difficulty_level)

    is_active = request.query_params.get('is_active')
    if is_active is not None:
        queryset = queryset.filter(is_active=is_active.lower() == 'true')

    search = request.query_params.get('search')
    if search:
        queryset = queryset.filter(text__icontains=search)

    serializer = WordListSerializer(queryset, many=True)
    return APIResponse.success(
        message='Words retrieved',
        data={
            'words': serializer.data,
            'total_count': queryset.count()
        }
    )


@extend_schema(
    tags=['관리자 - 단어'],
    summary="단어 생성",
    description="새로운 단어를 생성합니다. 번역과 예문도 함께 추가할 수 있습니다.",
    request=WordCreateSerializer,
    responses={201: WordSerializer},
    examples=[
        OpenApiExample(
            'Spanish Noun Example',
            value={
                'language': 1,
                'text': 'libro',
                'part_of_speech': 'noun',
                'pronunciation': '/ˈli.βɾo/',
                'grammar': {
                    'gender': 'masculine',
                    'plural': 'libros',
                    'article': 'el'
                },
                'difficulty_level': 1,
                'translations': [
                    {'language': 2, 'translated_text': '책', 'notes': ''}
                ],
                'examples': [
                    {
                        'sentence': 'El libro está en la mesa.',
                        'highlight_indices': [3, 8],
                        'translations': [
                            {'language': 2, 'translated_sentence': '책이 테이블 위에 있다.'}
                        ]
                    }
                ]
            },
            request_only=True,
        ),
    ]
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_word_create(request):
    """단어 생성 (Admin/Staff 전용)"""
    serializer = WordCreateSerializer(data=request.data)
    if serializer.is_valid():
        word = serializer.save()
        response_serializer = WordSerializer(word)
        return APIResponse.success(
            message='Word created successfully',
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED
        )

    return APIResponse.validation_error(
        errors=serializer.errors,
        message='Validation failed'
    )


@extend_schema(
    tags=['관리자 - 단어'],
    summary="단어 상세 조회",
    description="특정 단어의 상세 정보를 조회합니다. 번역과 예문이 포함됩니다.",
    responses={200: WordSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_word_detail(request, pk):
    """단어 상세 조회 (Admin/Staff 전용)"""
    word = get_object_or_404(Word, pk=pk)
    serializer = WordSerializer(word)
    return APIResponse.success(
        message='Word retrieved',
        data=serializer.data
    )


@extend_schema(
    tags=['관리자 - 단어'],
    summary="단어 수정",
    description="단어의 기본 정보를 수정합니다. 번역/예문은 별도 API로 관리합니다.",
    request=WordUpdateSerializer,
    responses={200: WordSerializer},
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_word_update(request, pk):
    """단어 수정 (Admin/Staff 전용)"""
    word = get_object_or_404(Word, pk=pk)
    serializer = WordUpdateSerializer(word, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        response_serializer = WordSerializer(word)
        return APIResponse.success(
            message='Word updated successfully',
            data=response_serializer.data
        )

    return APIResponse.validation_error(
        errors=serializer.errors,
        message='Validation failed'
    )


@extend_schema(
    tags=['관리자 - 단어'],
    summary="단어 삭제",
    description="단어를 삭제합니다. 관련된 번역과 예문도 함께 삭제됩니다.",
    responses={204: None},
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_word_delete(request, pk):
    """단어 삭제 (Admin/Staff 전용)"""
    word = get_object_or_404(Word, pk=pk)
    word.delete()
    return APIResponse.success(
        message='Word deleted successfully',
        data=None,
        status_code=status.HTTP_204_NO_CONTENT
    )


# =============================================================================
# WordTranslation Admin API
# =============================================================================

@extend_schema(
    tags=['관리자 - 단어 번역'],
    summary="단어 번역 목록 조회",
    description="특정 단어의 번역 목록을 조회합니다.",
    responses={200: WordTranslationSerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_word_translation_list(request, word_id):
    """단어 번역 목록 조회 (Admin/Staff 전용)"""
    word = get_object_or_404(Word, pk=word_id)
    translations = word.translations.select_related('language').all()
    serializer = WordTranslationSerializer(translations, many=True)
    return APIResponse.success(
        message='Translations retrieved',
        data={
            'word_id': word_id,
            'word_text': word.text,
            'translations': serializer.data
        }
    )


@extend_schema(
    tags=['관리자 - 단어 번역'],
    summary="단어 번역 추가",
    description="특정 단어에 새로운 번역을 추가합니다.",
    request=WordTranslationCreateSerializer,
    responses={201: WordTranslationSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_word_translation_create(request, word_id):
    """단어 번역 추가 (Admin/Staff 전용)"""
    word = get_object_or_404(Word, pk=word_id)
    serializer = WordTranslationCreateSerializer(data=request.data)
    if serializer.is_valid():
        translation = serializer.save(word=word)
        response_serializer = WordTranslationSerializer(translation)
        return APIResponse.success(
            message='Translation added successfully',
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED
        )

    return APIResponse.validation_error(
        errors=serializer.errors,
        message='Validation failed'
    )


@extend_schema(
    tags=['관리자 - 단어 번역'],
    summary="단어 번역 수정",
    description="특정 번역을 수정합니다.",
    request=WordTranslationCreateSerializer,
    responses={200: WordTranslationSerializer},
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_word_translation_update(request, word_id, translation_id):
    """단어 번역 수정 (Admin/Staff 전용)"""
    translation = get_object_or_404(WordTranslation, pk=translation_id, word_id=word_id)
    serializer = WordTranslationCreateSerializer(translation, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        response_serializer = WordTranslationSerializer(translation)
        return APIResponse.success(
            message='Translation updated successfully',
            data=response_serializer.data
        )

    return APIResponse.validation_error(
        errors=serializer.errors,
        message='Validation failed'
    )


@extend_schema(
    tags=['관리자 - 단어 번역'],
    summary="단어 번역 삭제",
    description="특정 번역을 삭제합니다.",
    responses={204: None},
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_word_translation_delete(request, word_id, translation_id):
    """단어 번역 삭제 (Admin/Staff 전용)"""
    translation = get_object_or_404(WordTranslation, pk=translation_id, word_id=word_id)
    translation.delete()
    return APIResponse.success(
        message='Translation deleted successfully',
        data=None,
        status_code=status.HTTP_204_NO_CONTENT
    )


# =============================================================================
# Example Admin API
# =============================================================================

@extend_schema(
    tags=['관리자 - 예문'],
    summary="예문 목록 조회",
    description="특정 단어의 예문 목록을 조회합니다.",
    responses={200: ExampleSerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_example_list(request, word_id):
    """예문 목록 조회 (Admin/Staff 전용)"""
    word = get_object_or_404(Word, pk=word_id)
    examples = word.examples.prefetch_related('translations__language').all()
    serializer = ExampleSerializer(examples, many=True)
    return APIResponse.success(
        message='Examples retrieved',
        data={
            'word_id': word_id,
            'word_text': word.text,
            'examples': serializer.data
        }
    )


@extend_schema(
    tags=['관리자 - 예문'],
    summary="예문 추가",
    description="특정 단어에 새로운 예문을 추가합니다. 번역도 함께 추가할 수 있습니다.",
    request=ExampleCreateSerializer,
    responses={201: ExampleSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_example_create(request, word_id):
    """예문 추가 (Admin/Staff 전용)"""
    word = get_object_or_404(Word, pk=word_id)
    serializer = ExampleCreateSerializer(data=request.data)
    if serializer.is_valid():
        example = serializer.save(word=word)
        response_serializer = ExampleSerializer(example)
        return APIResponse.success(
            message='Example added successfully',
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED
        )

    return APIResponse.validation_error(
        errors=serializer.errors,
        message='Validation failed'
    )


@extend_schema(
    tags=['관리자 - 예문'],
    summary="예문 수정",
    description="특정 예문을 수정합니다.",
    request=ExampleCreateSerializer,
    responses={200: ExampleSerializer},
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_example_update(request, word_id, example_id):
    """예문 수정 (Admin/Staff 전용)"""
    example = get_object_or_404(Example, pk=example_id, word_id=word_id)
    serializer = ExampleCreateSerializer(example, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        response_serializer = ExampleSerializer(example)
        return APIResponse.success(
            message='Example updated successfully',
            data=response_serializer.data
        )

    return APIResponse.validation_error(
        errors=serializer.errors,
        message='Validation failed'
    )


@extend_schema(
    tags=['관리자 - 예문'],
    summary="예문 삭제",
    description="특정 예문을 삭제합니다. 관련된 번역도 함께 삭제됩니다.",
    responses={204: None},
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_example_delete(request, word_id, example_id):
    """예문 삭제 (Admin/Staff 전용)"""
    example = get_object_or_404(Example, pk=example_id, word_id=word_id)
    example.delete()
    return APIResponse.success(
        message='Example deleted successfully',
        data=None,
        status_code=status.HTTP_204_NO_CONTENT
    )


# =============================================================================
# ExampleTranslation Admin API
# =============================================================================

@extend_schema(
    tags=['관리자 - 예문 번역'],
    summary="예문 번역 추가",
    description="특정 예문에 새로운 번역을 추가합니다.",
    request=ExampleTranslationCreateSerializer,
    responses={201: ExampleTranslationSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_example_translation_create(request, word_id, example_id):
    """예문 번역 추가 (Admin/Staff 전용)"""
    example = get_object_or_404(Example, pk=example_id, word_id=word_id)
    serializer = ExampleTranslationCreateSerializer(data=request.data)
    if serializer.is_valid():
        translation = serializer.save(example=example)
        response_serializer = ExampleTranslationSerializer(translation)
        return APIResponse.success(
            message='Example translation added successfully',
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED
        )

    return APIResponse.validation_error(
        errors=serializer.errors,
        message='Validation failed'
    )


@extend_schema(
    tags=['관리자 - 예문 번역'],
    summary="예문 번역 수정",
    description="특정 예문 번역을 수정합니다.",
    request=ExampleTranslationCreateSerializer,
    responses={200: ExampleTranslationSerializer},
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_example_translation_update(request, word_id, example_id, translation_id):
    """예문 번역 수정 (Admin/Staff 전용)"""
    translation = get_object_or_404(
        ExampleTranslation,
        pk=translation_id,
        example_id=example_id,
        example__word_id=word_id
    )
    serializer = ExampleTranslationCreateSerializer(translation, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        response_serializer = ExampleTranslationSerializer(translation)
        return APIResponse.success(
            message='Example translation updated successfully',
            data=response_serializer.data
        )

    return APIResponse.validation_error(
        errors=serializer.errors,
        message='Validation failed'
    )


@extend_schema(
    tags=['관리자 - 예문 번역'],
    summary="예문 번역 삭제",
    description="특정 예문 번역을 삭제합니다.",
    responses={204: None},
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated, IsStaffRole])
def admin_example_translation_delete(request, word_id, example_id, translation_id):
    """예문 번역 삭제 (Admin/Staff 전용)"""
    translation = get_object_or_404(
        ExampleTranslation,
        pk=translation_id,
        example_id=example_id,
        example__word_id=word_id
    )
    translation.delete()
    return APIResponse.success(
        message='Example translation deleted successfully',
        data=None,
        status_code=status.HTTP_204_NO_CONTENT
    )
