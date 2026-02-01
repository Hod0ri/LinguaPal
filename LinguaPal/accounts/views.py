from rest_framework import status, serializers
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from django.core.cache import cache
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiResponse
from .models import User, UserProfile, Language, Country
from .serializers import (
    UserSerializer,
    UserProfileSerializer,
    UserProfileCreateSerializer,
    UserProfileUpdateSerializer,
    LanguageSerializer,
    CountrySerializer
)
from .utils import APIResponse, ErrorCode
import time


# =============================================================================
# API 문서용 Serializer
# =============================================================================

class GoogleLoginRequestSerializer(serializers.Serializer):
    access_token = serializers.CharField(help_text="Google OAuth2 ID 토큰")


class TokenResponseSerializer(serializers.Serializer):
    access_token = serializers.CharField()
    refresh_token = serializers.CharField()
    user = UserSerializer()


class GoogleConfigResponseSerializer(serializers.Serializer):
    client_id = serializers.CharField()


class ErrorResponseSerializer(serializers.Serializer):
    success = serializers.BooleanField(default=False)
    message = serializers.CharField()
    data = serializers.DictField()


# =============================================================================
# Helper Functions
# =============================================================================

def get_client_ip(request):
    """Extract client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


# =============================================================================
# 인증 API
# =============================================================================

@extend_schema(
    tags=['인증'],
    summary="Google 로그인",
    description="Google OAuth2 ID 토큰을 검증하고 JWT 토큰을 발급합니다.",
    request=GoogleLoginRequestSerializer,
    responses={
        200: OpenApiResponse(
            response=TokenResponseSerializer,
            description="로그인 성공"
        ),
        400: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="잘못된 토큰"
        ),
        429: OpenApiResponse(
            response=ErrorResponseSerializer,
            description="요청 횟수 초과"
        ),
    },
    examples=[
        OpenApiExample(
            'Request Example',
            value={'access_token': 'eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...'},
            request_only=True,
        ),
    ]
)
@api_view(['POST'])
@permission_classes([AllowAny])
def google_login(request):
    """Google OAuth2 로그인"""
    token = request.data.get('access_token')

    if not token:
        return APIResponse.error(
            message='Access token is required',
            error_code=ErrorCode.INVALID_INPUT,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    # Rate Limiting
    client_ip = get_client_ip(request)
    rate_key = f'google_login_rate:{client_ip}'
    request_count = cache.get(rate_key, 0)

    if request_count > 10:
        return APIResponse.error(
            message='Too many requests. Please try again later.',
            error_code=ErrorCode.TOO_MANY_REQUESTS,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS
        )

    try:
        # Google ID Token verification
        idinfo = id_token.verify_oauth2_token(
            token,
            requests.Request(),
            settings.GOOGLE_OAUTH_CLIENT_ID,
            clock_skew_in_seconds=10
        )

        # 1. Audience validation
        if idinfo.get('aud') != settings.GOOGLE_OAUTH_CLIENT_ID:
            return APIResponse.error(
                message='Invalid audience',
                error_code=ErrorCode.INVALID_AUDIENCE,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # 2. Token issuer validation
        if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
            return APIResponse.error(
                message='Invalid token issuer',
                error_code=ErrorCode.INVALID_ISSUER,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # 3. Token expiration check
        current_time = int(time.time())
        if idinfo.get('exp', 0) < current_time:
            return APIResponse.error(
                message='Token has expired',
                error_code=ErrorCode.TOKEN_EXPIRED,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # 4. Email verification check
        if not idinfo.get('email_verified', False):
            return APIResponse.error(
                message='Email not verified by Google',
                error_code=ErrorCode.EMAIL_NOT_VERIFIED,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # 5. Token reuse prevention (Nonce check)
        jti = idinfo.get('jti') or f"{idinfo['sub']}:{idinfo['iat']}"
        nonce_key = f'google_token_nonce:{jti}'

        if cache.get(nonce_key):
            return APIResponse.error(
                message='Token has already been used',
                error_code=ErrorCode.TOKEN_ALREADY_USED,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Mark token as used
        ttl = idinfo.get('exp', current_time + 3600) - current_time
        cache.set(nonce_key, True, ttl)

        # Extract user information
        google_id = idinfo['sub']
        email = idinfo.get('email')
        name = idinfo.get('name', '')
        picture = idinfo.get('picture', '')

        # Create or get user
        user, created = User.objects.get_or_create(
            google_id=google_id,
            defaults={
                'email': email,
                'username': email.split('@')[0] if email else f'user_{google_id}',
                'profile_image': picture,
            }
        )

        # Auto-assign admin role for specific email
        ADMIN_EMAILS = ['mintwlsehtro@gmail.com']
        if email in ADMIN_EMAILS and user.role != User.Role.ADMIN:
            user.role = User.Role.ADMIN
            user.save()

        # Update existing user's profile image if not set
        elif not created and picture and not user.profile_image:
            user.profile_image = picture
            user.save()

        # Generate JWT tokens
        from rest_framework_simplejwt.tokens import RefreshToken
        refresh = RefreshToken.for_user(user)

        # Increment rate limit counter
        cache.set(rate_key, request_count + 1, 60)

        return APIResponse.success(
            message='Login successful',
            data={
                'access_token': str(refresh.access_token),
                'refresh_token': str(refresh),
                'user': UserSerializer(user).data
            },
            status_code=status.HTTP_200_OK
        )

    except ValueError as e:
        cache.set(rate_key, request_count + 1, 60)
        return APIResponse.error(
            message=f'Invalid token: {str(e)}',
            error_code=ErrorCode.INVALID_TOKEN,
            status_code=status.HTTP_400_BAD_REQUEST
        )
    except Exception as e:
        cache.set(rate_key, request_count + 1, 60)
        return APIResponse.error(
            message=f'Authentication failed: {str(e)}',
            error_code=ErrorCode.AUTHENTICATION_FAILED,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@extend_schema(
    tags=['인증'],
    summary="Google OAuth 설정 조회",
    description="Google OAuth Client ID를 반환합니다.",
    responses={200: GoogleConfigResponseSerializer},
)
@api_view(['GET'])
@permission_classes([AllowAny])
def google_config(request):
    """Google OAuth 설정 조회"""
    return APIResponse.success(
        message='Google OAuth configuration retrieved',
        data={
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID
        }
    )


# =============================================================================
# 사용자 API
# =============================================================================

@extend_schema(
    tags=['사용자'],
    summary="현재 사용자 정보 조회",
    description="JWT 토큰으로 인증된 현재 사용자의 정보를 반환합니다.",
    responses={200: UserSerializer},
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def current_user(request):
    """현재 로그인한 사용자 정보 조회"""
    serializer = UserSerializer(request.user)
    return APIResponse.success(
        message='User information retrieved',
        data=serializer.data
    )


# =============================================================================
# 기본 데이터 API
# =============================================================================

@extend_schema(
    tags=['기본 데이터'],
    summary="언어 목록 조회",
    description="시스템에서 지원하는 언어 목록을 반환합니다. 인증이 필요하지 않습니다.",
    responses={200: LanguageSerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([AllowAny])
def language_list(request):
    """언어 목록 조회"""
    queryset = Language.objects.all()
    serializer = LanguageSerializer(queryset, many=True)
    return APIResponse.success(
        message='Languages retrieved',
        data={
            'languages': serializer.data,
            'total_count': queryset.count()
        }
    )


@extend_schema(
    tags=['기본 데이터'],
    summary="국가 목록 조회",
    description="시스템에서 지원하는 국가 목록을 반환합니다. 인증이 필요하지 않습니다.",
    responses={200: CountrySerializer(many=True)},
)
@api_view(['GET'])
@permission_classes([AllowAny])
def country_list(request):
    """국가 목록 조회"""
    queryset = Country.objects.all().order_by('name_ko')
    serializer = CountrySerializer(queryset, many=True)
    return APIResponse.success(
        message='Countries retrieved',
        data={
            'countries': serializer.data,
            'total_count': queryset.count()
        }
    )


# =============================================================================
# 프로필 API
# =============================================================================

@extend_schema(
    tags=['프로필'],
    summary="프로필 조회",
    description="현재 로그인한 사용자의 프로필을 조회합니다.",
    responses={
        200: UserProfileSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """프로필 조회"""
    try:
        profile = request.user.profile
        serializer = UserProfileSerializer(profile)
        return APIResponse.success(
            message='Profile retrieved',
            data=serializer.data
        )
    except UserProfile.DoesNotExist:
        return APIResponse.error(
            message='Profile not found',
            error_code=ErrorCode.PROFILE_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND
        )


@extend_schema(
    tags=['프로필'],
    summary="프로필 생성",
    description="현재 로그인한 사용자의 프로필을 생성합니다. 닉네임, 국가, 학습 언어를 설정합니다.",
    request=UserProfileCreateSerializer,
    responses={
        201: UserProfileSerializer,
        400: ErrorResponseSerializer,
    },
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_profile(request):
    """프로필 생성"""
    # Check if profile already exists
    if hasattr(request.user, 'profile'):
        return APIResponse.error(
            message='Profile already exists',
            error_code=ErrorCode.PROFILE_ALREADY_EXISTS,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    serializer = UserProfileCreateSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(user=request.user)
        # Retrieve created profile with full details
        profile = request.user.profile
        response_serializer = UserProfileSerializer(profile)
        return APIResponse.success(
            message='Profile created successfully',
            data=response_serializer.data,
            status_code=status.HTTP_201_CREATED
        )

    return APIResponse.validation_error(
        errors=serializer.errors,
        message='Validation failed'
    )


@extend_schema(
    tags=['프로필'],
    summary="프로필 수정",
    description="현재 로그인한 사용자의 프로필을 수정합니다. 닉네임과 학습 언어만 수정 가능합니다.",
    request=UserProfileUpdateSerializer,
    responses={
        200: UserProfileSerializer,
        400: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """프로필 수정"""
    try:
        profile = request.user.profile
    except UserProfile.DoesNotExist:
        return APIResponse.error(
            message='Profile not found',
            error_code=ErrorCode.PROFILE_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND
        )

    serializer = UserProfileUpdateSerializer(profile, data=request.data, partial=True)
    if serializer.is_valid():
        serializer.save()
        # Return updated profile with full details
        response_serializer = UserProfileSerializer(profile)
        return APIResponse.success(
            message='Profile updated successfully',
            data=response_serializer.data
        )

    return APIResponse.validation_error(
        errors=serializer.errors,
        message='Validation failed'
    )


# =============================================================================
# 정책 문서 API
# =============================================================================

import os
import markdown


class PolicyDocumentSerializer(serializers.Serializer):
    type = serializers.ChoiceField(choices=['terms', 'privacy'])
    content = serializers.CharField()
    content_html = serializers.CharField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)


def _get_policy_path(policy_type: str) -> str:
    """Get file path for policy document."""
    policy_files = {
        'terms': 'terms_of_service.md',
        'privacy': 'privacy_policy.md',
    }
    filename = policy_files.get(policy_type)
    if not filename:
        return None
    return os.path.join(settings.BASE_DIR, 'policies', filename)


def _read_policy(policy_type: str) -> dict:
    """Read policy document from file."""
    filepath = _get_policy_path(policy_type)
    if not filepath or not os.path.exists(filepath):
        return None

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Convert to HTML
    md = markdown.Markdown(extensions=['tables', 'fenced_code'])
    content_html = md.convert(content)

    # Get file modification time
    mtime = os.path.getmtime(filepath)
    from datetime import datetime
    updated_at = datetime.fromtimestamp(mtime)

    return {
        'type': policy_type,
        'content': content,
        'content_html': content_html,
        'updated_at': updated_at,
    }


@extend_schema(
    tags=['정책'],
    summary="이용약관 조회",
    description="서비스 이용약관을 조회합니다. 인증이 필요하지 않습니다.",
    responses={200: PolicyDocumentSerializer},
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_terms_of_service(request):
    """이용약관 조회"""
    policy = _read_policy('terms')
    if not policy:
        return APIResponse.error(
            message='Terms of service not found',
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND
        )
    return APIResponse.success(
        message='Terms of service retrieved',
        data=policy
    )


@extend_schema(
    tags=['정책'],
    summary="개인정보처리방침 조회",
    description="개인정보처리방침을 조회합니다. 인증이 필요하지 않습니다.",
    responses={200: PolicyDocumentSerializer},
)
@api_view(['GET'])
@permission_classes([AllowAny])
def get_privacy_policy(request):
    """개인정보처리방침 조회"""
    policy = _read_policy('privacy')
    if not policy:
        return APIResponse.error(
            message='Privacy policy not found',
            error_code=ErrorCode.RESOURCE_NOT_FOUND,
            status_code=status.HTTP_404_NOT_FOUND
        )
    return APIResponse.success(
        message='Privacy policy retrieved',
        data=policy
    )


class PolicyUpdateSerializer(serializers.Serializer):
    content = serializers.CharField()


@extend_schema(
    tags=['정책'],
    summary="정책 문서 수정 (관리자)",
    description="이용약관 또는 개인정보처리방침을 수정합니다. 관리자 권한이 필요합니다.",
    request=PolicyUpdateSerializer,
    responses={
        200: PolicyDocumentSerializer,
        403: ErrorResponseSerializer,
        404: ErrorResponseSerializer,
    },
)
@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_policy(request, policy_type):
    """정책 문서 수정 (관리자 전용)"""
    # Check admin permission
    if not request.user.is_staff and not request.user.is_superuser:
        return APIResponse.error(
            message='Admin permission required',
            error_code=ErrorCode.PERMISSION_DENIED,
            status_code=status.HTTP_403_FORBIDDEN
        )

    if policy_type not in ['terms', 'privacy']:
        return APIResponse.error(
            message='Invalid policy type. Use "terms" or "privacy".',
            error_code=ErrorCode.INVALID_INPUT,
            status_code=status.HTTP_400_BAD_REQUEST
        )

    serializer = PolicyUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return APIResponse.validation_error(
            errors=serializer.errors,
            message='Validation failed'
        )

    content = serializer.validated_data['content']
    filepath = _get_policy_path(policy_type)

    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)

    # Write content to file
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)

    # Return updated policy
    policy = _read_policy(policy_type)
    return APIResponse.success(
        message=f'Policy document updated successfully',
        data=policy
    )
