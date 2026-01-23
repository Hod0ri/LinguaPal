from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User, Language
from .models import (
    Word, WordTranslation, Example, ExampleTranslation,
    PartOfSpeech, WordCategory,
    GanaQuiz, GanaQuizQuestion, UserGanaStats,
    GanaCharacterSet, GanaQuizType, GanaQuizQuestionCount
)


class WordModelTest(TestCase):
    """단어 모델 테스트"""

    def setUp(self):
        self.language = Language.objects.create(
            code='es',
            name_ko='스페인어',
            name_en='Spanish'
        )

    def test_word_creation(self):
        """단어 생성 테스트"""
        word = Word.objects.create(
            language=self.language,
            text='libro',
            category=WordCategory.WORD,
            part_of_speech=PartOfSpeech.NOUN,
            pronunciation='/ˈli.βɾo/',
            grammar={'gender': 'masculine', 'plural': 'libros'},
            difficulty_level=1
        )

        self.assertEqual(word.text, 'libro')
        self.assertEqual(word.category, WordCategory.WORD)
        self.assertEqual(word.part_of_speech, PartOfSpeech.NOUN)
        self.assertEqual(word.grammar['gender'], 'masculine')
        self.assertTrue(word.is_active)

    def test_hiragana_creation(self):
        """히라가나 문자 생성 테스트"""
        japanese = Language.objects.create(
            code='ja',
            name_ko='일본어',
            name_en='Japanese'
        )
        char = Word.objects.create(
            language=japanese,
            text='あ',
            category=WordCategory.HIRAGANA,
            part_of_speech=PartOfSpeech.CHARACTER,
            pronunciation='a',
            grammar={'romanji': 'a', 'row': 'あ행'},
            order=1,
            difficulty_level=1
        )

        self.assertEqual(char.text, 'あ')
        self.assertEqual(char.category, WordCategory.HIRAGANA)
        self.assertEqual(char.part_of_speech, PartOfSpeech.CHARACTER)
        self.assertEqual(char.grammar['romanji'], 'a')
        self.assertEqual(char.order, 1)

    def test_word_str(self):
        """단어 문자열 표현 테스트"""
        word = Word.objects.create(
            language=self.language,
            text='libro',
            part_of_speech=PartOfSpeech.NOUN
        )
        self.assertEqual(str(word), 'libro (es)')


class WordTranslationModelTest(TestCase):
    """단어 번역 모델 테스트"""

    def setUp(self):
        self.spanish = Language.objects.create(
            code='es',
            name_ko='스페인어',
            name_en='Spanish'
        )
        self.korean = Language.objects.create(
            code='ko',
            name_ko='한국어',
            name_en='Korean'
        )
        self.word = Word.objects.create(
            language=self.spanish,
            text='libro',
            part_of_speech=PartOfSpeech.NOUN
        )

    def test_word_translation_creation(self):
        """단어 번역 생성 테스트"""
        translation = WordTranslation.objects.create(
            word=self.word,
            language=self.korean,
            translated_text='책',
            notes='일반적인 책을 의미'
        )

        self.assertEqual(translation.translated_text, '책')
        self.assertEqual(translation.word, self.word)

    def test_word_translation_str(self):
        """단어 번역 문자열 표현 테스트"""
        translation = WordTranslation.objects.create(
            word=self.word,
            language=self.korean,
            translated_text='책'
        )
        self.assertEqual(str(translation), 'libro → 책 (ko)')

    def test_unique_constraint(self):
        """같은 단어에 같은 언어로 중복 번역 방지"""
        WordTranslation.objects.create(
            word=self.word,
            language=self.korean,
            translated_text='책'
        )

        with self.assertRaises(Exception):
            WordTranslation.objects.create(
                word=self.word,
                language=self.korean,
                translated_text='서적'
            )


class ExampleModelTest(TestCase):
    """예문 모델 테스트"""

    def setUp(self):
        self.language = Language.objects.create(
            code='es',
            name_ko='스페인어',
            name_en='Spanish'
        )
        self.word = Word.objects.create(
            language=self.language,
            text='libro',
            part_of_speech=PartOfSpeech.NOUN
        )

    def test_example_creation(self):
        """예문 생성 테스트"""
        example = Example.objects.create(
            word=self.word,
            sentence='El libro está en la mesa.',
            highlight_indices=[3, 8]
        )

        self.assertEqual(example.sentence, 'El libro está en la mesa.')
        self.assertEqual(example.highlight_indices, [3, 8])

    def test_example_str(self):
        """예문 문자열 표현 테스트"""
        example = Example.objects.create(
            word=self.word,
            sentence='El libro está en la mesa.',
        )
        # 모델의 __str__은 sentence[:50]...를 반환
        self.assertIn('libro:', str(example))
        self.assertIn('El libro', str(example))


class ExampleTranslationModelTest(TestCase):
    """예문 번역 모델 테스트"""

    def setUp(self):
        self.spanish = Language.objects.create(
            code='es',
            name_ko='스페인어',
            name_en='Spanish'
        )
        self.korean = Language.objects.create(
            code='ko',
            name_ko='한국어',
            name_en='Korean'
        )
        self.word = Word.objects.create(
            language=self.spanish,
            text='libro',
            part_of_speech=PartOfSpeech.NOUN
        )
        self.example = Example.objects.create(
            word=self.word,
            sentence='El libro está en la mesa.'
        )

    def test_example_translation_creation(self):
        """예문 번역 생성 테스트"""
        translation = ExampleTranslation.objects.create(
            example=self.example,
            language=self.korean,
            translated_sentence='책이 테이블 위에 있다.'
        )

        self.assertEqual(translation.translated_sentence, '책이 테이블 위에 있다.')

    def test_example_translation_str(self):
        """예문 번역 문자열 표현 테스트"""
        translation = ExampleTranslation.objects.create(
            example=self.example,
            language=self.korean,
            translated_sentence='책이 테이블 위에 있다.'
        )
        # 모델의 __str__은 sentence[:30]... → translated[:30]...를 반환
        self.assertIn('El libro', str(translation))
        self.assertIn('책이 테이블', str(translation))


