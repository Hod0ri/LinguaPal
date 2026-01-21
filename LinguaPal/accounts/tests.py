from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User, UserProfile, Language, Country
from .permissions import (
    IsAdminRole, IsStaffRole, IsUserRole,
    IsOwnerOrStaff, IsAdminOrReadOnly, IsStaffOrReadOnly
)


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
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['languages']), 3)


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
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['countries']), 3)


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
        self.assertFalse(response.data['success'])
        self.assertIn('error_code', response.data['data'])

    def test_create_profile_success(self):
        """프로필 생성 성공 테스트"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:create_profile')
        data = {
            'nickname': '테스터',
            'country': self.country_kr.id,
            'learning_language_ids': [self.language_en.id, self.language_ja.id]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['nickname'], '테스터')
        self.assertEqual(len(response.data['data']['learning_languages']), 2)

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
        url = reverse('accounts:create_profile')
        data = {
            'nickname': '테스터2',
            'country': self.country_kr.id,
            'learning_language_ids': [self.language_en.id]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('error_code', response.data['data'])

    def test_create_profile_invalid_nickname_too_short(self):
        """닉네임이 너무 짧을 때 테스트"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:create_profile')
        data = {
            'nickname': '테',
            'country': self.country_kr.id,
            'learning_language_ids': [self.language_en.id]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('nickname', response.data['data']['errors'])

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
        url = reverse('accounts:create_profile')
        data = {
            'nickname': '이미사용중',
            'country': self.country_kr.id,
            'learning_language_ids': [self.language_en.id]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('nickname', response.data['data']['errors'])

    def test_create_profile_no_learning_languages(self):
        """배우고자 하는 언어가 없을 때 테스트"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:create_profile')
        data = {
            'nickname': '테스터',
            'country': self.country_kr.id,
            'learning_language_ids': []
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('learning_language_ids', response.data['data']['errors'])

    def test_create_profile_invalid_language_id(self):
        """존재하지 않는 언어 ID로 프로필 생성 시도"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:create_profile')
        data = {
            'nickname': '테스터',
            'country': self.country_kr.id,
            'learning_language_ids': [9999]
        }
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('learning_language_ids', response.data['data']['errors'])

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
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['nickname'], '테스터')
        self.assertEqual(response.data['data']['country']['code'], 'KR')
        self.assertEqual(len(response.data['data']['learning_languages']), 2)

    def test_update_profile_nickname_success(self):
        """닉네임 수정 성공 테스트"""
        profile = UserProfile.objects.create(
            user=self.user,
            nickname='원래닉네임',
            country=self.country_kr
        )
        profile.learning_languages.add(self.language_en)

        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:update_profile')
        data = {
            'nickname': '새닉네임'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['nickname'], '새닉네임')

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
        url = reverse('accounts:update_profile')
        data = {
            'learning_language_ids': [self.language_ja.id, self.language_zh.id]
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['data']['learning_languages']), 2)

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
        url = reverse('accounts:update_profile')
        data = {
            'nickname': '새닉네임',
            'learning_language_ids': [self.language_ja.id]
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['nickname'], '새닉네임')
        self.assertEqual(len(response.data['data']['learning_languages']), 1)

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
        url = reverse('accounts:update_profile')
        data = {
            'nickname': '이미사용중'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('nickname', response.data['data']['errors'])

    def test_update_profile_not_found(self):
        """프로필이 없을 때 수정 테스트"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')
        url = reverse('accounts:update_profile')
        data = {
            'nickname': '새닉네임'
        }
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('error_code', response.data['data'])

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
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['email'], 'test@example.com')
        self.assertEqual(response.data['data']['has_profile'], False)
        self.assertIsNone(response.data['data']['profile'])

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
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['email'], 'test@example.com')
        self.assertEqual(response.data['data']['has_profile'], True)
        self.assertIsNotNone(response.data['data']['profile'])
        self.assertEqual(response.data['data']['profile']['nickname'], '테스터')


# =============================================================================
# RBAC (Role-Based Access Control) 테스트
# =============================================================================

class UserRoleModelTest(TestCase):
    """사용자 역할 모델 테스트"""

    def test_default_role_is_user(self):
        """기본 역할은 일반 사용자"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.assertEqual(user.role, User.Role.USER)
        self.assertTrue(user.is_user_role)
        self.assertFalse(user.is_staff_role)
        self.assertFalse(user.is_admin_role)

    def test_staff_role(self):
        """Staff 역할 테스트"""
        user = User.objects.create_user(
            username='staffuser',
            email='staff@example.com',
            password='testpass123',
            role=User.Role.STAFF
        )
        self.assertEqual(user.role, User.Role.STAFF)
        self.assertTrue(user.is_staff_role)
        self.assertFalse(user.is_user_role)
        self.assertFalse(user.is_admin_role)
        # Staff는 Django is_staff가 False
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_admin_role_sets_django_permissions(self):
        """Admin 역할은 Django is_staff, is_superuser 자동 설정"""
        user = User.objects.create_user(
            username='adminuser',
            email='admin@example.com',
            password='testpass123',
            role=User.Role.ADMIN
        )
        self.assertEqual(user.role, User.Role.ADMIN)
        self.assertTrue(user.is_admin_role)
        self.assertFalse(user.is_staff_role)
        self.assertFalse(user.is_user_role)
        # Admin은 Django is_staff, is_superuser가 True
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_role_change_updates_django_permissions(self):
        """역할 변경 시 Django 권한도 업데이트"""
        user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123',
            role=User.Role.USER
        )
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

        # Admin으로 변경
        user.role = User.Role.ADMIN
        user.save()
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

        # 다시 User로 변경
        user.role = User.Role.USER
        user.save()
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)


