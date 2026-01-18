from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, Language, Country


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """커스텀 사용자 관리자"""
    list_display = ['email', 'username', 'role', 'is_staff', 'is_active', 'google_id', 'date_joined']
    list_filter = ['role', 'is_staff', 'is_active', 'date_joined']
    search_fields = ['email', 'username', 'google_id']
    ordering = ['-date_joined']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('역할', {'fields': ('role',)}),
        ('소셜 정보', {'fields': ('google_id', 'profile_image')}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('추가 정보', {
            'fields': ('email', 'role', 'profile_image', 'google_id'),
        }),
    )


@admin.register(Language)
class LanguageAdmin(admin.ModelAdmin):
    """언어 관리자"""
    list_display = ['code', 'name_ko', 'name_en']
    search_fields = ['code', 'name_ko', 'name_en']
    ordering = ['code']


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    """국가 관리자"""
    list_display = ['code', 'name_ko', 'name_en']
    search_fields = ['code', 'name_ko', 'name_en']
    ordering = ['code']


class LearningLanguageInline(admin.TabularInline):
    """배우고자 하는 언어 인라인"""
    model = UserProfile.learning_languages.through
    extra = 1


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """사용자 프로필 관리자"""
    list_display = ['nickname', 'user_email', 'country', 'created_at', 'updated_at']
    list_filter = ['country', 'created_at', 'updated_at']
    search_fields = ['nickname', 'user__email']
    readonly_fields = ['created_at', 'updated_at']
    inlines = [LearningLanguageInline]

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = '사용자 이메일'
