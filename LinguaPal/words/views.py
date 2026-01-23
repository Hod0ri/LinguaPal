import random
from django.utils import timezone
from django.db.models import Sum, Count, F, Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from accounts.permissions import IsStaffRole
from accounts.utils import APIResponse, ErrorCode
from .models import (
    Word, WordTranslation, Example, ExampleTranslation,
    GanaQuiz, GanaQuizQuestion, UserGanaStats,
    WordCategory, GanaCharacterSet, GanaQuizType, GanaQuizQuestionCount
)
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
    GanaQuizStartRequestSerializer,
    GanaQuizSerializer,
    GanaQuizListSerializer,
    GanaQuizQuestionSerializer,
    GanaQuizQuestionCurrentSerializer,
    GanaQuizAnswerRequestSerializer,
    GanaQuizAnswerResponseSerializer,
    UserGanaStatsSerializer,
    UserGanaStatsSummarySerializer,
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


# =============================================================================
# 가나 퀴즈 API
# =============================================================================

def get_gana_words(character_set):
    """문자 세트에 따른 가나 문자 조회"""
    if character_set == GanaCharacterSet.HIRAGANA:
        return Word.objects.filter(category=WordCategory.HIRAGANA, is_active=True)
    elif character_set == GanaCharacterSet.KATAKANA:
        return Word.objects.filter(category=WordCategory.KATAKANA, is_active=True)
    else:  # ALL
        return Word.objects.filter(
            category__in=[WordCategory.HIRAGANA, WordCategory.KATAKANA],
            is_active=True
        )


def generate_choices(correct_word, all_words, quiz_type):
    """선택형 문제의 선택지 생성"""
    # 정답 제외한 단어들 중에서 2개 랜덤 선택
    other_words = list(all_words.exclude(id=correct_word.id))
    if len(other_words) < 2:
        other_words = list(all_words.exclude(id=correct_word.id))

    wrong_choices = random.sample(other_words, min(2, len(other_words)))

    if quiz_type == GanaQuizType.ROMAJI_TO_GANA_SELECT:
        # 로마자 보고 가나 선택
        choices = [correct_word.text] + [w.text for w in wrong_choices]
    else:
        choices = []

    random.shuffle(choices)
    return choices


