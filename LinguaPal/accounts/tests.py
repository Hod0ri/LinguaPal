from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, UserProfile, Language, Country


class LanguageModelTest(TestCase):
    """언어 모델 테스트"""

    def setUp(self):
        self.language = Language.objects.create(
            code='en',
            name_ko='영어',
            name_en='English'
        )

    def test_language_creation(self):
        """언어 생성 테스트"""
        self.assertEqual(self.language.code, 'en')
        self.assertEqual(self.language.name_ko, '영어')
        self.assertEqual(self.language.name_en, 'English')

    def test_language_str(self):
        """언어 문자열 표현 테스트"""
        self.assertEqual(str(self.language), '영어 (en)')


class CountryModelTest(TestCase):
    """국가 모델 테스트"""

    def setUp(self):
        self.country = Country.objects.create(
            code='KR',
            name_ko='대한민국',
            name_en='South Korea'
        )

    def test_country_creation(self):
        """국가 생성 테스트"""
        self.assertEqual(self.country.code, 'KR')
        self.assertEqual(self.country.name_ko, '대한민국')
        self.assertEqual(self.country.name_en, 'South Korea')

    def test_country_str(self):
        """국가 문자열 표현 테스트"""
        self.assertEqual(str(self.country), '대한민국 (KR)')


class UserProfileModelTest(TestCase):
    """사용자 프로필 모델 테스트"""

    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.country = Country.objects.create(
            code='KR',
            name_ko='대한민국',
            name_en='South Korea'
        )
        self.language_en = Language.objects.create(
            code='en',
            name_ko='영어',
            name_en='English'
        )
        self.language_ja = Language.objects.create(
            code='ja',
            name_ko='일본어',
            name_en='Japanese'
        )

    def test_userprofile_creation(self):
        """사용자 프로필 생성 테스트"""
        profile = UserProfile.objects.create(
            user=self.user,
            nickname='테스터',
            country=self.country
        )
        profile.learning_languages.add(self.language_en, self.language_ja)

        self.assertEqual(profile.nickname, '테스터')
        self.assertEqual(profile.country, self.country)
        self.assertEqual(profile.learning_languages.count(), 2)

    def test_userprofile_str(self):
        """사용자 프로필 문자열 표현 테스트"""
        profile = UserProfile.objects.create(
            user=self.user,
            nickname='테스터',
            country=self.country
        )
        self.assertEqual(str(profile), '테스터 (test@example.com)')

    def test_userprofile_unique_nickname(self):
        """닉네임 중복 방지 테스트"""
        UserProfile.objects.create(
            user=self.user,
            nickname='테스터',
            country=self.country
        )

        user2 = User.objects.create_user(
            username='testuser2',
            email='test2@example.com',
            password='testpass123'
        )

        with self.assertRaises(Exception):
            UserProfile.objects.create(
                user=user2,
                nickname='테스터',
                country=self.country
            )


class LanguageListAPITest(APITestCase):
    """언어 목록 API 테스트"""

    def setUp(self):
        Language.objects.create(code='en', name_ko='영어', name_en='English')
        Language.objects.create(code='ja', name_ko='일본어', name_en='Japanese')
        Language.objects.create(code='zh', name_ko='중국어', name_en='Chinese')

    def test_get_language_list(self):
        """언어 목록 조회 테스트 (인증 불필요)"""
        url = reverse('accounts:language_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)


class CountryListAPITest(APITestCase):
    """국가 목록 API 테스트"""

    def setUp(self):
        Country.objects.create(code='KR', name_ko='대한민국', name_en='South Korea')
        Country.objects.create(code='US', name_ko='미국', name_en='United States')
        Country.objects.create(code='JP', name_ko='일본', name_en='Japan')

    def test_get_country_list(self):
        """국가 목록 조회 테스트 (인증 불필요)"""
        url = reverse('accounts:country_list')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 3)


