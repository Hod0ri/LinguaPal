from rest_framework import generics, permissions, status, serializers
from rest_framework.views import APIView
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


# API 문서용 Serializer
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


@extend_schema(tags=['인증'])
class GoogleLoginView(APIView):
    """Google OAuth2 로그인"""
    permission_classes = [permissions.AllowAny]

    @extend_schema(
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
    def post(self, request):
        """Verify Google ID token and create/login user"""
        token = request.data.get('access_token')

        if not token:
            return APIResponse.error(
                message='Access token is required',
                error_code=ErrorCode.INVALID_INPUT,
                status_code=status.HTTP_400_BAD_REQUEST
            )

        # Rate Limiting
        client_ip = self.get_client_ip(request)
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

            # Update existing user's profile image if not set
            if not created:
                if picture and not user.profile_image:
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

    def get_client_ip(self, request):
        """Extract client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@extend_schema(tags=['인증'])
class GoogleConfigView(APIView):
    """Google OAuth 설정 조회"""
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="Google OAuth 설정 조회",
        description="Google OAuth Client ID를 반환합니다.",
        responses={200: GoogleConfigResponseSerializer},
    )
    def get(self, request):
        return APIResponse.success(
            message='Google OAuth configuration retrieved',
            data={
                'client_id': settings.GOOGLE_OAUTH_CLIENT_ID
            }
        )


@extend_schema(tags=['사용자'])
class CurrentUserView(generics.RetrieveAPIView):
    """현재 로그인한 사용자 정보 조회"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    @extend_schema(
        summary="현재 사용자 정보 조회",
        description="JWT 토큰으로 인증된 현재 사용자의 정보를 반환합니다.",
        responses={200: UserSerializer},
    )
    def get(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return APIResponse.success(
            message='User information retrieved',
            data=serializer.data
        )


@extend_schema(tags=['기본 데이터'])
class LanguageListView(generics.ListAPIView):
    """언어 목록 조회"""
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="언어 목록 조회",
        description="시스템에서 지원하는 언어 목록을 반환합니다. 인증이 필요하지 않습니다.",
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(
            message='Languages retrieved',
            data={
                'languages': serializer.data,
                'total_count': queryset.count()
            }
        )


@extend_schema(tags=['기본 데이터'])
class CountryListView(generics.ListAPIView):
    """국가 목록 조회"""
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [permissions.AllowAny]

    @extend_schema(
        summary="국가 목록 조회",
        description="시스템에서 지원하는 국가 목록을 반환합니다. 인증이 필요하지 않습니다.",
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        return APIResponse.success(
            message='Countries retrieved',
            data={
                'countries': serializer.data,
                'total_count': queryset.count()
            }
        )


@extend_schema(tags=['프로필'])
class UserProfileView(APIView):
    """사용자 프로필 관리"""
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="프로필 조회",
        description="현재 로그인한 사용자의 프로필을 조회합니다.",
        responses={
            200: UserProfileSerializer,
            404: ErrorResponseSerializer,
        },
    )
    def get(self, request):
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
        summary="프로필 생성",
        description="현재 로그인한 사용자의 프로필을 생성합니다. 닉네임, 국가, 학습 언어를 설정합니다.",
        request=UserProfileCreateSerializer,
        responses={
            201: UserProfileSerializer,
            400: ErrorResponseSerializer,
        },
    )
    def post(self, request):
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
        summary="프로필 수정",
        description="현재 로그인한 사용자의 프로필을 수정합니다. 닉네임과 학습 언어만 수정 가능합니다.",
        request=UserProfileUpdateSerializer,
        responses={
            200: UserProfileSerializer,
            400: ErrorResponseSerializer,
            404: ErrorResponseSerializer,
        },
    )
    def patch(self, request):
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