# =============================================================================
# Admin API 테스트
# =============================================================================

class AdminWordAPITestBase(APITestCase):
    """Admin Word API 테스트 베이스 클래스"""

    def setUp(self):
        self.client = APIClient()

        # 사용자 생성
        self.admin_user = User.objects.create_user(
            username='admin',
            email='admin@example.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass123',
            role=User.Role.STAFF
        )
        self.normal_user = User.objects.create_user(
            username='user',
            email='user@example.com',
            password='testpass123',
            role=User.Role.USER
        )

        # 언어 생성
        self.spanish = Language.objects.create(
            code='es',
            name_ko='스페인어',
            name_en='Spanish'
        )
        self.korean = Language.objects.create(
            code='ko',
            name_ko='한국어',
            name_en='Korean'
        )
        self.english = Language.objects.create(
            code='en',
            name_ko='영어',
            name_en='English'
        )

    def _get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def _authenticate_as(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._get_token(user)}')


class AdminWordListCreateAPITest(AdminWordAPITestBase):
    """단어 목록 조회 및 생성 API 테스트"""

    def test_admin_can_list_words(self):
        """Admin은 단어 목록 조회 가능"""
        Word.objects.create(
            language=self.spanish,
            text='libro',
            part_of_speech=PartOfSpeech.NOUN
        )

        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['words']), 1)

    def test_staff_can_list_words(self):
        """Staff는 단어 목록 조회 가능"""
        self._authenticate_as(self.staff_user)
        url = reverse('words:admin_word_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_normal_user_cannot_list_words(self):
        """일반 사용자는 단어 목록 조회 불가"""
        self._authenticate_as(self.normal_user)
        url = reverse('words:admin_word_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_list_words(self):
        """인증되지 않은 사용자는 조회 불가"""
        url = reverse('words:admin_word_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_admin_can_create_word(self):
        """Admin은 단어 생성 가능"""
        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_create')
        data = {
            'language': self.spanish.id,
            'text': 'libro',
            'part_of_speech': 'noun',
            'pronunciation': '/ˈli.βɾo/',
            'grammar': {
                'gender': 'masculine',
                'plural': 'libros'
            },
            'difficulty_level': 1
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['text'], 'libro')
        self.assertEqual(Word.objects.count(), 1)

    def test_staff_can_create_word(self):
        """Staff는 단어 생성 가능"""
        self._authenticate_as(self.staff_user)
        url = reverse('words:admin_word_create')
        data = {
            'language': self.spanish.id,
            'text': 'casa',
            'part_of_speech': 'noun',
            'difficulty_level': 1
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_create_word_with_translations_and_examples(self):
        """단어 생성 시 번역과 예문 함께 생성"""
        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_create')
        data = {
            'language': self.spanish.id,
            'text': 'libro',
            'part_of_speech': 'noun',
            'difficulty_level': 1,
            'translations': [
                {'language': self.korean.id, 'translated_text': '책', 'notes': ''}
            ],
            'examples': [
                {
                    'sentence': 'El libro está en la mesa.',
                    'highlight_indices': [3, 8],
                    'translations': [
                        {'language': self.korean.id, 'translated_sentence': '책이 테이블 위에 있다.'}
                    ]
                }
            ]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data['data']['translations']), 1)
        self.assertEqual(len(response.data['data']['examples']), 1)

    def test_create_word_validation_error(self):
        """단어 생성 시 유효성 검사 실패"""
        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_create')
        data = {
            'language': self.spanish.id,
            'text': 'libro',
            'part_of_speech': 'noun',
            'difficulty_level': 10  # 유효 범위 초과 (1-5)
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_filter_words_by_language(self):
        """언어로 단어 필터링"""
        Word.objects.create(language=self.spanish, text='libro', part_of_speech=PartOfSpeech.NOUN)
        Word.objects.create(language=self.english, text='book', part_of_speech=PartOfSpeech.NOUN)

        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_list')
        response = self.client.get(url, {'language': self.spanish.id})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['words']), 1)
        self.assertEqual(response.data['data']['words'][0]['text'], 'libro')

    def test_filter_words_by_part_of_speech(self):
        """품사로 단어 필터링"""
        Word.objects.create(language=self.spanish, text='libro', part_of_speech=PartOfSpeech.NOUN)
        Word.objects.create(language=self.spanish, text='leer', part_of_speech=PartOfSpeech.VERB)

        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_list')
        response = self.client.get(url, {'part_of_speech': 'verb'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['words']), 1)
        self.assertEqual(response.data['data']['words'][0]['text'], 'leer')

    def test_search_words(self):
        """단어 검색"""
        Word.objects.create(language=self.spanish, text='libro', part_of_speech=PartOfSpeech.NOUN)
        Word.objects.create(language=self.spanish, text='libreta', part_of_speech=PartOfSpeech.NOUN)
        Word.objects.create(language=self.spanish, text='casa', part_of_speech=PartOfSpeech.NOUN)

        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_list')
        response = self.client.get(url, {'search': 'libr'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['words']), 2)

    def test_filter_words_by_category(self):
        """카테고리로 단어 필터링"""
        japanese = Language.objects.create(code='ja', name_ko='일본어', name_en='Japanese')
        Word.objects.create(language=japanese, text='あ', category=WordCategory.HIRAGANA, part_of_speech=PartOfSpeech.CHARACTER)
        Word.objects.create(language=japanese, text='ア', category=WordCategory.KATAKANA, part_of_speech=PartOfSpeech.CHARACTER)
        Word.objects.create(language=japanese, text='本', category=WordCategory.WORD, part_of_speech=PartOfSpeech.NOUN)

        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_list')
        response = self.client.get(url, {'category': 'hiragana'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['words']), 1)
        self.assertEqual(response.data['data']['words'][0]['text'], 'あ')


class AdminWordDetailAPITest(AdminWordAPITestBase):
    """단어 상세 조회/수정/삭제 API 테스트"""

    def setUp(self):
        super().setUp()
        self.word = Word.objects.create(
            language=self.spanish,
            text='libro',
            part_of_speech=PartOfSpeech.NOUN,
            difficulty_level=1
        )

    def test_admin_can_get_word_detail(self):
        """Admin은 단어 상세 조회 가능"""
        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_detail', kwargs={'pk': self.word.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['text'], 'libro')

    def test_admin_can_update_word(self):
        """Admin은 단어 수정 가능"""
        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_update', kwargs={'pk': self.word.pk})
        data = {
            'text': 'libro actualizado',
            'difficulty_level': 3
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.word.refresh_from_db()
        self.assertEqual(self.word.text, 'libro actualizado')
        self.assertEqual(self.word.difficulty_level, 3)

    def test_admin_can_delete_word(self):
        """Admin은 단어 삭제 가능"""
        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_delete', kwargs={'pk': self.word.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Word.objects.count(), 0)

    def test_get_nonexistent_word_returns_404(self):
        """존재하지 않는 단어 조회 시 404"""
        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_detail', kwargs={'pk': 9999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class AdminWordTranslationAPITest(AdminWordAPITestBase):
    """단어 번역 API 테스트"""

    def setUp(self):
        super().setUp()
        self.word = Word.objects.create(
            language=self.spanish,
            text='libro',
            part_of_speech=PartOfSpeech.NOUN
        )

    def test_admin_can_add_translation(self):
        """Admin은 번역 추가 가능"""
        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_translation_create', kwargs={'word_id': self.word.pk})
        data = {
            'language': self.korean.id,
            'translated_text': '책',
            'notes': '일반적인 책'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(WordTranslation.objects.count(), 1)

    def test_admin_can_list_translations(self):
        """Admin은 번역 목록 조회 가능"""
        WordTranslation.objects.create(
            word=self.word,
            language=self.korean,
            translated_text='책'
        )

        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_translation_list', kwargs={'word_id': self.word.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['translations']), 1)

    def test_admin_can_update_translation(self):
        """Admin은 번역 수정 가능"""
        translation = WordTranslation.objects.create(
            word=self.word,
            language=self.korean,
            translated_text='책'
        )

        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_translation_update',
                      kwargs={'word_id': self.word.pk, 'translation_id': translation.pk})
        data = {
            'translated_text': '서적'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        translation.refresh_from_db()
        self.assertEqual(translation.translated_text, '서적')

    def test_admin_can_delete_translation(self):
        """Admin은 번역 삭제 가능"""
        translation = WordTranslation.objects.create(
            word=self.word,
            language=self.korean,
            translated_text='책'
        )

        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_word_translation_delete',
                      kwargs={'word_id': self.word.pk, 'translation_id': translation.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(WordTranslation.objects.count(), 0)


class AdminExampleAPITest(AdminWordAPITestBase):
    """예문 API 테스트"""

    def setUp(self):
        super().setUp()
        self.word = Word.objects.create(
            language=self.spanish,
            text='libro',
            part_of_speech=PartOfSpeech.NOUN
        )

    def test_admin_can_add_example(self):
        """Admin은 예문 추가 가능"""
        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_example_create', kwargs={'word_id': self.word.pk})
        data = {
            'sentence': 'El libro está en la mesa.',
            'highlight_indices': [3, 8]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Example.objects.count(), 1)

    def test_admin_can_add_example_with_translation(self):
        """Admin은 번역과 함께 예문 추가 가능"""
        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_example_create', kwargs={'word_id': self.word.pk})
        data = {
            'sentence': 'El libro está en la mesa.',
            'translations': [
                {'language': self.korean.id, 'translated_sentence': '책이 테이블 위에 있다.'}
            ]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExampleTranslation.objects.count(), 1)

    def test_admin_can_list_examples(self):
        """Admin은 예문 목록 조회 가능"""
        Example.objects.create(
            word=self.word,
            sentence='El libro está en la mesa.'
        )

        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_example_list', kwargs={'word_id': self.word.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['examples']), 1)

    def test_admin_can_update_example(self):
        """Admin은 예문 수정 가능"""
        example = Example.objects.create(
            word=self.word,
            sentence='El libro está en la mesa.'
        )

        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_example_update',
                      kwargs={'word_id': self.word.pk, 'example_id': example.pk})
        data = {
            'sentence': 'El libro rojo está en la mesa.'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        example.refresh_from_db()
        self.assertIn('rojo', example.sentence)

    def test_admin_can_delete_example(self):
        """Admin은 예문 삭제 가능"""
        example = Example.objects.create(
            word=self.word,
            sentence='El libro está en la mesa.'
        )

        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_example_delete',
                      kwargs={'word_id': self.word.pk, 'example_id': example.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(Example.objects.count(), 0)


class AdminExampleTranslationAPITest(AdminWordAPITestBase):
    """예문 번역 API 테스트"""

    def setUp(self):
        super().setUp()
        self.word = Word.objects.create(
            language=self.spanish,
            text='libro',
            part_of_speech=PartOfSpeech.NOUN
        )
        self.example = Example.objects.create(
            word=self.word,
            sentence='El libro está en la mesa.'
        )

    def test_admin_can_add_example_translation(self):
        """Admin은 예문 번역 추가 가능"""
        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_example_translation_create',
                      kwargs={'word_id': self.word.pk, 'example_id': self.example.pk})
        data = {
            'language': self.korean.id,
            'translated_sentence': '책이 테이블 위에 있다.'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(ExampleTranslation.objects.count(), 1)

    def test_admin_can_update_example_translation(self):
        """Admin은 예문 번역 수정 가능"""
        translation = ExampleTranslation.objects.create(
            example=self.example,
            language=self.korean,
            translated_sentence='책이 테이블 위에 있다.'
        )

        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_example_translation_update',
                      kwargs={
                          'word_id': self.word.pk,
                          'example_id': self.example.pk,
                          'translation_id': translation.pk
                      })
        data = {
            'translated_sentence': '그 책은 테이블 위에 있다.'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        translation.refresh_from_db()
        self.assertIn('그 책', translation.translated_sentence)

    def test_admin_can_delete_example_translation(self):
        """Admin은 예문 번역 삭제 가능"""
        translation = ExampleTranslation.objects.create(
            example=self.example,
            language=self.korean,
            translated_sentence='책이 테이블 위에 있다.'
        )

        self._authenticate_as(self.admin_user)
        url = reverse('words:admin_example_translation_delete',
                      kwargs={
                          'word_id': self.word.pk,
                          'example_id': self.example.pk,
                          'translation_id': translation.pk
                      })
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(ExampleTranslation.objects.count(), 0)


# =============================================================================
# 가나 퀴즈 모델 테스트
# =============================================================================

class GanaQuizModelTest(TestCase):
    """가나 퀴즈 모델 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.japanese = Language.objects.create(
            code='ja',
            name_ko='일본어',
            name_en='Japanese'
        )

    def test_gana_quiz_creation(self):
        """가나 퀴즈 생성 테스트"""
        quiz = GanaQuiz.objects.create(
            user=self.user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.GANA_TO_ROMAJI,
            question_count_setting=GanaQuizQuestionCount.TEN,
            total_questions=10
        )

        self.assertEqual(quiz.character_set, GanaCharacterSet.HIRAGANA)
        self.assertEqual(quiz.quiz_type, GanaQuizType.GANA_TO_ROMAJI)
        self.assertEqual(quiz.total_questions, 10)
        self.assertEqual(quiz.correct_count, 0)
        self.assertFalse(quiz.is_completed)

    def test_score_percentage(self):
        """점수 백분율 계산 테스트"""
        quiz = GanaQuiz.objects.create(
            user=self.user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.GANA_TO_ROMAJI,
            question_count_setting=GanaQuizQuestionCount.TEN,
            total_questions=10,
            correct_count=7
        )

        self.assertEqual(quiz.score_percentage, 70.0)

    def test_score_percentage_zero_questions(self):
        """문제 수가 0일 때 점수 계산"""
        quiz = GanaQuiz.objects.create(
            user=self.user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.GANA_TO_ROMAJI,
            question_count_setting=GanaQuizQuestionCount.ALL,
            total_questions=0
        )

        self.assertEqual(quiz.score_percentage, 0)


class GanaQuizQuestionModelTest(TestCase):
    """가나 퀴즈 문제 모델 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.japanese = Language.objects.create(
            code='ja',
            name_ko='일본어',
            name_en='Japanese'
        )
        self.hiragana_a = Word.objects.create(
            language=self.japanese,
            text='あ',
            category=WordCategory.HIRAGANA,
            part_of_speech=PartOfSpeech.CHARACTER,
            pronunciation='a',
            order=1
        )
        self.quiz = GanaQuiz.objects.create(
            user=self.user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.GANA_TO_ROMAJI,
            question_count_setting=GanaQuizQuestionCount.TEN,
            total_questions=10
        )

    def test_question_creation(self):
        """퀴즈 문제 생성 테스트"""
        question = GanaQuizQuestion.objects.create(
            quiz=self.quiz,
            word=self.hiragana_a,
            question_number=1
        )

        self.assertEqual(question.question_number, 1)
        self.assertEqual(question.word, self.hiragana_a)
        self.assertIsNone(question.is_correct)

    def test_correct_answer_gana_to_romaji(self):
        """가나→로마자 퀴즈의 정답 반환"""
        question = GanaQuizQuestion.objects.create(
            quiz=self.quiz,
            word=self.hiragana_a,
            question_number=1
        )

        self.assertEqual(question.correct_answer, 'a')

    def test_correct_answer_romaji_to_gana(self):
        """로마자→가나 퀴즈의 정답 반환"""
        quiz = GanaQuiz.objects.create(
            user=self.user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.ROMAJI_TO_GANA_INPUT,
            question_count_setting=GanaQuizQuestionCount.TEN,
            total_questions=10
        )
        question = GanaQuizQuestion.objects.create(
            quiz=quiz,
            word=self.hiragana_a,
            question_number=1
        )

        self.assertEqual(question.correct_answer, 'あ')


class UserGanaStatsModelTest(TestCase):
    """사용자 가나 통계 모델 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.japanese = Language.objects.create(
            code='ja',
            name_ko='일본어',
            name_en='Japanese'
        )
        self.hiragana_a = Word.objects.create(
            language=self.japanese,
            text='あ',
            category=WordCategory.HIRAGANA,
            part_of_speech=PartOfSpeech.CHARACTER,
            pronunciation='a'
        )

    def test_stats_creation(self):
        """통계 생성 테스트"""
        stats = UserGanaStats.objects.create(
            user=self.user,
            word=self.hiragana_a,
            total_attempts=10,
            correct_count=8,
            incorrect_count=2
        )

        self.assertEqual(stats.total_attempts, 10)
        self.assertEqual(stats.correct_count, 8)
        self.assertEqual(stats.accuracy, 80.0)

    def test_accuracy_zero_attempts(self):
        """시도 횟수가 0일 때 정답률"""
        stats = UserGanaStats.objects.create(
            user=self.user,
            word=self.hiragana_a
        )

        self.assertEqual(stats.accuracy, 0)


# =============================================================================
# 가나 퀴즈 API 테스트
# =============================================================================

class GanaQuizAPITestBase(APITestCase):
    """가나 퀴즈 API 테스트 베이스 클래스"""

    def setUp(self):
        self.client = APIClient()

        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        self.japanese = Language.objects.create(
            code='ja',
            name_ko='일본어',
            name_en='Japanese'
        )

        # 히라가나 문자 생성 (테스트용 10개)
        hiragana_data = [
            ('あ', 'a', 1), ('い', 'i', 2), ('う', 'u', 3),
            ('え', 'e', 4), ('お', 'o', 5), ('か', 'ka', 6),
            ('き', 'ki', 7), ('く', 'ku', 8), ('け', 'ke', 9),
            ('こ', 'ko', 10)
        ]
        self.hiragana_chars = []
        for text, pronunciation, order in hiragana_data:
            char = Word.objects.create(
                language=self.japanese,
                text=text,
                category=WordCategory.HIRAGANA,
                part_of_speech=PartOfSpeech.CHARACTER,
                pronunciation=pronunciation,
                order=order
            )
            self.hiragana_chars.append(char)

        # 가타카나 문자 생성 (테스트용 5개)
        katakana_data = [
            ('ア', 'a', 1), ('イ', 'i', 2), ('ウ', 'u', 3),
            ('エ', 'e', 4), ('オ', 'o', 5)
        ]
        self.katakana_chars = []
        for text, pronunciation, order in katakana_data:
            char = Word.objects.create(
                language=self.japanese,
                text=text,
                category=WordCategory.KATAKANA,
                part_of_speech=PartOfSpeech.CHARACTER,
                pronunciation=pronunciation,
                order=order
            )
            self.katakana_chars.append(char)

    def _get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def _authenticate_as(self, user):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._get_token(user)}')


class GanaQuizStartAPITest(GanaQuizAPITestBase):
    """퀴즈 시작 API 테스트"""

    def test_start_hiragana_quiz(self):
        """히라가나 퀴즈 시작"""
        self._authenticate_as(self.user)
        url = reverse('words:quiz_start')
        data = {
            'character_set': 'hiragana',
            'quiz_type': 'gana_to_romaji',
            'question_count': 10
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertIn('quiz', response.data['data'])
        self.assertIn('current_question', response.data['data'])
        self.assertEqual(response.data['data']['quiz']['total_questions'], 10)

    def test_start_katakana_quiz(self):
        """가타카나 퀴즈 시작"""
        self._authenticate_as(self.user)
        url = reverse('words:quiz_start')
        data = {
            'character_set': 'katakana',
            'quiz_type': 'romaji_to_gana_select',
            'question_count': 10
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 가타카나는 5개뿐이므로 5문제
        self.assertEqual(response.data['data']['quiz']['total_questions'], 5)

    def test_start_all_characters_quiz(self):
        """전체 문자 퀴즈 시작"""
        self._authenticate_as(self.user)
        url = reverse('words:quiz_start')
        data = {
            'character_set': 'all',
            'quiz_type': 'gana_to_romaji',
            'question_count': 0  # 전체
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 히라가나 10개 + 가타카나 5개 = 15개
        self.assertEqual(response.data['data']['quiz']['total_questions'], 15)

    def test_start_quiz_with_choices(self):
        """선택형 퀴즈 시작 시 선택지 생성 확인"""
        self._authenticate_as(self.user)
        url = reverse('words:quiz_start')
        data = {
            'character_set': 'hiragana',
            'quiz_type': 'romaji_to_gana_select',
            'question_count': 10
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        current_question = response.data['data']['current_question']
        self.assertIn('choices', current_question)
        self.assertEqual(len(current_question['choices']), 3)

    def test_start_quiz_unauthenticated(self):
        """인증되지 않은 사용자 퀴즈 시작 불가"""
        url = reverse('words:quiz_start')
        data = {
            'character_set': 'hiragana',
            'quiz_type': 'gana_to_romaji',
            'question_count': 10
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_start_quiz_invalid_data(self):
        """잘못된 데이터로 퀴즈 시작"""
        self._authenticate_as(self.user)
        url = reverse('words:quiz_start')
        data = {
            'character_set': 'invalid',
            'quiz_type': 'gana_to_romaji',
            'question_count': 10
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GanaQuizAnswerAPITest(GanaQuizAPITestBase):
    """퀴즈 답변 API 테스트"""

    def setUp(self):
        super().setUp()
        self._authenticate_as(self.user)

        # 퀴즈 생성
        self.quiz = GanaQuiz.objects.create(
            user=self.user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.GANA_TO_ROMAJI,
            question_count_setting=GanaQuizQuestionCount.TEN,
            total_questions=3
        )

        # 문제 생성
        for i, char in enumerate(self.hiragana_chars[:3], 1):
            GanaQuizQuestion.objects.create(
                quiz=self.quiz,
                word=char,
                question_number=i
            )

    def test_submit_correct_answer(self):
        """정답 제출"""
        question = self.quiz.questions.first()
        url = reverse('words:quiz_answer', kwargs={'quiz_id': self.quiz.id})
        data = {
            'question_id': question.id,
            'answer': 'a'  # あ의 발음
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['is_correct'])
        self.assertEqual(response.data['data']['current_score'], 1)

    def test_submit_wrong_answer(self):
        """오답 제출"""
        question = self.quiz.questions.first()
        url = reverse('words:quiz_answer', kwargs={'quiz_id': self.quiz.id})
        data = {
            'question_id': question.id,
            'answer': 'wrong'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['data']['is_correct'])
        self.assertEqual(response.data['data']['current_score'], 0)

    def test_submit_answer_case_insensitive(self):
        """대소문자 무시 정답 확인"""
        question = self.quiz.questions.first()
        url = reverse('words:quiz_answer', kwargs={'quiz_id': self.quiz.id})
        data = {
            'question_id': question.id,
            'answer': 'A'  # 대문자
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['is_correct'])

    def test_answer_updates_user_stats(self):
        """답변 시 사용자 통계 업데이트"""
        question = self.quiz.questions.first()
        url = reverse('words:quiz_answer', kwargs={'quiz_id': self.quiz.id})
        data = {
            'question_id': question.id,
            'answer': 'a'
        }
        self.client.post(url, data, format='json')

        # 통계 확인
        stats = UserGanaStats.objects.get(user=self.user, word=question.word)
        self.assertEqual(stats.total_attempts, 1)
        self.assertEqual(stats.correct_count, 1)

    def test_complete_quiz(self):
        """퀴즈 완료"""
        # 모든 문제 답변
        for question in self.quiz.questions.all():
            url = reverse('words:quiz_answer', kwargs={'quiz_id': self.quiz.id})
            data = {
                'question_id': question.id,
                'answer': question.word.pronunciation
            }
            response = self.client.post(url, data, format='json')

        # 마지막 응답에서 퀴즈 완료 확인
        self.assertTrue(response.data['data']['quiz_completed'])

        # 퀴즈 상태 확인
        self.quiz.refresh_from_db()
        self.assertTrue(self.quiz.is_completed)
        self.assertIsNotNone(self.quiz.completed_at)

    def test_cannot_answer_completed_quiz(self):
        """완료된 퀴즈에 답변 불가"""
        self.quiz.is_completed = True
        self.quiz.save()

        question = self.quiz.questions.first()
        url = reverse('words:quiz_answer', kwargs={'quiz_id': self.quiz.id})
        data = {
            'question_id': question.id,
            'answer': 'a'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_cannot_answer_same_question_twice(self):
        """같은 문제에 두 번 답변 불가"""
        question = self.quiz.questions.first()
        url = reverse('words:quiz_answer', kwargs={'quiz_id': self.quiz.id})
        data = {
            'question_id': question.id,
            'answer': 'a'
        }

        # 첫 번째 답변
        self.client.post(url, data, format='json')

        # 두 번째 답변 시도
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class GanaQuizDetailAPITest(GanaQuizAPITestBase):
    """퀴즈 상세 조회 API 테스트"""

    def setUp(self):
        super().setUp()
        self._authenticate_as(self.user)

        self.quiz = GanaQuiz.objects.create(
            user=self.user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.GANA_TO_ROMAJI,
            question_count_setting=GanaQuizQuestionCount.TEN,
            total_questions=3
        )

    def test_get_quiz_detail(self):
        """퀴즈 상세 조회"""
        url = reverse('words:quiz_detail', kwargs={'quiz_id': self.quiz.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['id'], self.quiz.id)

    def test_cannot_get_other_user_quiz(self):
        """다른 사용자 퀴즈 조회 불가"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        other_quiz = GanaQuiz.objects.create(
            user=other_user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.GANA_TO_ROMAJI,
            question_count_setting=GanaQuizQuestionCount.TEN,
            total_questions=3
        )

        url = reverse('words:quiz_detail', kwargs={'quiz_id': other_quiz.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GanaQuizHistoryAPITest(GanaQuizAPITestBase):
    """퀴즈 기록 조회 API 테스트"""

    def setUp(self):
        super().setUp()
        self._authenticate_as(self.user)

        # 여러 퀴즈 생성
        for i in range(5):
            GanaQuiz.objects.create(
                user=self.user,
                character_set=GanaCharacterSet.HIRAGANA if i % 2 == 0 else GanaCharacterSet.KATAKANA,
                quiz_type=GanaQuizType.GANA_TO_ROMAJI,
                question_count_setting=GanaQuizQuestionCount.TEN,
                total_questions=10,
                is_completed=i < 3
            )

    def test_get_quiz_history(self):
        """퀴즈 기록 조회"""
        url = reverse('words:quiz_history')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['quizzes']), 5)

    def test_filter_by_character_set(self):
        """문자 세트로 필터링"""
        url = reverse('words:quiz_history')
        response = self.client.get(url, {'character_set': 'hiragana'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['quizzes']), 3)

    def test_filter_by_completion(self):
        """완료 여부로 필터링"""
        url = reverse('words:quiz_history')
        response = self.client.get(url, {'is_completed': 'true'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['quizzes']), 3)

    def test_limit_results(self):
        """결과 수 제한"""
        url = reverse('words:quiz_history')
        response = self.client.get(url, {'limit': 2})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['quizzes']), 2)


class GanaQuizStatsAPITest(GanaQuizAPITestBase):
    """학습 통계 조회 API 테스트"""

    def setUp(self):
        super().setUp()
        self._authenticate_as(self.user)

        # 완료된 퀴즈 생성
        quiz = GanaQuiz.objects.create(
            user=self.user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.GANA_TO_ROMAJI,
            question_count_setting=GanaQuizQuestionCount.TEN,
            total_questions=10,
            correct_count=8,
            is_completed=True
        )

        # 사용자 통계 생성
        for i, char in enumerate(self.hiragana_chars[:5]):
            UserGanaStats.objects.create(
                user=self.user,
                word=char,
                total_attempts=10,
                correct_count=10 - i,  # 다양한 정답률
                incorrect_count=i
            )

    def test_get_stats(self):
        """통계 조회"""
        url = reverse('words:quiz_stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('total_quizzes', response.data['data'])
        self.assertIn('overall_accuracy', response.data['data'])
        self.assertIn('hiragana_stats', response.data['data'])
        self.assertIn('katakana_stats', response.data['data'])

    def test_stats_accuracy(self):
        """통계 정확도 확인"""
        url = reverse('words:quiz_stats')
        response = self.client.get(url)

        self.assertEqual(response.data['data']['total_quizzes'], 1)
        self.assertEqual(response.data['data']['total_correct'], 8)
        self.assertEqual(response.data['data']['overall_accuracy'], 80.0)

    def test_weakest_and_strongest_characters(self):
        """약점/강점 문자 조회"""
        url = reverse('words:quiz_stats')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('weakest_characters', response.data['data'])
        self.assertIn('strongest_characters', response.data['data'])


class GanaQuizCurrentQuestionAPITest(GanaQuizAPITestBase):
    """현재 문제 조회 API 테스트"""

    def setUp(self):
        super().setUp()
        self._authenticate_as(self.user)

        # 퀴즈 생성
        self.quiz = GanaQuiz.objects.create(
            user=self.user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.GANA_TO_ROMAJI,
            question_count_setting=GanaQuizQuestionCount.TEN,
            total_questions=3
        )

        # 문제 생성
        for i, char in enumerate(self.hiragana_chars[:3], 1):
            GanaQuizQuestion.objects.create(
                quiz=self.quiz,
                word=char,
                question_number=i
            )

    def test_get_current_question(self):
        """현재 문제 조회"""
        url = reverse('words:quiz_current_question', kwargs={'quiz_id': self.quiz.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('question', response.data['data'])
        self.assertIn('progress', response.data['data'])
        self.assertEqual(response.data['data']['question']['question_number'], 1)

    def test_get_current_question_progress(self):
        """현재 문제 조회 시 진행 상황 확인"""
        # 첫 번째 문제 답변
        first_question = self.quiz.questions.first()
        first_question.user_answer = 'a'
        first_question.is_correct = True
        first_question.answered_at = timezone.now()
        first_question.save()
        self.quiz.correct_count = 1
        self.quiz.save()

        url = reverse('words:quiz_current_question', kwargs={'quiz_id': self.quiz.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['progress']['current'], 2)
        self.assertEqual(response.data['data']['progress']['total'], 3)
        self.assertEqual(response.data['data']['progress']['correct_so_far'], 1)

    def test_get_current_question_completed_quiz(self):
        """완료된 퀴즈의 현재 문제 조회 시 에러"""
        self.quiz.is_completed = True
        self.quiz.save()

        url = reverse('words:quiz_current_question', kwargs={'quiz_id': self.quiz.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_get_current_question_no_more_questions(self):
        """모든 문제 답변 후 현재 문제 조회 시 에러"""
        # 모든 문제 답변 처리
        for question in self.quiz.questions.all():
            question.user_answer = question.word.pronunciation
            question.is_correct = True
            question.answered_at = timezone.now()
            question.save()

        url = reverse('words:quiz_current_question', kwargs={'quiz_id': self.quiz.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_cannot_get_other_user_current_question(self):
        """다른 사용자 퀴즈의 현재 문제 조회 불가"""
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        other_quiz = GanaQuiz.objects.create(
            user=other_user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.GANA_TO_ROMAJI,
            question_count_setting=GanaQuizQuestionCount.TEN,
            total_questions=3
        )

        url = reverse('words:quiz_current_question', kwargs={'quiz_id': other_quiz.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_nonexistent_quiz_current_question(self):
        """존재하지 않는 퀴즈의 현재 문제 조회 시 404"""
        url = reverse('words:quiz_current_question', kwargs={'quiz_id': 9999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class GanaQuizSelectTypeAPITest(GanaQuizAPITestBase):
    """선택형 퀴즈 API 테스트"""

    def setUp(self):
        super().setUp()
        self._authenticate_as(self.user)

    def test_select_quiz_has_choices(self):
        """선택형 퀴즈 문제에 선택지 포함"""
        url = reverse('words:quiz_start')
        data = {
            'character_set': 'hiragana',
            'quiz_type': 'romaji_to_gana_select',
            'question_count': 10
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        current_question = response.data['data']['current_question']
        self.assertIsNotNone(current_question['choices'])
        self.assertEqual(len(current_question['choices']), 3)

    def test_input_quiz_no_choices(self):
        """입력형 퀴즈 문제에 선택지 없음"""
        url = reverse('words:quiz_start')
        data = {
            'character_set': 'hiragana',
            'quiz_type': 'gana_to_romaji',
            'question_count': 10
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        current_question = response.data['data']['current_question']
        # 입력형은 choices가 null이거나 빈 리스트
        self.assertTrue(
            current_question['choices'] is None or
            len(current_question['choices']) == 0
        )

    def test_select_answer_from_choices(self):
        """선택형 퀴즈에서 선택지로 답변"""
        # 선택형 퀴즈 생성
        quiz = GanaQuiz.objects.create(
            user=self.user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.ROMAJI_TO_GANA_SELECT,
            question_count_setting=GanaQuizQuestionCount.TEN,
            total_questions=1
        )
        question = GanaQuizQuestion.objects.create(
            quiz=quiz,
            word=self.hiragana_chars[0],  # あ
            question_number=1,
            choices=['あ', 'い', 'う']
        )

        url = reverse('words:quiz_answer', kwargs={'quiz_id': quiz.id})
        data = {
            'question_id': question.id,
            'answer': 'あ'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['is_correct'])


class GanaQuizEdgeCaseAPITest(GanaQuizAPITestBase):
    """퀴즈 API 엣지 케이스 테스트"""

    def setUp(self):
        super().setUp()
        self._authenticate_as(self.user)

    def test_start_quiz_with_few_characters(self):
        """문자 수보다 많은 문제 수 요청 시"""
        # 가타카나는 5개만 있음
        url = reverse('words:quiz_start')
        data = {
            'character_set': 'katakana',
            'quiz_type': 'gana_to_romaji',
            'question_count': 10  # 5개밖에 없는데 10개 요청
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # 실제 문자 수만큼만 출제
        self.assertEqual(response.data['data']['quiz']['total_questions'], 5)

    def test_answer_with_whitespace(self):
        """공백이 포함된 답변 처리"""
        quiz = GanaQuiz.objects.create(
            user=self.user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.GANA_TO_ROMAJI,
            question_count_setting=GanaQuizQuestionCount.TEN,
            total_questions=1
        )
        question = GanaQuizQuestion.objects.create(
            quiz=quiz,
            word=self.hiragana_chars[0],  # あ (a)
            question_number=1
        )

        url = reverse('words:quiz_answer', kwargs={'quiz_id': quiz.id})
        data = {
            'question_id': question.id,
            'answer': '  a  '  # 앞뒤 공백
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['data']['is_correct'])

    def test_answer_nonexistent_quiz(self):
        """존재하지 않는 퀴즈에 답변 시도"""
        url = reverse('words:quiz_answer', kwargs={'quiz_id': 9999})
        data = {
            'question_id': 1,
            'answer': 'a'
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_answer_nonexistent_question(self):
        """존재하지 않는 문제에 답변 시도"""
        quiz = GanaQuiz.objects.create(
            user=self.user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.GANA_TO_ROMAJI,
            question_count_setting=GanaQuizQuestionCount.TEN,
            total_questions=1
        )

        url = reverse('words:quiz_answer', kwargs={'quiz_id': quiz.id})
        data = {
            'question_id': 9999,
            'answer': 'a'
        }
        response = self.client.post(url, data, format='json')

        # 존재하지 않는 문제는 404 반환
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_quiz_detail_includes_questions(self):
        """퀴즈 상세 조회 시 문제 목록 포함"""
        quiz = GanaQuiz.objects.create(
            user=self.user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.GANA_TO_ROMAJI,
            question_count_setting=GanaQuizQuestionCount.TEN,
            total_questions=3
        )
        for i, char in enumerate(self.hiragana_chars[:3], 1):
            GanaQuizQuestion.objects.create(
                quiz=quiz,
                word=char,
                question_number=i
            )

        url = reverse('words:quiz_detail', kwargs={'quiz_id': quiz.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('questions', response.data['data'])
        self.assertEqual(len(response.data['data']['questions']), 3)

    def test_completed_quiz_shows_answers(self):
        """완료된 퀴즈 조회 시 정답 표시"""
        quiz = GanaQuiz.objects.create(
            user=self.user,
            character_set=GanaCharacterSet.HIRAGANA,
            quiz_type=GanaQuizType.GANA_TO_ROMAJI,
            question_count_setting=GanaQuizQuestionCount.TEN,
            total_questions=1,
            is_completed=True,
            completed_at=timezone.now()
        )
        question = GanaQuizQuestion.objects.create(
            quiz=quiz,
            word=self.hiragana_chars[0],
            question_number=1,
            user_answer='a',
            is_correct=True,
            answered_at=timezone.now()
        )

        url = reverse('words:quiz_detail', kwargs={'quiz_id': quiz.id})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        questions = response.data['data']['questions']
        self.assertEqual(len(questions), 1)
        # 완료된 퀴즈는 correct_answer가 표시되어야 함
        self.assertIn('correct_answer', questions[0])
