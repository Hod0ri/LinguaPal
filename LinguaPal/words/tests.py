from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import User, Language
from .models import Word, WordTranslation, Example, ExampleTranslation, PartOfSpeech, WordCategory


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
