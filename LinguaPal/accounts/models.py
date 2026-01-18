from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """커스텀 사용자 모델"""

    class Role(models.TextChoices):
        ADMIN = 'admin', '관리자'
        STAFF = 'staff', '스태프'
        USER = 'user', '일반 사용자'

    email = models.EmailField(unique=True, verbose_name='이메일')
    profile_image = models.URLField(blank=True, null=True, verbose_name='프로필 이미지')
    google_id = models.CharField(max_length=255, blank=True, null=True, unique=True, verbose_name='Google ID')
    role = models.CharField(
        max_length=10,
        choices=Role.choices,
        default=Role.USER,
        verbose_name='역할'
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        verbose_name = '사용자'
        verbose_name_plural = '사용자 목록'

    def __str__(self):
        return self.email

    @property
    def is_admin_role(self):
        """Admin 역할 여부"""
        return self.role == self.Role.ADMIN

    @property
    def is_staff_role(self):
        """Staff 역할 여부"""
        return self.role == self.Role.STAFF

    @property
    def is_user_role(self):
        """일반 사용자 역할 여부"""
        return self.role == self.Role.USER

    def save(self, *args, **kwargs):
        # Admin 역할인 경우 Django의 is_staff, is_superuser 자동 설정
        if self.role == self.Role.ADMIN:
            self.is_staff = True
            self.is_superuser = True
        else:
            self.is_staff = False
            self.is_superuser = False
        super().save(*args, **kwargs)


class Language(models.Model):
    """언어 마스터 테이블"""
    code = models.CharField(max_length=10, unique=True, verbose_name='언어 코드')
    name_ko = models.CharField(max_length=50, verbose_name='언어명 (한국어)')
    name_en = models.CharField(max_length=50, verbose_name='언어명 (영어)')

    class Meta:
        verbose_name = '언어'
        verbose_name_plural = '언어 목록'
        ordering = ['code']

    def __str__(self):
        return f"{self.name_ko} ({self.code})"


class Country(models.Model):
    """국가 마스터 테이블"""
    code = models.CharField(max_length=3, unique=True, verbose_name='국가 코드')
    name_ko = models.CharField(max_length=50, verbose_name='국가명 (한국어)')
    name_en = models.CharField(max_length=50, verbose_name='국가명 (영어)')

    class Meta:
        verbose_name = '국가'
        verbose_name_plural = '국가 목록'
        ordering = ['code']

    def __str__(self):
        return f"{self.name_ko} ({self.code})"


class UserProfile(models.Model):
    """사용자 프로필"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile', verbose_name='사용자')
    nickname = models.CharField(max_length=50, unique=True, verbose_name='닉네임')
    country = models.ForeignKey(Country, on_delete=models.PROTECT, verbose_name='출신 국가')
    learning_languages = models.ManyToManyField(Language, related_name='learners', verbose_name='배우고자 하는 언어')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')

    class Meta:
        verbose_name = '사용자 프로필'
        verbose_name_plural = '사용자 프로필 목록'

    def __str__(self):
        return f"{self.nickname} ({self.user.email})"