class IsAdminRolePermissionTest(APITestCase):
    """IsAdminRole 권한 테스트"""

    def setUp(self):
        self.client = APIClient()
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

    def _get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_admin_role_has_permission(self):
        """Admin 역할은 접근 가능"""
        permission = IsAdminRole()

        class MockRequest:
            user = self.admin_user

        self.assertTrue(permission.has_permission(MockRequest(), None))

    def test_staff_role_denied(self):
        """Staff 역할은 접근 불가"""
        permission = IsAdminRole()

        class MockRequest:
            user = self.staff_user

        self.assertFalse(permission.has_permission(MockRequest(), None))

    def test_user_role_denied(self):
        """일반 사용자 역할은 접근 불가"""
        permission = IsAdminRole()

        class MockRequest:
            user = self.normal_user

        self.assertFalse(permission.has_permission(MockRequest(), None))

    def test_unauthenticated_denied(self):
        """인증되지 않은 사용자는 접근 불가"""
        permission = IsAdminRole()

        class MockUser:
            is_authenticated = False

        class MockRequest:
            user = MockUser()

        self.assertFalse(permission.has_permission(MockRequest(), None))


class IsStaffRolePermissionTest(APITestCase):
    """IsStaffRole 권한 테스트"""

    def setUp(self):
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

    def test_admin_role_has_permission(self):
        """Admin 역할은 접근 가능"""
        permission = IsStaffRole()

        class MockRequest:
            user = self.admin_user

        self.assertTrue(permission.has_permission(MockRequest(), None))

    def test_staff_role_has_permission(self):
        """Staff 역할은 접근 가능"""
        permission = IsStaffRole()

        class MockRequest:
            user = self.staff_user

        self.assertTrue(permission.has_permission(MockRequest(), None))

    def test_user_role_denied(self):
        """일반 사용자 역할은 접근 불가"""
        permission = IsStaffRole()

        class MockRequest:
            user = self.normal_user

        self.assertFalse(permission.has_permission(MockRequest(), None))


class IsUserRolePermissionTest(APITestCase):
    """IsUserRole 권한 테스트"""

    def setUp(self):
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

    def test_all_authenticated_users_have_permission(self):
        """모든 인증된 사용자는 접근 가능"""
        permission = IsUserRole()

        for user in [self.admin_user, self.staff_user, self.normal_user]:
            class MockRequest:
                pass
            MockRequest.user = user
            self.assertTrue(permission.has_permission(MockRequest(), None))

    def test_unauthenticated_denied(self):
        """인증되지 않은 사용자는 접근 불가"""
        permission = IsUserRole()

        class MockUser:
            is_authenticated = False

        class MockRequest:
            user = MockUser()

        self.assertFalse(permission.has_permission(MockRequest(), None))