@extend_schema(
    tags=['가나 퀴즈'],
    summary="퀴즈 시작",
    description="""
    새로운 가나 퀴즈를 시작합니다.

    **문자 세트 (character_set):**
    - `hiragana`: 히라가나만
    - `katakana`: 가타카나만
    - `all`: 전체

    **퀴즈 유형 (quiz_type):**
    - `gana_to_romaji`: 가나를 보고 로마자 입력
    - `romaji_to_gana_select`: 로마자를 보고 가나 선택 (3지선다)
    - `romaji_to_gana_input`: 로마자를 보고 가나 입력

    **문제 수 (question_count):**
    - `10`: 10문제
    - `25`: 25문제
    - `0`: 전체 (선택한 문자 세트의 모든 문자)
    """,
    request=GanaQuizStartRequestSerializer,
    responses={201: GanaQuizSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def quiz_start(request):
    """퀴즈 시작"""
    serializer = GanaQuizStartRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return APIResponse.validation_error(
            errors=serializer.errors,
            message='Validation failed'
        )

    character_set = serializer.validated_data['character_set']
    quiz_type = serializer.validated_data['quiz_type']
    question_count_setting = int(serializer.validated_data['question_count'])

    # 가나 문자 조회
    all_words = get_gana_words(character_set)
    word_list = list(all_words.order_by('order'))

    if not word_list:
        return APIResponse.error(
            message='No characters available for the selected set',
            error_code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND
        )

    # 문제 수 결정
    if question_count_setting == 0:  # 전체
        total_questions = len(word_list)
    else:
        total_questions = min(question_count_setting, len(word_list))

    # 문제 선택 (랜덤)
    selected_words = random.sample(word_list, total_questions)

    # 퀴즈 세션 생성
    quiz = GanaQuiz.objects.create(
        user=request.user,
        character_set=character_set,
        quiz_type=quiz_type,
        question_count_setting=question_count_setting,
        total_questions=total_questions
    )

    # 문제 생성
    for i, word in enumerate(selected_words, 1):
        choices = []
        if quiz_type == GanaQuizType.ROMAJI_TO_GANA_SELECT:
            choices = generate_choices(word, all_words, quiz_type)

        GanaQuizQuestion.objects.create(
            quiz=quiz,
            word=word,
            question_number=i,
            choices=choices
        )

    # 첫 번째 문제 포함하여 응답
    response_serializer = GanaQuizSerializer(quiz)
    first_question = quiz.questions.first()

    return APIResponse.success(
        message='Quiz started',
        data={
            'quiz': response_serializer.data,
            'current_question': GanaQuizQuestionCurrentSerializer(first_question).data if first_question else None
        },
        status_code=status.HTTP_201_CREATED
    )


@extend_schema(
    tags=['가나 퀴즈'],
    summary="답변 제출",
    description="현재 문제에 대한 답변을 제출합니다.",
    request=GanaQuizAnswerRequestSerializer,
    responses={200: GanaQuizAnswerResponseSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def quiz_answer(request, quiz_id):
    """답변 제출"""
    quiz = get_object_or_404(GanaQuiz, pk=quiz_id, user=request.user)

    if quiz.is_completed:
        return APIResponse.error(
            message='Quiz is already completed',
            error_code=ErrorCode.INVALID_INPUT,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    serializer = GanaQuizAnswerRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return APIResponse.validation_error(
            errors=serializer.errors,
            message='Validation failed'
        )

    question_id = serializer.validated_data['question_id']
    user_answer = serializer.validated_data['answer'].strip()

    # 문제 조회
    question = get_object_or_404(
        GanaQuizQuestion,
        pk=question_id,
        quiz=quiz
    )

    if question.is_correct is not None:
        return APIResponse.error(
            message='This question has already been answered',
            error_code=ErrorCode.INVALID_INPUT,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 정답 확인
    correct_answer = question.correct_answer
    is_correct = user_answer.lower() == correct_answer.lower()

    # 문제 업데이트
    question.user_answer = user_answer
    question.is_correct = is_correct
    question.answered_at = timezone.now()
    question.save()

    # 퀴즈 통계 업데이트
    if is_correct:
        quiz.correct_count += 1

    quiz.current_question += 1

    # 사용자 가나 통계 업데이트
    user_stats, _ = UserGanaStats.objects.get_or_create(
        user=request.user,
        word=question.word
    )
    user_stats.total_attempts += 1
    user_stats.last_attempted_at = timezone.now()
    if is_correct:
        user_stats.correct_count += 1
        user_stats.last_correct_at = timezone.now()
    else:
        user_stats.incorrect_count += 1
    user_stats.save()

    # 다음 문제 확인
    next_question = quiz.questions.filter(is_correct__isnull=True).first()
    quiz_completed = next_question is None

    if quiz_completed:
        quiz.is_completed = True
        quiz.completed_at = timezone.now()

    quiz.save()

    return APIResponse.success(
        message='Answer submitted',
        data={
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'user_answer': user_answer,
            'next_question': GanaQuizQuestionCurrentSerializer(next_question).data if next_question else None,
            'quiz_completed': quiz_completed,
            'current_score': quiz.correct_count,
            'total_answered': quiz.questions.filter(is_correct__isnull=False).count()
        }
    )


@extend_schema(
    tags=['가나 퀴즈'],
    summary="퀴즈 상세 조회",
    description="특정 퀴즈의 상세 정보와 모든 문제/답변을 조회합니다.",
    responses={200: GanaQuizSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_detail(request, quiz_id):
    """퀴즈 상세 조회"""
    quiz = get_object_or_404(GanaQuiz, pk=quiz_id, user=request.user)
    serializer = GanaQuizSerializer(quiz)
    return APIResponse.success(
        message='Quiz retrieved',
        data=serializer.data
    )


@extend_schema(
    tags=['가나 퀴즈'],
    summary="현재 문제 조회",
    description="진행 중인 퀴즈의 현재 문제를 조회합니다.",
    responses={200: GanaQuizQuestionCurrentSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_current_question(request, quiz_id):
    """현재 문제 조회"""
    quiz = get_object_or_404(GanaQuiz, pk=quiz_id, user=request.user)

    if quiz.is_completed:
        return APIResponse.error(
            message='Quiz is already completed',
            error_code=ErrorCode.INVALID_INPUT,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    current_question = quiz.questions.filter(is_correct__isnull=True).first()

    if not current_question:
        return APIResponse.error(
            message='No more questions',
            error_code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND
        )

    return APIResponse.success(
        message='Current question retrieved',
        data={
            'question': GanaQuizQuestionCurrentSerializer(current_question).data,
            'progress': {
                'current': quiz.questions.filter(is_correct__isnull=False).count() + 1,
                'total': quiz.total_questions,
                'correct_so_far': quiz.correct_count
            }
        }
    )


@extend_schema(
    tags=['가나 퀴즈'],
    summary="퀴즈 기록 조회",
    description="사용자의 퀴즈 기록을 조회합니다.",
    parameters=[
        OpenApiParameter(name='character_set', description='문자 세트 필터', required=False, type=str),
        OpenApiParameter(name='quiz_type', description='퀴즈 유형 필터', required=False, type=str),
        OpenApiParameter(name='is_completed', description='완료 여부 필터', required=False, type=bool),
        OpenApiParameter(name='limit', description='조회 개수 (기본: 20)', required=False, type=int),
    ],
    responses={200: GanaQuizListSerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_history(request):
    """퀴즈 기록 조회"""
    queryset = GanaQuiz.objects.filter(user=request.user)

    # 필터링
    character_set = request.query_params.get('character_set')
    if character_set:
        queryset = queryset.filter(character_set=character_set)

    quiz_type = request.query_params.get('quiz_type')
    if quiz_type:
        queryset = queryset.filter(quiz_type=quiz_type)

    is_completed = request.query_params.get('is_completed')
    if is_completed is not None:
        queryset = queryset.filter(is_completed=is_completed.lower() == 'true')

    # 제한
    limit = int(request.query_params.get('limit', 20))
    queryset = queryset[:limit]

    serializer = GanaQuizListSerializer(queryset, many=True)
    return APIResponse.success(
        message='Quiz history retrieved',
        data={
            'quizzes': serializer.data,
            'total_count': GanaQuiz.objects.filter(user=request.user).count()
        }
    )


@extend_schema(
    tags=['가나 퀴즈'],
    summary="학습 통계 조회",
    description="사용자의 가나 학습 통계를 조회합니다.",
    responses={200: UserGanaStatsSummarySerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def quiz_stats(request):
    """학습 통계 조회"""
    user = request.user

    # 퀴즈 통계
    quiz_stats = GanaQuiz.objects.filter(user=user).aggregate(
        total_quizzes=Count('id'),
        completed_quizzes=Count('id', filter=Q(is_completed=True)),
        total_correct=Sum('correct_count'),
        total_questions=Sum('total_questions')
    )

    total_quizzes = quiz_stats['total_quizzes'] or 0
    completed_quizzes = quiz_stats['completed_quizzes'] or 0
    total_correct = quiz_stats['total_correct'] or 0
    total_questions = quiz_stats['total_questions'] or 0

    overall_accuracy = round((total_correct / total_questions * 100), 1) if total_questions > 0 else 0

    # 히라가나/가타카나별 통계
    def get_category_stats(category):
        stats = UserGanaStats.objects.filter(
            user=user,
            word__category=category
        ).aggregate(
            total_attempts=Sum('total_attempts'),
            correct_count=Sum('correct_count'),
            characters_practiced=Count('id')
        )
        attempts = stats['total_attempts'] or 0
        correct = stats['correct_count'] or 0
        return {
            'total_attempts': attempts,
            'correct_count': correct,
            'accuracy': round((correct / attempts * 100), 1) if attempts > 0 else 0,
            'characters_practiced': stats['characters_practiced'] or 0
        }

    hiragana_stats = get_category_stats(WordCategory.HIRAGANA)
    katakana_stats = get_category_stats(WordCategory.KATAKANA)

    # 취약 문자 (정답률 낮은 순)
    weakest = UserGanaStats.objects.filter(
        user=user,
        total_attempts__gte=3  # 최소 3번 이상 시도한 것만
    ).annotate(
        accuracy_rate=F('correct_count') * 100 / F('total_attempts')
    ).order_by('accuracy_rate')[:5]

    # 강점 문자 (정답률 높은 순)
    strongest = UserGanaStats.objects.filter(
        user=user,
        total_attempts__gte=3
    ).annotate(
        accuracy_rate=F('correct_count') * 100 / F('total_attempts')
    ).order_by('-accuracy_rate')[:5]

    return APIResponse.success(
        message='Stats retrieved',
        data={
            'total_quizzes': total_quizzes,
            'completed_quizzes': completed_quizzes,
            'total_questions_answered': total_questions,
            'total_correct': total_correct,
            'overall_accuracy': overall_accuracy,
            'hiragana_stats': hiragana_stats,
            'katakana_stats': katakana_stats,
            'weakest_characters': UserGanaStatsSerializer(weakest, many=True).data,
            'strongest_characters': UserGanaStatsSerializer(strongest, many=True).data
        }
    )
