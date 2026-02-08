import uuid
import logging
import random
from django.utils import timezone
from django.db.models import Sum, Count, F, Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404

logger = logging.getLogger(__name__)


# =============================================================================
# xAPI Statement 비동기 생성 헬퍼
# =============================================================================

def queue_statement_task(statement_data):
    """xAPI Statement 생성을 비동기 태스크로 큐에 넣기"""
    try:
        from lrs.tasks import create_statement_task
        create_statement_task.delay(statement_data)
    except Exception as exc:
        logger.warning(f"Could not queue statement creation: {exc}")


def queue_quiz_completion_statements(quiz_data):
    """퀴즈 완료 시 여러 Statement (COMPLETED, PASSED/FAILED) 일괄 생성"""
    try:
        from lrs.tasks import create_quiz_statements_task
        create_quiz_statements_task.delay(quiz_data)
    except Exception as exc:
        logger.warning(f"Could not queue quiz completion statements: {exc}")
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample, OpenApiResponse
from accounts.permissions import IsStaffRole
from accounts.utils import APIResponse, ErrorCode
from .models import (
    Word, WordTranslation, Example, ExampleTranslation,
    GanaQuiz, GanaQuizQuestion, UserGanaStats,
    WordCategory, GanaCharacterSet, GanaQuizType, GanaQuizQuestionCount,
    Vocabulary, VocabularyWord,
    WordQuiz, WordQuizQuestion, UserWordStats,
    WordQuizType, WordQuizQuestionCount,
    FlashcardSession, FlashcardRecord
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
    WordQuizStartRequestSerializer,
    WordQuizSerializer,
    WordQuizListSerializer,
    WordQuizQuestionSerializer,
    WordQuizQuestionCurrentSerializer,
    WordQuizAnswerRequestSerializer,
    WordQuizAnswerResponseSerializer,
    UserWordStatsSerializer,
    WordQuizStatsSummarySerializer,
    FlashcardSessionSerializer,
    FlashcardSessionDetailSerializer,
    FlashcardRecordSerializer,
    FlashcardWordSerializer,
    FlashcardStartRequestSerializer,
    FlashcardAnswerRequestSerializer,
    VocabularyListSerializer,
    VocabularyDetailSerializer,
    VocabularyCreateSerializer,
    AddWordToVocabularySerializer,
    VocabularyWordSerializer,
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

    # xAPI INITIALIZED Statement 생성 (비동기)
    registration = uuid.uuid4()
    quiz.registration = registration  # registration 저장을 위해 모델에 필드 필요시 추가
    from lrs.services import QuizStatementService
    statement_data = QuizStatementService.quiz_initialized(
        user=request.user,
        quiz=quiz,
        quiz_type=quiz_type,
        registration=registration
    )
    queue_statement_task(statement_data)

    # 첫 번째 문제 포함하여 응답
    response_serializer = GanaQuizSerializer(quiz)
    first_question = quiz.questions.first()

    return APIResponse.success(
        message='Quiz started',
        data={
            'quiz': response_serializer.data,
            'current_question': GanaQuizQuestionCurrentSerializer(first_question).data if first_question else None,
            'registration': str(registration)
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

    # xAPI ANSWERED Statement 생성 (비동기)
    from lrs.services import QuizStatementService
    registration = getattr(quiz, 'registration', None)
    answered_data = QuizStatementService.question_answered(
        user=request.user,
        quiz=quiz,
        question=question,
        user_answer=user_answer,
        is_correct=is_correct,
        correct_answer=correct_answer,
        registration=registration
    )
    queue_statement_task(answered_data)

    # 다음 문제 확인
    next_question = quiz.questions.filter(is_correct__isnull=True).first()
    quiz_completed = next_question is None

    if quiz_completed:
        quiz.is_completed = True
        quiz.completed_at = timezone.now()

        # xAPI COMPLETED, PASSED/FAILED Statement 생성 (비동기)
        completion_statements = QuizStatementService.quiz_completed(
            user=request.user,
            quiz=quiz,
            registration=registration
        )
        queue_quiz_completion_statements({'statements': completion_statements})

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


# =============================================================================
# 단어 퀴즈 API
# =============================================================================

def get_word_quiz_words(language):
    """학습 언어에 해당하는 단어 조회 (category=word)"""
    return Word.objects.filter(
        language=language,
        category=WordCategory.WORD,
        is_active=True
    ).prefetch_related('translations')


def generate_word_choices(correct_word, all_words, quiz_type, native_language):
    """선택형 문제의 선택지 생성"""
    other_words = list(all_words.exclude(id=correct_word.id))
    if len(other_words) < 2:
        other_words = list(all_words.exclude(id=correct_word.id))

    wrong_choices = random.sample(other_words, min(2, len(other_words)))

    if quiz_type == WordQuizType.NATIVE_TO_WORD_SELECT:
        # 모국어 보고 단어 선택 -> 선택지는 학습 언어 단어들
        choices = [correct_word.text] + [w.text for w in wrong_choices]
    else:
        choices = []

    random.shuffle(choices)
    return choices


def generate_example_fill_choices(correct_word, all_words):
    """예문 빈칸 채우기 선택지 생성"""
    # 정답 단어 추가
    choices = [correct_word.text]

    # 다른 단어들 중 랜덤하게 2개 선택
    other_words = list(all_words.exclude(id=correct_word.id))
    if len(other_words) >= 2:
        wrong_choices = random.sample(other_words, 2)
        choices.extend([w.text for w in wrong_choices])

    random.shuffle(choices)
    return choices


def get_random_quiz_type():
    """혼합 퀴즈를 위한 랜덤 타입 선택"""
    types = [
        WordQuizType.WORD_TO_NATIVE,
        WordQuizType.NATIVE_TO_WORD_SELECT,
        WordQuizType.NATIVE_TO_WORD_INPUT,
        WordQuizType.EXAMPLE_FILL_IN_BLANK,
    ]
    return random.choice(types)


@extend_schema(
    tags=['단어 퀴즈'],
    summary="단어 퀴즈 시작",
    description="""
    새로운 단어 퀴즈를 시작합니다.

    **퀴즈 유형 (quiz_type):**
    - `word_to_native`: 외국어 단어를 보고 모국어 뜻 입력
    - `native_to_word_select`: 모국어 뜻을 보고 외국어 단어 선택 (3지선다)
    - `native_to_word_input`: 모국어 뜻을 보고 외국어 단어 입력

    **문제 수 (question_count):**
    - `10`: 10문제
    - `25`: 25문제
    - `0`: 전체
    """,
    request=WordQuizStartRequestSerializer,
    responses={201: WordQuizSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def word_quiz_start(request):
    """단어 퀴즈 시작"""
    serializer = WordQuizStartRequestSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return APIResponse.validation_error(
            errors=serializer.errors,
            message='Validation failed'
        )

    learning_language_id = serializer.validated_data['learning_language']
    quiz_type = serializer.validated_data['quiz_type']
    question_count_setting = int(serializer.validated_data['question_count'])
    vocabulary_id = serializer.validated_data.get('vocabulary_id')

    # 학습 언어 조회
    from accounts.models import Language
    learning_language = get_object_or_404(Language, pk=learning_language_id)

    # 사용자의 모국어 조회 (프로필의 국가에서)
    user_profile = getattr(request.user, 'profile', None)
    if not user_profile:
        return APIResponse.error(
            message='프로필이 설정되지 않았습니다.',
            error_code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 국가 코드에서 언어 코드로 매핑
    COUNTRY_TO_LANGUAGE = {
        'KR': 'ko',  # 한국 → 한국어
        'JP': 'ja',  # 일본 → 일본어
        'US': 'en',  # 미국 → 영어
        'GB': 'en',  # 영국 → 영어
        'ES': 'es',  # 스페인 → 스페인어
        'CN': 'zh',  # 중국 → 중국어
    }

    native_language = None
    if user_profile.country:
        lang_code = COUNTRY_TO_LANGUAGE.get(user_profile.country.code)
        if lang_code:
            native_language = Language.objects.filter(code=lang_code).first()

    if not native_language:
        # 기본값으로 한국어 사용
        native_language = Language.objects.filter(code='ko').first()
        if not native_language:
            return APIResponse.error(
                message='모국어를 설정할 수 없습니다.',
                error_code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_400_BAD_REQUEST
            )

    # 단어 조회 (학습 언어의 단어 중 모국어 번역이 있는 것만)
    all_words = get_word_quiz_words(learning_language).filter(
        translations__language=native_language
    ).distinct()

    # 단어장이 지정된 경우, 해당 단어장의 단어만 필터링
    if vocabulary_id:
        vocabulary = get_object_or_404(Vocabulary, id=vocabulary_id, user=request.user)
        # 단어장에 포함된 단어 ID 목록
        vocabulary_word_ids = vocabulary.words.values_list('id', flat=True)
        all_words = all_words.filter(id__in=vocabulary_word_ids)

    # 배운 단어만 퀴즈에 포함하는 경우
    learned_words_only = serializer.validated_data.get('learned_words_only', False)
    if learned_words_only:
        # 학습하기에서 본 단어 ID 조회 (viewed_at이 null이 아닌 FlashcardRecord)
        learned_word_ids = set(
            FlashcardRecord.objects.filter(
                session__user=request.user,
                session__learning_language=learning_language,
                viewed_at__isnull=False
            ).values_list('word_id', flat=True).distinct()
        )

        if not learned_word_ids:
            return APIResponse.error(
                message='학습한 단어가 없습니다. 먼저 학습하기를 진행해주세요.',
                error_code=ErrorCode.NOT_FOUND,
                status_code=status.HTTP_404_NOT_FOUND
            )

        all_words = all_words.filter(id__in=learned_word_ids)

    word_list = list(all_words)

    if not word_list:
        if learned_words_only:
            error_message = '학습한 단어가 부족합니다. 먼저 학습하기를 진행해주세요.'
        elif vocabulary_id:
            error_message = '해당 단어장에 단어가 없습니다.'
        else:
            error_message = '해당 언어에 대한 단어가 없습니다.'
        return APIResponse.error(
            message=error_message,
            error_code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND
        )

    # 문제 수 결정
    if question_count_setting == 0:
        total_questions = len(word_list)
    else:
        total_questions = min(question_count_setting, len(word_list))

    # 문제 선택
    if learned_words_only:
        # 스마트 선택: 오답률 높은 것, 최근에 배운 것, 퀴즈에 나온 지 오래된 것 우선
        from datetime import timedelta
        now = timezone.now()

        # 각 단어의 우선순위 점수 계산
        word_priorities = []
        for word in word_list:
            # 1. 오답률 계산
            quiz_stats = WordQuizQuestion.objects.filter(
                quiz__user=request.user,
                word=word
            ).aggregate(
                total=Count('id'),
                incorrect=Count('id', filter=Q(is_correct=False))
            )
            total_attempts = quiz_stats['total'] or 0
            incorrect_count = quiz_stats['incorrect'] or 0
            error_rate = incorrect_count / total_attempts if total_attempts > 0 else 0.5  # 처음 보는 단어는 중간값

            # 2. 최근 학습 시간
            recent_flashcard = FlashcardRecord.objects.filter(
                session__user=request.user,
                word=word,
                viewed_at__isnull=False
            ).order_by('-viewed_at').first()

            if recent_flashcard and recent_flashcard.viewed_at:
                days_since_learned = (now - recent_flashcard.viewed_at).days
                # 최근 7일 이내면 높은 점수, 그 이후는 점수 감소
                recency_score = max(0, 1.0 - (days_since_learned / 30.0))  # 30일 기준
            else:
                recency_score = 0.5

            # 3. 마지막 퀴즈 시간
            last_quiz = WordQuizQuestion.objects.filter(
                quiz__user=request.user,
                word=word,
                answered_at__isnull=False
            ).order_by('-answered_at').first()

            if last_quiz and last_quiz.answered_at:
                days_since_quiz = (now - last_quiz.answered_at).days
                # 오래될수록 높은 점수
                staleness_score = min(1.0, days_since_quiz / 7.0)  # 7일 기준
            else:
                staleness_score = 1.0  # 퀴즈에 안 나온 단어는 최대 점수

            # 종합 우선순위 점수 (가중치 적용)
            priority_score = (
                error_rate * 0.4 +        # 오답률 40%
                recency_score * 0.3 +     # 최근 학습 30%
                staleness_score * 0.3     # 오래된 정도 30%
            )

            word_priorities.append((word, priority_score))

        # 우선순위 점수로 정렬
        word_priorities.sort(key=lambda x: x[1], reverse=True)

        # 상위 단어 선택 (일부 랜덤성 추가)
        # 상위 50%에서 필요한 만큼 랜덤 선택
        top_half_count = max(total_questions, len(word_priorities) // 2)
        top_candidates = [w for w, _ in word_priorities[:top_half_count]]
        selected_words = random.sample(top_candidates, min(total_questions, len(top_candidates)))
    else:
        # 일반 퀴즈는 랜덤 선택
        selected_words = random.sample(word_list, total_questions)

    # 퀴즈 세션 생성
    quiz = WordQuiz.objects.create(
        user=request.user,
        learning_language=learning_language,
        native_language=native_language,
        quiz_type=quiz_type,
        question_count_setting=question_count_setting,
        total_questions=total_questions
    )

    # 문제 생성
    for i, word in enumerate(selected_words, 1):
        choices = []
        current_type = quiz_type

        # 혼합 퀴즈인 경우 문제마다 랜덤 타입 선택
        if quiz_type == WordQuizType.MIXED:
            current_type = get_random_quiz_type()

        # 타입에 따라 선택지 생성
        if current_type == WordQuizType.NATIVE_TO_WORD_SELECT:
            choices = generate_word_choices(word, all_words, current_type, native_language)
        elif current_type == WordQuizType.EXAMPLE_FILL_IN_BLANK:
            choices = generate_example_fill_choices(word, all_words)

        WordQuizQuestion.objects.create(
            quiz=quiz,
            word=word,
            question_number=i,
            choices=choices
        )

    # xAPI INITIALIZED Statement 생성 (비동기)
    registration = uuid.uuid4()
    from lrs.services import QuizStatementService
    statement_data = QuizStatementService.quiz_initialized(
        user=request.user,
        quiz=quiz,
        quiz_type=quiz_type,
        registration=registration
    )
    queue_statement_task(statement_data)

    # 첫 번째 문제 포함하여 응답
    response_serializer = WordQuizSerializer(quiz)
    first_question = quiz.questions.first()

    return APIResponse.success(
        message='Word quiz started',
        data={
            'quiz': response_serializer.data,
            'current_question': WordQuizQuestionCurrentSerializer(first_question).data if first_question else None,
            'registration': str(registration)
        },
        status_code=status.HTTP_201_CREATED
    )


@extend_schema(
    tags=['단어 퀴즈'],
    summary="단어 퀴즈 답변 제출",
    description="현재 문제에 대한 답변을 제출합니다.",
    request=WordQuizAnswerRequestSerializer,
    responses={200: WordQuizAnswerResponseSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def word_quiz_answer(request, quiz_id):
    """단어 퀴즈 답변 제출"""
    quiz = get_object_or_404(WordQuiz, pk=quiz_id, user=request.user)

    if quiz.is_completed:
        return APIResponse.error(
            message='Quiz is already completed',
            error_code=ErrorCode.INVALID_INPUT,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    serializer = WordQuizAnswerRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return APIResponse.validation_error(
            errors=serializer.errors,
            message='Validation failed'
        )

    question_id = serializer.validated_data['question_id']
    user_answer = serializer.validated_data['answer'].strip()

    # 문제 조회
    question = get_object_or_404(
        WordQuizQuestion,
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
    correct_answer = question.get_correct_answer(quiz.native_language)
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

    # 사용자 단어 통계 업데이트
    user_stats, _ = UserWordStats.objects.get_or_create(
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

    # xAPI ANSWERED Statement 생성 (비동기)
    from lrs.services import QuizStatementService
    registration = getattr(quiz, 'registration', None)
    answered_data = QuizStatementService.question_answered(
        user=request.user,
        quiz=quiz,
        question=question,
        user_answer=user_answer,
        is_correct=is_correct,
        correct_answer=correct_answer,
        registration=registration
    )
    queue_statement_task(answered_data)

    # 다음 문제 확인
    next_question = quiz.questions.filter(is_correct__isnull=True).first()
    quiz_completed = next_question is None

    if quiz_completed:
        quiz.is_completed = True
        quiz.completed_at = timezone.now()

        # xAPI COMPLETED, PASSED/FAILED Statement 생성 (비동기)
        completion_statements = QuizStatementService.quiz_completed(
            user=request.user,
            quiz=quiz,
            registration=registration
        )
        queue_quiz_completion_statements({'statements': completion_statements})

    quiz.save()

    return APIResponse.success(
        message='Answer submitted',
        data={
            'is_correct': is_correct,
            'correct_answer': correct_answer,
            'user_answer': user_answer,
            'next_question': WordQuizQuestionCurrentSerializer(next_question).data if next_question else None,
            'quiz_completed': quiz_completed,
            'current_score': quiz.correct_count,
            'total_answered': quiz.questions.filter(is_correct__isnull=False).count()
        }
    )


@extend_schema(
    tags=['단어 퀴즈'],
    summary="단어 퀴즈 상세 조회",
    description="특정 퀴즈의 상세 정보와 모든 문제/답변을 조회합니다.",
    responses={200: WordQuizSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def word_quiz_detail(request, quiz_id):
    """단어 퀴즈 상세 조회"""
    quiz = get_object_or_404(WordQuiz, pk=quiz_id, user=request.user)
    serializer = WordQuizSerializer(quiz)
    return APIResponse.success(
        message='Word quiz retrieved',
        data=serializer.data
    )


@extend_schema(
    tags=['단어 퀴즈'],
    summary="현재 문제 조회",
    description="진행 중인 퀴즈의 현재 문제를 조회합니다.",
    responses={200: WordQuizQuestionCurrentSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def word_quiz_current_question(request, quiz_id):
    """현재 문제 조회"""
    quiz = get_object_or_404(WordQuiz, pk=quiz_id, user=request.user)

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
            'question': WordQuizQuestionCurrentSerializer(current_question).data,
            'progress': {
                'current': quiz.questions.filter(is_correct__isnull=False).count() + 1,
                'total': quiz.total_questions,
                'correct_so_far': quiz.correct_count
            }
        }
    )


@extend_schema(
    tags=['단어 퀴즈'],
    summary="단어 퀴즈 기록 조회",
    description="사용자의 단어 퀴즈 기록을 조회합니다.",
    parameters=[
        OpenApiParameter(name='learning_language', description='학습 언어 코드 필터', required=False, type=str),
        OpenApiParameter(name='quiz_type', description='퀴즈 유형 필터', required=False, type=str),
        OpenApiParameter(name='is_completed', description='완료 여부 필터', required=False, type=bool),
        OpenApiParameter(name='limit', description='조회 개수 (기본: 20)', required=False, type=int),
    ],
    responses={200: WordQuizListSerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def word_quiz_history(request):
    """단어 퀴즈 기록 조회"""
    queryset = WordQuiz.objects.filter(user=request.user).select_related('learning_language')

    # 필터링
    learning_language = request.query_params.get('learning_language')
    if learning_language:
        queryset = queryset.filter(learning_language__code=learning_language)

    quiz_type = request.query_params.get('quiz_type')
    if quiz_type:
        queryset = queryset.filter(quiz_type=quiz_type)

    is_completed = request.query_params.get('is_completed')
    if is_completed is not None:
        queryset = queryset.filter(is_completed=is_completed.lower() == 'true')

    # 제한
    limit = int(request.query_params.get('limit', 20))
    queryset = queryset[:limit]

    serializer = WordQuizListSerializer(queryset, many=True)
    return APIResponse.success(
        message='Word quiz history retrieved',
        data={
            'quizzes': serializer.data,
            'total_count': WordQuiz.objects.filter(user=request.user).count()
        }
    )


@extend_schema(
    tags=['단어 퀴즈'],
    summary="단어 학습 통계 조회",
    description="사용자의 단어 학습 통계를 조회합니다.",
    parameters=[
        OpenApiParameter(name='learning_language', description='학습 언어 코드 필터', required=False, type=str),
    ],
    responses={200: WordQuizStatsSummarySerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def word_quiz_stats(request):
    """단어 학습 통계 조회"""
    user = request.user

    # 퀴즈 통계 기본 쿼리
    quiz_queryset = WordQuiz.objects.filter(user=user)

    # 언어 필터
    learning_language = request.query_params.get('learning_language')
    if learning_language:
        quiz_queryset = quiz_queryset.filter(learning_language__code=learning_language)

    quiz_stats = quiz_queryset.aggregate(
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

    # 언어별 통계
    from accounts.models import Language
    language_stats = {}

    user_languages = WordQuiz.objects.filter(user=user).values_list(
        'learning_language', flat=True
    ).distinct()

    for lang_id in user_languages:
        lang = Language.objects.filter(pk=lang_id).first()
        if lang:
            lang_quizzes = WordQuiz.objects.filter(user=user, learning_language=lang)
            lang_aggregate = lang_quizzes.aggregate(
                total_attempts=Sum('total_questions'),
                correct_count=Sum('correct_count'),
                quiz_count=Count('id', filter=Q(is_completed=True))
            )
            attempts = lang_aggregate['total_attempts'] or 0
            correct = lang_aggregate['correct_count'] or 0
            language_stats[lang.code] = {
                'language_name': lang.name_ko,
                'total_attempts': attempts,
                'correct_count': correct,
                'accuracy': round((correct / attempts * 100), 1) if attempts > 0 else 0,
                'quiz_count': lang_aggregate['quiz_count'] or 0
            }

    # 취약 단어 (정답률 낮은 순)
    weakest = UserWordStats.objects.filter(
        user=user,
        total_attempts__gte=3
    ).annotate(
        accuracy_rate=F('correct_count') * 100 / F('total_attempts')
    ).order_by('accuracy_rate')[:5]

    # 강점 단어 (정답률 높은 순)
    strongest = UserWordStats.objects.filter(
        user=user,
        total_attempts__gte=3
    ).annotate(
        accuracy_rate=F('correct_count') * 100 / F('total_attempts')
    ).order_by('-accuracy_rate')[:5]

    return APIResponse.success(
        message='Word quiz stats retrieved',
        data={
            'total_quizzes': total_quizzes,
            'completed_quizzes': completed_quizzes,
            'total_questions_answered': total_questions,
            'total_correct': total_correct,
            'overall_accuracy': overall_accuracy,
            'language_stats': language_stats,
            'weakest_words': UserWordStatsSerializer(weakest, many=True).data,
            'strongest_words': UserWordStatsSerializer(strongest, many=True).data
        }
    )


# =============================================================================
# Flashcard Study API
# =============================================================================

@extend_schema(
    tags=['플래시카드 학습'],
    summary="플래시카드 학습 시작",
    description="새로운 플래시카드 학습 세션을 시작합니다.",
    request=FlashcardStartRequestSerializer,
    responses={201: FlashcardSessionDetailSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def flashcard_start(request):
    """플래시카드 학습 세션 시작"""
    serializer = FlashcardStartRequestSerializer(data=request.data, context={'request': request})
    if not serializer.is_valid():
        return APIResponse.error(
            message='Invalid request data',
            data=serializer.errors,
            error_code=ErrorCode.VALIDATION_ERROR
        )

    user = request.user
    learning_language_id = serializer.validated_data['learning_language']
    category = serializer.validated_data.get('category', '')
    card_count = serializer.validated_data.get('card_count', 20)
    vocabulary_id = serializer.validated_data.get('vocabulary_id')

    # 사용자의 학습 언어인지 확인
    if not hasattr(user, 'profile') or not user.profile:
        return APIResponse.error(
            message='Profile not found',
            error_code=ErrorCode.NOT_FOUND
        )

    user_learning_languages = user.profile.learning_languages.values_list('id', flat=True)
    if learning_language_id not in user_learning_languages:
        return APIResponse.error(
            message='Not a learning language',
            data={'learning_language': '학습 언어가 아닙니다.'},
            error_code=ErrorCode.VALIDATION_ERROR
        )

    # 단어 쿼리
    words_qs = Word.objects.filter(
        language_id=learning_language_id,
        is_active=True
    ).prefetch_related('translations', 'examples__translations')

    # 단어장이 지정된 경우, 해당 단어장의 단어만 필터링
    if vocabulary_id:
        vocabulary = get_object_or_404(Vocabulary, id=vocabulary_id, user=user)
        vocabulary_word_ids = vocabulary.words.values_list('id', flat=True)
        words_qs = words_qs.filter(id__in=vocabulary_word_ids)
    elif category:
        # 단어장이 없을 때만 카테고리 필터 적용
        words_qs = words_qs.filter(category=category)

    # 사용자 모국어로 번역이 있는 단어만
    native_language = user.profile.country.languages.first() if hasattr(user.profile.country, 'languages') else None
    if native_language:
        words_qs = words_qs.filter(translations__language=native_language).distinct()

    # 스마트 단어 선택 알고리즘 (1/3 복습 + 2/3 새 단어)
    all_word_ids = set(words_qs.values_list('id', flat=True))

    if len(all_word_ids) == 0:
        error_message = '해당 단어장에 단어가 없습니다.' if vocabulary_id else '해당 언어에 학습할 단어가 없습니다.'
        return APIResponse.error(
            message='No words available',
            data={'learning_language': error_message},
            error_code=ErrorCode.NOT_FOUND
        )

    # 실제 카드 수 조정
    if len(all_word_ids) < card_count:
        card_count = len(all_word_ids)

    # 1. 이미 본 단어 찾기 (FlashcardRecord에 기록된 단어)
    viewed_word_ids = set(
        FlashcardRecord.objects.filter(
            session__user=user,
            session__learning_language_id=learning_language_id,
            viewed_at__isnull=False
        ).values_list('word_id', flat=True).distinct()
    )

    # 2. 퀴즈에서 틀린 단어 찾기 (최근 30일 내)
    from django.utils import timezone
    from datetime import timedelta
    thirty_days_ago = timezone.now() - timedelta(days=30)

    incorrect_word_ids = set(
        WordQuizQuestion.objects.filter(
            quiz__user=user,
            quiz__learning_language_id=learning_language_id,
            quiz__started_at__gte=thirty_days_ago,
            is_correct=False
        ).values_list('word_id', flat=True).distinct()
    )

    # 3. 복습할 단어와 새 단어 구분
    review_candidates = (viewed_word_ids | incorrect_word_ids) & all_word_ids  # 교집합
    new_candidates = all_word_ids - review_candidates  # 차집합

    # 4. 복습 단어 선택 (1/3, 틀린 단어 우선)
    review_count = max(1, card_count // 3)  # 최소 1개
    review_word_ids = []

    # 틀린 단어 우선 선택
    incorrect_available = list(incorrect_word_ids & all_word_ids)
    if incorrect_available:
        take_count = min(len(incorrect_available), review_count)
        review_word_ids.extend(random.sample(incorrect_available, take_count))

    # 부족하면 다른 복습 단어로 채우기
    if len(review_word_ids) < review_count:
        remaining_review = list(review_candidates - set(review_word_ids))
        if remaining_review:
            need_count = min(len(remaining_review), review_count - len(review_word_ids))
            review_word_ids.extend(random.sample(remaining_review, need_count))

    # 5. 새 단어 선택 (나머지)
    new_count = card_count - len(review_word_ids)
    new_word_ids = []

    if new_count > 0 and new_candidates:
        take_count = min(len(new_candidates), new_count)
        new_word_ids = random.sample(list(new_candidates), take_count)

    # 6. 만약 새 단어가 부족하면 복습 단어로 채우기
    if len(review_word_ids) + len(new_word_ids) < card_count:
        remaining = card_count - len(review_word_ids) - len(new_word_ids)
        available = list((review_candidates - set(review_word_ids)) | (new_candidates - set(new_word_ids)))
        if available:
            additional = random.sample(available, min(len(available), remaining))
            new_word_ids.extend(additional)

    # 7. 최종 선택된 단어들 (순서 섞기)
    selected_ids = review_word_ids + new_word_ids
    random.shuffle(selected_ids)

    selected_words = Word.objects.filter(id__in=selected_ids).prefetch_related(
        'translations', 'examples__translations'
    )

    # 세션 생성
    from accounts.models import Language
    learning_language = Language.objects.get(id=learning_language_id)

    session = FlashcardSession.objects.create(
        user=user,
        learning_language=learning_language,
        category=category,
        total_cards=card_count
    )

    # 카드 레코드 생성
    records = []
    for idx, word in enumerate(selected_words):
        record = FlashcardRecord.objects.create(
            session=session,
            word=word,
            card_index=idx
        )
        records.append(record)

    # xAPI Statement: INITIALIZED
    # subcategory: 카테고리가 있으면 카테고리명, 없으면 언어명
    from .models import WordCategory
    subcategory_display = learning_language.name_ko
    if category:
        category_labels = dict(WordCategory.choices)
        subcategory_display = category_labels.get(category, category)

    queue_statement_task({
        'actor_user_id': user.id,
        'verb': 'initialized',
        'object_type': 'flashcard',
        'object_id': f'flashcard/session/{session.id}',
        'context': {
            'category': 'flashcard',
            'subcategory': subcategory_display,
            'quiz_type': '일반 학습',
            'session_id': session.id,
            'total_cards': card_count,
            'language_code': learning_language.code,
            'language_name': learning_language.name_ko,
        }
    })

    session.refresh_from_db()
    first_record = records[0] if records else None
    serializer_context = {'native_language_id': native_language.id if native_language else None}
    return APIResponse.success(
        message='Flashcard session started',
        data={
            'session': FlashcardSessionSerializer(session).data,
            'current_card': FlashcardRecordSerializer(first_record, context=serializer_context).data if first_record else None
        },
        status_code=status.HTTP_201_CREATED
    )


@extend_schema(
    tags=['플래시카드 학습'],
    summary="현재 카드 조회",
    description="현재 학습 중인 카드 정보를 조회합니다.",
    responses={200: FlashcardRecordSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def flashcard_current(request, session_id):
    """현재 플래시카드 조회"""
    session = get_object_or_404(FlashcardSession, id=session_id, user=request.user)

    if session.is_completed:
        return APIResponse.error(
            message='Session already completed',
            error_code=ErrorCode.VALIDATION_ERROR
        )

    # 현재 인덱스의 레코드
    record = session.records.select_related('word').prefetch_related(
        'word__translations', 'word__examples__translations'
    ).filter(card_index=session.current_index).first()
    if not record:
        return APIResponse.error(
            message='No more cards',
            error_code=ErrorCode.NOT_FOUND
        )

    # 사용자 모국어 조회
    user = request.user
    native_language = user.profile.country.languages.first() if hasattr(user, 'profile') and hasattr(user.profile.country, 'languages') else None

    # 조회 시간 기록
    if not record.viewed_at:
        record.viewed_at = timezone.now()
        record.save()

        # xAPI Statement: EXPERIENCED (카드 조회)
        # subcategory: 카테고리가 있으면 카테고리명, 없으면 언어명
        from .models import WordCategory
        subcategory_display = session.learning_language.name_ko
        if session.category:
            category_labels = dict(WordCategory.choices)
            subcategory_display = category_labels.get(session.category, session.category)

        queue_statement_task({
            'actor_user_id': request.user.id,
            'verb': 'experienced',
            'object_type': 'flashcard',
            'object_id': f'flashcard/session/{session.id}/card/{record.id}',
            'context': {
                'category': 'flashcard',
                'subcategory': subcategory_display,
                'quiz_type': '일반 학습',
                'session_id': session.id,
                'card_index': record.card_index,
                'word_id': record.word.id,
                'word_text': record.word.text,
                'language_code': session.learning_language.code,
                'language_name': session.learning_language.name_ko,
            }
        })

    serializer_context = {'native_language_id': native_language.id if native_language else None}
    return APIResponse.success(
        message='Current card',
        data={
            'session': FlashcardSessionSerializer(session).data,
            'current_card': FlashcardRecordSerializer(record, context=serializer_context).data,
        }
    )


@extend_schema(
    tags=['플래시카드 학습'],
    summary="카드 응답",
    description="플래시카드에 대한 응답(알아요/몰라요)을 제출합니다.",
    request=FlashcardAnswerRequestSerializer,
    responses={200: FlashcardSessionSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def flashcard_answer(request, session_id):
    """플래시카드 다음 카드로 이동 (viewed 기록)"""
    session = get_object_or_404(FlashcardSession, id=session_id, user=request.user)

    if session.is_completed:
        return APIResponse.error(
            message='Session already completed',
            error_code=ErrorCode.VALIDATION_ERROR
        )

    serializer = FlashcardAnswerRequestSerializer(data=request.data)
    if not serializer.is_valid():
        return APIResponse.error(
            message='Invalid request data',
            data=serializer.errors,
            error_code=ErrorCode.VALIDATION_ERROR
        )

    record_id = serializer.validated_data['record_id']

    # 사용자 모국어 조회
    user = request.user
    native_language = user.profile.country.languages.first() if hasattr(user, 'profile') and hasattr(user.profile.country, 'languages') else None

    record = get_object_or_404(
        FlashcardRecord.objects.select_related('word').prefetch_related('word__translations', 'word__examples__translations'),
        id=record_id,
        session=session
    )

    if record.viewed_at is not None:
        return APIResponse.error(
            message='Already viewed',
            error_code=ErrorCode.VALIDATION_ERROR
        )

    # 학습 기록 (viewed만 기록)
    record.viewed_at = timezone.now()
    record.answered_at = timezone.now()
    record.save()

    # 세션 업데이트
    session.current_index += 1

    # xAPI Statement: ANSWERED
    # subcategory: 카테고리가 있으면 카테고리명, 없으면 언어명
    from .models import WordCategory
    subcategory_display = session.learning_language.name_ko
    if session.category:
        category_labels = dict(WordCategory.choices)
        subcategory_display = category_labels.get(session.category, session.category)

    queue_statement_task({
        'actor_user_id': request.user.id,
        'verb': 'progressed',
        'object_type': 'flashcard',
        'object_id': f'flashcard/session/{session.id}/card/{record.id}',
        'result': {
            'response': 'viewed',
        },
        'context': {
            'category': 'flashcard',
            'subcategory': subcategory_display,
            'quiz_type': '일반 학습',
            'session_id': session.id,
            'card_index': record.card_index,
            'word_id': record.word.id,
            'word_text': record.word.text,
            'language_code': session.learning_language.code,
            'language_name': session.learning_language.name_ko,
        }
    })

    # 완료 체크
    next_card = None
    if session.current_index >= session.total_cards:
        session.is_completed = True
        session.completed_at = timezone.now()

        # xAPI Statement: COMPLETED
        queue_statement_task({
            'actor_user_id': request.user.id,
            'verb': 'completed',
            'object_type': 'flashcard',
            'object_id': f'flashcard/session/{session.id}',
            'result': {
                'score_raw': session.total_cards,
                'score_max': session.total_cards,
                'completion': True,
            },
            'context': {
                'category': 'flashcard',
                'subcategory': subcategory_display,
                'quiz_type': '일반 학습',
                'session_id': session.id,
                'total_cards': session.total_cards,
                'language_code': session.learning_language.code,
                'language_name': session.learning_language.name_ko,
            }
        })
    else:
        # 다음 카드 정보
        next_record = session.records.select_related('word').prefetch_related(
            'word__translations', 'word__examples__translations'
        ).filter(card_index=session.current_index).first()
        if next_record:
            serializer_context = {'native_language_id': native_language.id if native_language else None}
            next_card = FlashcardRecordSerializer(next_record, context=serializer_context).data

    session.save()

    serializer_context = {'native_language_id': native_language.id if native_language else None}
    return APIResponse.success(
        message='Answer recorded',
        data={
            'record': FlashcardRecordSerializer(record, context=serializer_context).data,
            'next_card': next_card,
            'session_completed': session.is_completed,
            'known_count': session.known_count,
            'unknown_count': session.unknown_count,
        }
    )


@extend_schema(
    tags=['플래시카드 학습'],
    summary="세션 상세 조회",
    description="플래시카드 학습 세션의 상세 정보를 조회합니다.",
    responses={200: FlashcardSessionDetailSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def flashcard_detail(request, session_id):
    """플래시카드 세션 상세 조회"""
    session = get_object_or_404(
        FlashcardSession.objects.prefetch_related('records__word__translations', 'records__word__examples'),
        id=session_id,
        user=request.user
    )

    return APIResponse.success(
        message='Flashcard session detail',
        data=FlashcardSessionDetailSerializer(session).data
    )


@extend_schema(
    tags=['플래시카드 학습'],
    summary="학습 중단",
    description="진행 중인 플래시카드 학습을 중단합니다.",
    responses={200: FlashcardSessionSerializer},
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def flashcard_abandon(request, session_id):
    """플래시카드 세션 중단 (abandoned)"""
    session = get_object_or_404(FlashcardSession, id=session_id, user=request.user)

    # 이미 완료된 세션은 중단 불가
    if session.is_completed:
        return APIResponse.error(
            message='Session already completed',
            error_code=ErrorCode.VALIDATION_ERROR
        )

    # xAPI Statement: ABANDONED
    from .models import WordCategory
    subcategory_display = session.learning_language.name_ko
    if session.category:
        category_labels = dict(WordCategory.choices)
        subcategory_display = category_labels.get(session.category, session.category)

    # 현재까지의 진행률 계산
    answered_count = session.known_count + session.unknown_count
    progress_rate = (answered_count / session.total_cards) if session.total_cards > 0 else 0

    queue_statement_task({
        'actor_user_id': request.user.id,
        'verb': 'abandoned',
        'object_type': 'flashcard',
        'object_id': f'flashcard/session/{session.id}',
        'result': {
            'score_scaled': progress_rate,
            'score_raw': answered_count,
            'score_max': session.total_cards,
            'completion': False,
        },
        'context': {
            'category': 'flashcard',
            'subcategory': subcategory_display,
            'quiz_type': '일반 학습',
            'session_id': session.id,
            'total_cards': session.total_cards,
            'known_count': session.known_count,
            'unknown_count': session.unknown_count,
            'progress_percentage': round(progress_rate * 100, 1),
            'language_code': session.learning_language.code,
            'language_name': session.learning_language.name_ko,
        }
    })

    return APIResponse.success(
        message='Session abandoned',
        data=FlashcardSessionSerializer(session).data
    )


@extend_schema(
    tags=['플래시카드 학습'],
    summary="학습 히스토리",
    description="사용자의 플래시카드 학습 히스토리를 조회합니다.",
    parameters=[
        OpenApiParameter(name='learning_language', description='학습 언어 ID', required=False, type=int),
        OpenApiParameter(name='is_completed', description='완료 여부', required=False, type=bool),
        OpenApiParameter(name='limit', description='조회 수 (기본 20)', required=False, type=int),
    ],
    responses={200: FlashcardSessionSerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def flashcard_history(request):
    """플래시카드 학습 히스토리"""
    sessions = FlashcardSession.objects.filter(user=request.user)

    learning_language = request.query_params.get('learning_language')
    if learning_language:
        sessions = sessions.filter(learning_language_id=learning_language)

    is_completed = request.query_params.get('is_completed')
    if is_completed is not None:
        sessions = sessions.filter(is_completed=is_completed.lower() == 'true')

    limit = int(request.query_params.get('limit', 20))
    sessions = sessions[:limit]

    return APIResponse.success(
        message='Flashcard history',
        data={
            'sessions': FlashcardSessionSerializer(sessions, many=True).data,
            'total_count': sessions.count()
        }
    )


# =============================================================================
# 단어 퀴즈 초기화 API
# =============================================================================

@extend_schema(
    tags=['단어 퀴즈'],
    summary="언어별 단어 퀴즈 기록 초기화",
    description="특정 언어의 단어 퀴즈 기록을 모두 삭제합니다.",
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'language_code': {
                    'type': 'string',
                    'description': '초기화할 언어 코드 (예: ja, es, en)',
                }
            },
            'required': ['language_code']
        }
    },
    responses={
        200: {
            'description': '초기화 성공',
            'content': {
                'application/json': {
                    'example': {
                        'success': True,
                        'message': 'Word quiz stats reset successfully',
                        'data': {'deleted_quizzes': 10}
                    }
                }
            }
        }
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def word_quiz_reset(request):
    """특정 언어의 퀴즈 기록 초기화 (일본어인 경우 가나 퀴즈도 함께 삭제)"""
    from .models import WordQuiz, GanaQuiz, Language

    language_code = request.data.get('language_code')
    if not language_code:
        return APIResponse.error(
            message='language_code is required',
            error_code=ErrorCode.VALIDATION_ERROR
        )

    # 언어 확인
    try:
        language = Language.objects.get(code=language_code)
    except Language.DoesNotExist:
        return APIResponse.error(
            message=f'Language not found: {language_code}',
            error_code=ErrorCode.NOT_FOUND
        )

    # 해당 사용자의 해당 언어 단어 퀴즈 삭제
    word_deleted_count, _ = WordQuiz.objects.filter(
        user=request.user,
        learning_language=language
    ).delete()

    # 일본어인 경우 가나 퀴즈도 삭제
    gana_deleted_count = 0
    if language_code == 'ja':
        gana_deleted_count, _ = GanaQuiz.objects.filter(
            user=request.user
        ).delete()

    return APIResponse.success(
        message='Quiz stats reset successfully',
        data={
            'deleted_word_quizzes': word_deleted_count,
            'deleted_gana_quizzes': gana_deleted_count,
            'total_deleted': word_deleted_count + gana_deleted_count
        }
    )


# =============================================================================
# 단어 보기 API (학생용)
# =============================================================================

@extend_schema(
    tags=['단어 보기'],
    summary="단어 목록 조회",
    description="""
    학생이 학습 중인 언어의 단어를 검색하고 조회합니다.

    **필터링 옵션:**
    - `language`: 언어 코드 (ja, en, es 등)
    - `category`: 카테고리 (word, hiragana, katakana 등)
    - `part_of_speech`: 품사 (noun, verb, adjective 등)
    - `difficulty_level`: 난이도 (1-5)
    - `search`: 검색어 (단어 텍스트 또는 발음)

    **정렬 옵션:**
    - `order_by`: 정렬 기준 (text, difficulty_level, created_at)
    - `order_dir`: 정렬 방향 (asc, desc)

    **페이지네이션:**
    - `page`: 페이지 번호 (기본: 1)
    - `page_size`: 페이지당 개수 (기본: 20, 최대: 100)
    """,
    parameters=[
        OpenApiParameter(name='language', description='언어 코드', required=False, type=str),
        OpenApiParameter(name='category', description='카테고리', required=False, type=str),
        OpenApiParameter(name='part_of_speech', description='품사', required=False, type=str),
        OpenApiParameter(name='difficulty_level', description='난이도 (1-5)', required=False, type=int),
        OpenApiParameter(name='search', description='검색어', required=False, type=str),
        OpenApiParameter(name='order_by', description='정렬 기준', required=False, type=str),
        OpenApiParameter(name='order_dir', description='정렬 방향 (asc/desc)', required=False, type=str),
        OpenApiParameter(name='page', description='페이지 번호', required=False, type=int),
        OpenApiParameter(name='page_size', description='페이지당 개수', required=False, type=int),
    ],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def word_browse_list(request):
    """학생용 단어 목록 조회"""
    from .serializers import WordBrowseListSerializer
    from accounts.models import Language

    user = request.user
    user_profile = getattr(user, 'profile', None)

    if not user_profile:
        return APIResponse.error(
            message='프로필이 설정되지 않았습니다.',
            error_code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 사용자의 학습 언어 목록
    learning_languages = user_profile.learning_languages.all()
    learning_language_ids = list(learning_languages.values_list('id', flat=True))

    if not learning_language_ids:
        return APIResponse.error(
            message='학습 중인 언어가 없습니다.',
            error_code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND
        )

    # 사용자의 모국어 조회
    COUNTRY_TO_LANGUAGE = {
        'KR': 'ko', 'JP': 'ja', 'US': 'en', 'GB': 'en', 'ES': 'es', 'CN': 'zh',
    }
    native_language = None
    if user_profile.country:
        lang_code = COUNTRY_TO_LANGUAGE.get(user_profile.country.code)
        if lang_code:
            native_language = Language.objects.filter(code=lang_code).first()
    if not native_language:
        native_language = Language.objects.filter(code='ko').first()

    # 카테고리 결정 (기본값: word)
    category = request.query_params.get('category') or WordCategory.WORD

    # 기본 쿼리 (학습 중인 언어의 단어만)
    queryset = Word.objects.filter(
        language_id__in=learning_language_ids,
        category=category,
        is_active=True
    ).select_related('language').prefetch_related('translations')

    # 언어 필터
    language_code = request.query_params.get('language')
    if language_code:
        queryset = queryset.filter(language__code=language_code)

    # 품사 필터
    part_of_speech = request.query_params.get('part_of_speech')
    if part_of_speech:
        queryset = queryset.filter(part_of_speech=part_of_speech)

    # 난이도 필터
    difficulty_level = request.query_params.get('difficulty_level')
    if difficulty_level:
        queryset = queryset.filter(difficulty_level=int(difficulty_level))

    # 검색 (단어 텍스트 또는 발음)
    search = request.query_params.get('search')
    if search:
        queryset = queryset.filter(
            Q(text__icontains=search) | Q(pronunciation__icontains=search)
        )

    # 정렬
    order_by = request.query_params.get('order_by', 'text')
    order_dir = request.query_params.get('order_dir', 'asc')
    valid_order_fields = ['text', 'difficulty_level', 'created_at', 'pronunciation']
    if order_by not in valid_order_fields:
        order_by = 'text'
    if order_dir == 'desc':
        order_by = f'-{order_by}'
    queryset = queryset.order_by(order_by)

    # 페이지네이션
    page = int(request.query_params.get('page', 1))
    page_size = min(int(request.query_params.get('page_size', 20)), 100)
    total_count = queryset.count()
    start = (page - 1) * page_size
    end = start + page_size
    queryset = queryset[start:end]

    serializer_context = {'native_language_id': native_language.id if native_language else None}
    serializer = WordBrowseListSerializer(queryset, many=True, context=serializer_context)

    return APIResponse.success(
        message='Words retrieved',
        data={
            'words': serializer.data,
            'pagination': {
                'page': page,
                'page_size': page_size,
                'total_count': total_count,
                'total_pages': (total_count + page_size - 1) // page_size
            }
        }
    )


@extend_schema(
    tags=['단어 보기'],
    summary="단어 상세 조회",
    description="특정 단어의 상세 정보를 조회합니다. 문법 속성, 예문, 하이라이트 정보가 포함됩니다.",
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def word_browse_detail(request, word_id):
    """학생용 단어 상세 조회"""
    from .serializers import WordBrowseSerializer
    from accounts.models import Language

    user = request.user
    user_profile = getattr(user, 'profile', None)

    if not user_profile:
        return APIResponse.error(
            message='프로필이 설정되지 않았습니다.',
            error_code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 사용자의 학습 언어 목록
    learning_language_ids = list(user_profile.learning_languages.values_list('id', flat=True))

    # 단어 조회 (학습 중인 언어만)
    word = get_object_or_404(
        Word.objects.select_related('language').prefetch_related(
            'translations__language', 'examples__translations__language'
        ),
        pk=word_id,
        language_id__in=learning_language_ids,
        is_active=True
    )

    # 사용자의 모국어 조회
    COUNTRY_TO_LANGUAGE = {
        'KR': 'ko', 'JP': 'ja', 'US': 'en', 'GB': 'en', 'ES': 'es', 'CN': 'zh',
    }
    native_language = None
    if user_profile.country:
        lang_code = COUNTRY_TO_LANGUAGE.get(user_profile.country.code)
        if lang_code:
            native_language = Language.objects.filter(code=lang_code).first()
    if not native_language:
        native_language = Language.objects.filter(code='ko').first()

    serializer_context = {'native_language_id': native_language.id if native_language else None}
    serializer = WordBrowseSerializer(word, context=serializer_context)

    return APIResponse.success(
        message='Word retrieved',
        data=serializer.data
    )


@extend_schema(
    tags=['단어 보기'],
    summary="랜덤 단어 조회",
    description="""
    학습 중인 언어에서 랜덤으로 단어를 조회합니다.

    **옵션:**
    - `language`: 특정 언어로 제한 (언어 코드)
    - `category`: 특정 카테고리로 제한
    - `count`: 반환할 단어 수 (기본: 1, 최대: 10)
    """,
    parameters=[
        OpenApiParameter(name='language', description='언어 코드', required=False, type=str),
        OpenApiParameter(name='category', description='카테고리', required=False, type=str),
        OpenApiParameter(name='count', description='단어 수 (1-10)', required=False, type=int),
    ],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def word_browse_random(request):
    """랜덤 단어 조회"""
    from .serializers import WordBrowseSerializer
    from accounts.models import Language

    user = request.user
    user_profile = getattr(user, 'profile', None)

    if not user_profile:
        return APIResponse.error(
            message='프로필이 설정되지 않았습니다.',
            error_code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 사용자의 학습 언어 목록
    learning_language_ids = list(user_profile.learning_languages.values_list('id', flat=True))

    if not learning_language_ids:
        return APIResponse.error(
            message='학습 중인 언어가 없습니다.',
            error_code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND
        )

    # 사용자의 모국어 조회
    COUNTRY_TO_LANGUAGE = {
        'KR': 'ko', 'JP': 'ja', 'US': 'en', 'GB': 'en', 'ES': 'es', 'CN': 'zh',
    }
    native_language = None
    if user_profile.country:
        lang_code = COUNTRY_TO_LANGUAGE.get(user_profile.country.code)
        if lang_code:
            native_language = Language.objects.filter(code=lang_code).first()
    if not native_language:
        native_language = Language.objects.filter(code='ko').first()

    # 카테고리 결정 (기본값: word)
    category = request.query_params.get('category') or WordCategory.WORD

    # 기본 쿼리 (학습 중인 언어의 단어)
    queryset = Word.objects.filter(
        language_id__in=learning_language_ids,
        category=category,
        is_active=True
    ).select_related('language').prefetch_related(
        'translations__language', 'examples__translations__language'
    )

    # 언어 필터
    language_code = request.query_params.get('language')
    if language_code:
        queryset = queryset.filter(language__code=language_code)

    # 단어 수
    count = min(int(request.query_params.get('count', 1)), 10)

    # 랜덤 선택
    word_ids = list(queryset.values_list('id', flat=True))
    if not word_ids:
        return APIResponse.error(
            message='조건에 맞는 단어가 없습니다.',
            error_code=ErrorCode.NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND
        )

    selected_count = min(count, len(word_ids))
    random_ids = random.sample(word_ids, selected_count)

    # 선택된 단어 조회
    words = Word.objects.filter(id__in=random_ids).select_related('language').prefetch_related(
        'translations__language', 'examples__translations__language'
    )

    serializer_context = {'native_language_id': native_language.id if native_language else None}
    serializer = WordBrowseSerializer(words, many=True, context=serializer_context)

    return APIResponse.success(
        message='Random words retrieved',
        data={
            'words': serializer.data,
            'count': len(serializer.data)
        }
    )


# =============================================================================
# 단어장 API
# =============================================================================

@extend_schema(
    summary='내 단어장 목록 조회',
    description='로그인한 사용자의 단어장 목록을 조회합니다.',
    responses={200: VocabularyListSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_vocabularies(request):
    """내 단어장 목록 조회"""
    vocabularies = Vocabulary.objects.filter(
        user=request.user,
        is_active=True
    ).select_related('language').annotate(
        word_count=Count('words')
    ).order_by('-created_at')

    serializer = VocabularyListSerializer(vocabularies, many=True)
    return APIResponse.success(
        message='Vocabularies retrieved',
        data={'vocabularies': serializer.data}
    )


@extend_schema(
    summary='단어장 생성',
    description='새로운 단어장을 생성합니다.',
    request=VocabularyCreateSerializer,
    responses={201: VocabularyListSerializer}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_vocabulary(request):
    """단어장 생성"""
    serializer = VocabularyCreateSerializer(
        data=request.data,
        context={'request': request}
    )

    if not serializer.is_valid():
        return APIResponse.error(
            message='Invalid data',
            error_code=ErrorCode.VALIDATION_ERROR,
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    vocabulary = serializer.save()

    # Re-query with word_count annotation
    vocabulary = Vocabulary.objects.filter(id=vocabulary.id).annotate(
        word_count=Count('words')
    ).first()

    response_serializer = VocabularyListSerializer(vocabulary)
    return APIResponse.success(
        message='Vocabulary created',
        data={'vocabulary': response_serializer.data},
        status_code=status.HTTP_201_CREATED
    )


@extend_schema(
    summary='단어장 상세 조회',
    description='특정 단어장의 상세 정보와 포함된 단어 목록을 조회합니다.',
    responses={200: VocabularyDetailSerializer}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_vocabulary(request, vocabulary_id):
    """단어장 상세 조회"""
    vocabulary = get_object_or_404(
        Vocabulary.objects.annotate(word_count=Count('words')),
        id=vocabulary_id,
        user=request.user
    )

    serializer = VocabularyDetailSerializer(vocabulary)

    return APIResponse.success(
        message='Vocabulary retrieved',
        data={'vocabulary': serializer.data}
    )


@extend_schema(
    summary='단어장 수정',
    description='단어장의 이름, 설명, 활성화 상태를 수정합니다.',
    request=VocabularyCreateSerializer,
    responses={200: VocabularyListSerializer}
)
@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def update_vocabulary(request, vocabulary_id):
    """단어장 수정"""
    vocabulary = get_object_or_404(
        Vocabulary,
        id=vocabulary_id,
        user=request.user
    )

    partial = request.method == 'PATCH'
    serializer = VocabularyCreateSerializer(
        vocabulary,
        data=request.data,
        partial=partial,
        context={'request': request}
    )

    if not serializer.is_valid():
        return APIResponse.error(
            message='Invalid data',
            error_code=ErrorCode.VALIDATION_ERROR,
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    vocabulary = serializer.save()

    # Re-query with word_count annotation
    vocabulary = Vocabulary.objects.filter(id=vocabulary.id).annotate(
        word_count=Count('words')
    ).first()

    response_serializer = VocabularyListSerializer(vocabulary)

    return APIResponse.success(
        message='Vocabulary updated',
        data={'vocabulary': response_serializer.data}
    )


@extend_schema(
    summary='단어장 삭제',
    description='단어장을 삭제합니다 (소프트 삭제: is_active=False).',
    responses={200: dict}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_vocabulary(request, vocabulary_id):
    """단어장 삭제 (소프트 삭제)"""
    vocabulary = get_object_or_404(
        Vocabulary,
        id=vocabulary_id,
        user=request.user
    )

    vocabulary.is_active = False
    vocabulary.save()

    return APIResponse.success(
        message='Vocabulary deleted'
    )


@extend_schema(
    summary='단어장에 단어 추가',
    description='특정 단어장에 단어를 추가합니다.',
    request=AddWordToVocabularySerializer,
    responses={201: VocabularyWordSerializer}
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def add_word_to_vocabulary(request, vocabulary_id):
    """단어장에 단어 추가"""
    vocabulary = get_object_or_404(
        Vocabulary,
        id=vocabulary_id,
        user=request.user
    )

    serializer = AddWordToVocabularySerializer(data=request.data)
    if not serializer.is_valid():
        return APIResponse.error(
            message='Invalid data',
            error_code=ErrorCode.VALIDATION_ERROR,
            errors=serializer.errors,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    word_id = serializer.validated_data['word_id']
    notes = serializer.validated_data.get('notes', '')

    # 단어 조회
    word = get_object_or_404(Word, id=word_id)

    # 단어의 언어와 단어장의 언어가 일치하는지 확인
    if word.language_id != vocabulary.language_id:
        return APIResponse.error(
            message=f'Language mismatch: This vocabulary is for {vocabulary.language.name_ko}, but the word is in {word.language.name_ko}',
            error_code=ErrorCode.VALIDATION_ERROR,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 이미 추가되어 있는지 확인
    if VocabularyWord.objects.filter(vocabulary=vocabulary, word_id=word_id).exists():
        return APIResponse.error(
            message='Word already exists in vocabulary',
            error_code=ErrorCode.DUPLICATE_RESOURCE,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # 단어장에 추가
    vocab_word = VocabularyWord.objects.create(
        vocabulary=vocabulary,
        word_id=word_id,
        notes=notes
    )

    response_serializer = VocabularyWordSerializer(vocab_word)
    return APIResponse.success(
        message='Word added to vocabulary',
        data={'vocabulary_word': response_serializer.data},
        status_code=status.HTTP_201_CREATED
    )


@extend_schema(
    summary='단어장에서 단어 제거',
    description='특정 단어장에서 단어를 제거합니다.',
    responses={200: dict}
)
@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def remove_word_from_vocabulary(request, vocabulary_id, word_id):
    """단어장에서 단어 제거"""
    vocabulary = get_object_or_404(
        Vocabulary,
        id=vocabulary_id,
        user=request.user
    )

    vocab_word = get_object_or_404(
        VocabularyWord,
        vocabulary=vocabulary,
        word_id=word_id
    )

    vocab_word.delete()

    return APIResponse.success(
        message='Word removed from vocabulary'
    )


@extend_schema(
    summary='단어가 속한 내 단어장 목록',
    description='특정 단어가 속한 내 단어장 목록을 조회합니다.',
    responses={200: VocabularyListSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_word_vocabularies(request, word_id):
    """이 단어가 속한 내 단어장 목록"""
    word = get_object_or_404(Word, id=word_id)

    vocabularies = Vocabulary.objects.filter(
        user=request.user,
        words=word,
        is_active=True
    ).select_related('language').annotate(
        word_count=Count('words')
    )

    serializer = VocabularyListSerializer(vocabularies, many=True)
    return APIResponse.success(
        message='Vocabularies containing this word retrieved',
        data={'vocabularies': serializer.data}
    )


@extend_schema(
    summary='학습한 단어 목록 조회',
    description='학습하기에서 본 단어들을 조회합니다. (FlashcardRecord의 viewed_at이 null이 아닌 단어들)',
    parameters=[
        OpenApiParameter(
            name='learning_language',
            type=str,
            location=OpenApiParameter.QUERY,
            description='학습 언어 코드 (예: es, ja)',
            required=False
        )
    ],
    responses={200: WordListSerializer(many=True)}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_learned_words(request):
    """학습한 단어 목록 조회"""
    learning_language_code = request.query_params.get('learning_language')

    # FlashcardRecord에서 viewed_at이 null이 아닌 단어 ID 조회
    query = FlashcardRecord.objects.filter(
        session__user=request.user,
        viewed_at__isnull=False
    )

    # 언어 필터링
    if learning_language_code:
        query = query.filter(session__learning_language__code=learning_language_code)

    # 중복 제거된 단어 ID 목록
    learned_word_ids = query.values_list('word_id', flat=True).distinct()

    # 단어 조회
    words = Word.objects.filter(
        id__in=learned_word_ids
    ).select_related(
        'language'
    ).prefetch_related(
        'translations__language',
        'examples__translations__language'
    ).order_by('-updated_at')

    serializer = WordSerializer(words, many=True, context={'request': request})

    return APIResponse.success(
        message='Learned words retrieved successfully',
        data={
            'words': serializer.data,
            'count': words.count()
        }
    )
