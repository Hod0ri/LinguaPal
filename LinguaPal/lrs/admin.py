"""
LRS Admin Configuration

Admin interface for xAPI Statements, cmi5 Sessions, and LRS Credentials.
"""

from django.contrib import admin
from django.utils.html import format_html

from .models import XAPIStatement, CMI5Session, LRSCredential


@admin.register(XAPIStatement)
class XAPIStatementAdmin(admin.ModelAdmin):
    """Admin configuration for xAPI Statements."""

    list_display = [
        'id_short',
        'actor_name',
        'verb_display',
        'object_id_short',
        'result_success',
        'result_score_scaled',
        'timestamp',
    ]
    list_filter = [
        'verb_id',
        'result_success',
        'timestamp',
    ]
    search_fields = [
        'actor_name',
        'actor_mbox',
        'object_id',
        'verb_display',
    ]
    readonly_fields = [
        'id',
        'stored',
    ]
    date_hierarchy = 'timestamp'

    fieldsets = (
        ('Actor', {
            'fields': ('actor_user', 'actor_mbox', 'actor_name')
        }),
        ('Verb', {
            'fields': ('verb_id', 'verb_display')
        }),
        ('Object', {
            'fields': ('object_type', 'object_id', 'object_definition')
        }),
        ('Result', {
            'fields': (
                'result_success',
                'result_response',
                ('result_score_scaled', 'result_score_raw'),
                ('result_score_min', 'result_score_max'),
                'result_completion',
                'result_duration',
            ),
            'classes': ('collapse',)
        }),
        ('Context', {
            'fields': ('context_registration', 'context_extensions'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('id', 'timestamp', 'stored')
        }),
    )

    def id_short(self, obj):
        """Display shortened UUID."""
        return str(obj.id)[:8]
    id_short.short_description = 'ID'

    def object_id_short(self, obj):
        """Display shortened object ID."""
        return obj.object_id.split('/')[-1] if obj.object_id else ''
    object_id_short.short_description = 'Object'


@admin.register(CMI5Session)
class CMI5SessionAdmin(admin.ModelAdmin):
    """Admin configuration for cmi5 Sessions."""

    list_display = [
        'registration_short',
        'actor_user',
        'au_type',
        'state_badge',
        'is_passed',
        'is_completed',
        'score_scaled',
        'launched_at',
    ]
    list_filter = [
        'state',
        'au_type',
        'is_passed',
        'is_completed',
        'launched_at',
    ]
    search_fields = [
        'actor_user__email',
        'au_id',
        'registration',
    ]
    readonly_fields = [
        'id',
        'registration',
        'launched_at',
    ]
    date_hierarchy = 'launched_at'

    fieldsets = (
        ('Session', {
            'fields': ('id', 'registration', 'state')
        }),
        ('Actor', {
            'fields': ('actor_user',)
        }),
        ('Assignable Unit', {
            'fields': ('au_id', 'au_type', 'au_object_id')
        }),
        ('cmi5 Configuration', {
            'fields': ('mastery_score', 'launch_mode', 'move_on')
        }),
        ('Timestamps', {
            'fields': ('launched_at', 'initialized_at', 'terminated_at')
        }),
        ('Results', {
            'fields': ('is_passed', 'is_completed', 'score_scaled')
        }),
    )

    def registration_short(self, obj):
        """Display shortened registration UUID."""
        return str(obj.registration)[:8]
    registration_short.short_description = 'Registration'

    def state_badge(self, obj):
        """Display state with color badge."""
        colors = {
            'launched': 'blue',
            'initialized': 'orange',
            'terminated': 'green',
            'abandoned': 'red',
        }
        color = colors.get(obj.state, 'gray')
        return format_html(
            '<span style="color: white; background-color: {}; padding: 2px 8px; '
            'border-radius: 4px;">{}</span>',
            color,
            obj.state.upper()
        )
    state_badge.short_description = 'State'


@admin.register(LRSCredential)
class LRSCredentialAdmin(admin.ModelAdmin):
    """Admin configuration for LRS Credentials."""

    list_display = [
        'name',
        'key',
        'is_active_badge',
        'permissions_display',
        'created_by',
        'last_used_at',
        'created_at',
    ]
    list_filter = [
        'is_active',
        'created_at',
    ]
    search_fields = [
        'name',
        'key',
    ]
    readonly_fields = [
        'id',
        'key',
        'secret_hash',
        'created_at',
        'last_used_at',
    ]

    fieldsets = (
        ('Credential', {
            'fields': ('name', 'key', 'is_active')
        }),
        ('Permissions', {
            'fields': ('permissions',)
        }),
        ('Security', {
            'fields': ('secret_hash',),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'last_used_at')
        }),
    )

    def is_active_badge(self, obj):
        """Display active status with color."""
        if obj.is_active:
            return format_html(
                '<span style="color: green;">Active</span>'
            )
        return format_html(
            '<span style="color: red;">Inactive</span>'
        )
    is_active_badge.short_description = 'Status'

    def permissions_display(self, obj):
        """Display permissions as badges."""
        if not obj.permissions:
            return '-'
        return ', '.join(obj.permissions)
    permissions_display.short_description = 'Permissions'
