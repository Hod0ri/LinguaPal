from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """커스텀 사용자 관리자"""
    list_display = ['email', 'username', 'is_staff', 'is_active', 'google_id', 'date_joined']
    list_filter = ['is_staff', 'is_active', 'date_joined']
    search_fields = ['email', 'username', 'google_id']
    ordering = ['-date_joined']

    fieldsets = BaseUserAdmin.fieldsets + (
        ('소셜 정보', {'fields': ('google_id', 'profile_image')}),
    )

    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('추가 정보', {
            'fields': ('email', 'profile_image', 'google_id'),
        }),
    )
