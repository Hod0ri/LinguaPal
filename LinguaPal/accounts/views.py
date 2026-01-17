from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from django.core.cache import cache
from .models import User
from .serializers import UserSerializer
import time


class GoogleLoginView(APIView):
    """Google OAuth2 로그인 뷰 - ID Token 검증 (보안 강화)"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Google ID Token을 검증하고 사용자 생성/로그인"""
        token = request.data.get('access_token')

        if not token:
            return Response(
                {'error': 'access_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Rate Limiting: 동일 IP에서 너무 많은 요청 방지
        client_ip = self.get_client_ip(request)
        rate_key = f'google_login_rate:{client_ip}'
        request_count = cache.get(rate_key, 0)

        if request_count > 10:  # 1분에 10회 제한
            return Response(
                {'error': 'Too many requests. Please try again later.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )

        try:
            # Google ID Token 검증
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID,
                clock_skew_in_seconds=10
            )

            # 1. Audience(aud) 명시적 검증
            if idinfo.get('aud') != settings.GOOGLE_OAUTH_CLIENT_ID:
                return Response(
                    {'error': 'Invalid audience'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 2. 토큰 발급자(iss) 확인
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                return Response(
                    {'error': 'Invalid token issuer'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 3. 토큰 만료 시간 확인 (추가 보안)
            current_time = int(time.time())
            if idinfo.get('exp', 0) < current_time:
                return Response(
                    {'error': 'Token has expired'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 4. Email 검증 여부 확인 (Google에서 이메일을 검증했는지)
            if not idinfo.get('email_verified', False):
                return Response(
                    {'error': 'Email not verified by Google'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 5. 토큰 재사용 방지 (Nonce 체크)
            jti = idinfo.get('jti') or f"{idinfo['sub']}:{idinfo['iat']}"
            nonce_key = f'google_token_nonce:{jti}'

            if cache.get(nonce_key):
                return Response(
                    {'error': 'Token has already been used'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # 토큰을 사용했다고 표시 (만료 시간까지 캐시)
            ttl = idinfo.get('exp', current_time + 3600) - current_time
            cache.set(nonce_key, True, ttl)

            # 사용자 정보 추출
            google_id = idinfo['sub']
            email = idinfo.get('email')
            name = idinfo.get('name', '')
            picture = idinfo.get('picture', '')

            # 사용자 생성 또는 조회
            user, created = User.objects.get_or_create(
                google_id=google_id,
                defaults={
                    'email': email,
                    'username': email.split('@')[0] if email else f'user_{google_id}',
                    'profile_image': picture,
                }
            )

            # 기존 사용자의 정보 업데이트
            if not created:
                if picture and not user.profile_image:
                    user.profile_image = picture
                    user.save()

            # JWT 토큰 생성
            refresh = RefreshToken.for_user(user)

            # Rate limit 카운터 증가
            cache.set(rate_key, request_count + 1, 60)

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            # Invalid token
            cache.set(rate_key, request_count + 1, 60)
            return Response(
                {'error': f'Invalid token: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            cache.set(rate_key, request_count + 1, 60)
            return Response(
                {'error': f'Authentication failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def get_client_ip(self, request):
        """클라이언트 IP 주소 추출"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


class GoogleConfigView(APIView):
    """Google OAuth 설정 정보 반환"""
    permission_classes = [permissions.AllowAny]

    def get(self, request):
        """Google OAuth Client ID 반환"""
        return Response({
            'client_id': settings.GOOGLE_OAUTH_CLIENT_ID
        })


class CurrentUserView(generics.RetrieveAPIView):
    """현재 로그인한 사용자 정보 조회"""
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        return self.request.user
