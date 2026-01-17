from rest_framework import serializers
from .models import User


class UserSerializer(serializers.ModelSerializer):
    """사용자 시리얼라이저"""
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'profile_image', 'google_id', 'date_joined']
        read_only_fields = ['id', 'google_id', 'date_joined']