class UserProfileAPITest(APITestCase):
    """사용자 프로필 API 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # JWT 토큰 생성
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # 테스트 데이터 생성
        self.country_kr = Country.objects.create(
            code='KR',
            name_ko='대한민국',
            name_en='South Korea'
        )
        self.country_us = Country.objects.create(
            code='US',
            name_ko='미국',
            name_en='United States'
        )

        self.language_en = Language.objects.create(
            code='en',
            name_ko='영어',
            name_en='English'
        )
        self.language_ja = Language.objects.create(
            code='ja',
            name_ko='일본어',
            name_en='Japanese'
        )
        self.language_zh = Language.objects.create(
            code='zh',
            name_ko='중국어',
            name_en='Chinese'
        )

    def test_get_profile_not_found(self):
        """프로필이 없을 때 조회 테스트"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:user_profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_create_profile_success(self):
        """프로필 생성 성공 테스트"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:user_profile')
        data = {
            'nickname': '테스터',
            'country': self.country_kr.id,
            'learning_language_ids': [self.language_en.id, self.language_ja.id]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['nickname'], '테스터')
        self.assertEqual(len(response.data['learning_languages']), 2)

        # DB에 실제로 생성되었는지 확인
        profile = UserProfile.objects.get(user=self.user)
        self.assertEqual(profile.nickname, '테스터')
        self.assertEqual(profile.country, self.country_kr)
        self.assertEqual(profile.learning_languages.count(), 2)

    def test_create_profile_duplicate(self):
        """프로필 중복 생성 방지 테스트"""
        # 첫 번째 프로필 생성
        UserProfile.objects.create(
            user=self.user,
            nickname='테스터',
            country=self.country_kr
        )

        # 두 번째 프로필 생성 시도
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:user_profile')
        data = {
            'nickname': '테스터2',
            'country': self.country_kr.id,
            'learning_language_ids': [self.language_en.id]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_create_profile_invalid_nickname_too_short(self):
        """닉네임이 너무 짧을 때 테스트"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:user_profile')
        data = {
            'nickname': '테',
            'country': self.country_kr.id,
            'learning_language_ids': [self.language_en.id]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nickname', response.data)

    def test_create_profile_duplicate_nickname(self):
        """닉네임 중복 방지 테스트"""
        # 다른 사용자가 이미 사용 중인 닉네임
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=other_user,
            nickname='이미사용중',
            country=self.country_kr
        )

        # 같은 닉네임으로 프로필 생성 시도
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:user_profile')
        data = {
            'nickname': '이미사용중',
            'country': self.country_kr.id,
            'learning_language_ids': [self.language_en.id]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nickname', response.data)

    def test_create_profile_no_learning_languages(self):
        """배우고자 하는 언어가 없을 때 테스트"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:user_profile')
        data = {
            'nickname': '테스터',
            'country': self.country_kr.id,
            'learning_language_ids': []
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('learning_language_ids', response.data)

    def test_create_profile_invalid_language_id(self):
        """존재하지 않는 언어 ID로 프로필 생성 시도"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:user_profile')
        data = {
            'nickname': '테스터',
            'country': self.country_kr.id,
            'learning_language_ids': [9999]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('learning_language_ids', response.data)

    def test_get_profile_success(self):
        """프로필 조회 성공 테스트"""
        profile = UserProfile.objects.create(
            user=self.user,
            nickname='테스터',
            country=self.country_kr
        )
        profile.learning_languages.add(self.language_en, self.language_ja)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:user_profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nickname'], '테스터')
        self.assertEqual(response.data['country']['code'], 'KR')
        self.assertEqual(len(response.data['learning_languages']), 2)

    def test_update_profile_nickname_success(self):
        """닉네임 수정 성공 테스트"""
        profile = UserProfile.objects.create(
            user=self.user,
            nickname='원래닉네임',
            country=self.country_kr
        )
        profile.learning_languages.add(self.language_en)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:user_profile')
        data = {
            'nickname': '새닉네임'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nickname'], '새닉네임')

        # DB에 실제로 업데이트되었는지 확인
        profile.refresh_from_db()
        self.assertEqual(profile.nickname, '새닉네임')

    def test_update_profile_learning_languages_success(self):
        """배우고자 하는 언어 수정 성공 테스트"""
        profile = UserProfile.objects.create(
            user=self.user,
            nickname='테스터',
            country=self.country_kr
        )
        profile.learning_languages.add(self.language_en)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:user_profile')
        data = {
            'learning_language_ids': [self.language_ja.id, self.language_zh.id]
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['learning_languages']), 2)

        # DB에 실제로 업데이트되었는지 확인
        profile.refresh_from_db()
        self.assertEqual(profile.learning_languages.count(), 2)
        self.assertIn(self.language_ja, profile.learning_languages.all())
        self.assertIn(self.language_zh, profile.learning_languages.all())

    def test_update_profile_nickname_and_languages_success(self):
        """닉네임과 언어 동시 수정 성공 테스트"""
        profile = UserProfile.objects.create(
            user=self.user,
            nickname='원래닉네임',
            country=self.country_kr
        )
        profile.learning_languages.add(self.language_en)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:user_profile')
        data = {
            'nickname': '새닉네임',
            'learning_language_ids': [self.language_ja.id]
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['nickname'], '새닉네임')
        self.assertEqual(len(response.data['learning_languages']), 1)

        # DB에 실제로 업데이트되었는지 확인
        profile.refresh_from_db()
        self.assertEqual(profile.nickname, '새닉네임')
        self.assertEqual(profile.learning_languages.count(), 1)

    def test_update_profile_duplicate_nickname(self):
        """닉네임 수정 시 중복 방지 테스트"""
        # 다른 사용자가 이미 사용 중인 닉네임
        other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123'
        )
        UserProfile.objects.create(
            user=other_user,
            nickname='이미사용중',
            country=self.country_kr
        )

        # 본인 프로필 생성
        profile = UserProfile.objects.create(
            user=self.user,
            nickname='테스터',
            country=self.country_kr
        )

        # 다른 사용자의 닉네임으로 변경 시도
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:user_profile')
        data = {
            'nickname': '이미사용중'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('nickname', response.data)

    def test_update_profile_not_found(self):
        """프로필이 없을 때 수정 테스트"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:user_profile')
        data = {
            'nickname': '새닉네임'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertIn('error', response.data)

    def test_unauthenticated_access(self):
        """인증되지 않은 사용자의 프로필 접근 테스트"""
        url = reverse('accounts:user_profile')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class CurrentUserViewTest(APITestCase):
    """현재 사용자 정보 조회 API 테스트"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )

        # JWT 토큰 생성
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

        # 테스트 데이터 생성
        self.country = Country.objects.create(
            code='KR',
            name_ko='대한민국',
            name_en='South Korea'
        )
        self.language_en = Language.objects.create(
            code='en',
            name_ko='영어',
            name_en='English'
        )

    def test_get_current_user_without_profile(self):
        """프로필이 없는 사용자 정보 조회"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:current_user')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['has_profile'], False)
        self.assertIsNone(response.data['profile'])

    def test_get_current_user_with_profile(self):
        """프로필이 있는 사용자 정보 조회"""
        profile = UserProfile.objects.create(
            user=self.user,
            nickname='테스터',
            country=self.country
        )
        profile.learning_languages.add(self.language_en)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:current_user')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'test@example.com')
        self.assertEqual(response.data['has_profile'], True)
        self.assertIsNotNone(response.data['profile'])
        self.assertEqual(response.data['profile']['nickname'], '테스터')