class IsOwnerOrStaffPermissionTest(APITestCase):
    """IsOwnerOrStaff 권한 테스트"""

    def setUp(self):
        self.staff_user = User.objects.create_user(
            username='staff',
            email='staff@example.com',
            password='testpass123',
            role=User.Role.STAFF
        )
        self.owner_user = User.objects.create_user(
            username='owner',
            email='owner@example.com',
            password='testpass123',
            role=User.Role.USER
        )
        self.other_user = User.objects.create_user(
            username='other',
            email='other@example.com',
            password='testpass123',
            role=User.Role.USER
        )
        self.country = Country.objects.create(
            code='KR',
            name_ko='대한민국',
            name_en='South Korea'
        )
        self.profile = UserProfile.objects.create(
            user=self.owner_user,
            nickname='오너',
            country=self.country
        )

    def test_owner_can_access_own_object(self):
        """소유자는 자신의 객체에 접근 가능"""
        permission = IsOwnerOrStaff()

        class MockRequest:
            user = self.owner_user

        self.assertTrue(permission.has_object_permission(MockRequest(), None, self.profile))

    def test_staff_can_access_any_object(self):
        """Staff는 모든 객체에 접근 가능"""
        permission = IsOwnerOrStaff()

        class MockRequest:
            user = self.staff_user

        self.assertTrue(permission.has_object_permission(MockRequest(), None, self.profile))

    def test_other_user_cannot_access(self):
        """다른 사용자는 접근 불가"""
        permission = IsOwnerOrStaff()

        class MockRequest:
            user = self.other_user

        self.assertFalse(permission.has_object_permission(MockRequest(), None, self.profile))

    def test_owner_can_access_user_object(self):
        """소유자는 자신의 User 객체에 접근 가능"""
        permission = IsOwnerOrStaff()

        class MockRequest:
            user = self.owner_user

        self.assertTrue(permission.has_object_permission(MockRequest(), None, self.owner_user))


class IsStaffOrReadOnlyPermissionTest(APITestCase):
    """IsStaffOrReadOnly 권한 테스트"""

    def setUp(self):
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

    def test_staff_can_write(self):
        """Staff는 쓰기 가능"""
        permission = IsStaffOrReadOnly()

        class MockRequest:
            user = self.staff_user
            method = 'POST'

        self.assertTrue(permission.has_permission(MockRequest(), None))

    def test_user_can_read(self):
        """일반 사용자는 읽기만 가능"""
        permission = IsStaffOrReadOnly()

        class MockRequest:
            user = self.normal_user
            method = 'GET'

        self.assertTrue(permission.has_permission(MockRequest(), None))

    def test_user_cannot_write(self):
        """일반 사용자는 쓰기 불가"""
        permission = IsStaffOrReadOnly()

        class MockRequest:
            user = self.normal_user
            method = 'POST'

        self.assertFalse(permission.has_permission(MockRequest(), None))


class UserSerializerRoleTest(APITestCase):
    """사용자 Serializer 역할 필드 테스트"""

    def setUp(self):
        self.client = APIClient()
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

    def _get_token(self, user):
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)

    def test_admin_user_response_includes_role(self):
        """Admin 사용자 응답에 역할 정보 포함"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._get_token(self.admin_user)}')
        url = reverse('accounts:current_user')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['role'], 'admin')
        self.assertEqual(response.data['data']['role_display'], '관리자')

    def test_staff_user_response_includes_role(self):
        """Staff 사용자 응답에 역할 정보 포함"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._get_token(self.staff_user)}')
        url = reverse('accounts:current_user')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['role'], 'staff')
        self.assertEqual(response.data['data']['role_display'], '스태프')

    def test_normal_user_response_includes_role(self):
        """일반 사용자 응답에 역할 정보 포함"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self._get_token(self.normal_user)}')
        url = reverse('accounts:current_user')
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['data']['role'], 'user')
        self.assertEqual(response.data['data']['role_display'], '일반 사용자')
