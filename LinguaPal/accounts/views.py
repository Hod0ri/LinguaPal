from rest_framework import generics, permissions, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from google.oauth2 import id_token
from google.auth.transport import requests
from django.conf import settings
from .models import User
from .serializers import UserSerializer


class GoogleLoginView(APIView):
    """Google OAuth2 로그인 뷰 - ID Token 검증"""
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        """Google ID Token을 검증하고 사용자 생성/로그인"""
        token = request.data.get('access_token')

        if not token:
            return Response(
                {'error': 'access_token is required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            # Google ID Token 검증 (10초 시간 여유 허용)
            idinfo = id_token.verify_oauth2_token(
                token,
                requests.Request(),
                settings.GOOGLE_OAUTH_CLIENT_ID,
                clock_skew_in_seconds=10
            )

            # 토큰 발급자 확인
            if idinfo['iss'] not in ['accounts.google.com', 'https://accounts.google.com']:
                return Response(
                    {'error': 'Invalid token issuer'},
                    status=status.HTTP_400_BAD_REQUEST
                )

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

            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            # Invalid token
            return Response(
                {'error': f'Invalid token: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            return Response(
                {'error': f'Authentication failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


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
