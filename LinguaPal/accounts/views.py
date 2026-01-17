from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from django.core.cache import cache
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


class GoogleLoginView(APIView):
    """Google OAuth2 login with ID token verification"""
    permission_classes = [permissions.AllowAny]

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


class GoogleConfigView(APIView):
    """Return Google OAuth configuration"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Return Google OAuth Client ID"""
        return APIResponse.success(
            message='Google OAuth configuration retrieved',
            data={
                'client_id': settings.GOOGLE_OAUTH_CLIENT_ID
            }
        )


class CurrentUserView(generics.RetrieveAPIView):
    """Get current logged-in user information"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return APIResponse.success(
            message='User information retrieved',
            data=serializer.data
        )


class LanguageListView(generics.ListAPIView):
    """Get language list (no authentication required)"""
    queryset = Language.objects.all()
    serializer_class = LanguageSerializer
    permission_classes = [permissions.AllowAny]

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


class CountryListView(generics.ListAPIView):
    """Get country list (no authentication required)"""
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = [permissions.AllowAny]

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


class UserProfileView(APIView):
    """User profile view/create/update"""
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        """Get profile"""
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

    def post(self, request):
        """Create profile"""
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

    def patch(self, request):
        """Update profile (nickname and languages only)"""
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
