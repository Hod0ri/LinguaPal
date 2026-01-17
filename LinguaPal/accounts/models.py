from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """커스텀 사용자 모델"""
    email = models.EmailField(unique=True, verbose_name='이메일')
    profile_image = models.URLField(blank=True, null=True, verbose_name='프로필 이미지')
    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True, verbose_name='Google ID')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = '사용자'
        verbose_name_plural = '사용자 목록'

    def __str__(self):
        return self.email
