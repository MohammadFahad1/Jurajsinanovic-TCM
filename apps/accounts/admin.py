from django.contrib import admin
from django.contrib.auth.models import Group
from accounts.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from .models import User, ACTIVE, INACTIVE, SUSPENDED, DELETED

admin.site.unregister(Group)

admin.site.site_header = "Prune Admin Panel"
admin.site.site_title = "Prune Admin Panel"
admin.site.index_title = "Welcome to Prune Admin Panel"

@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    # List view layout
    list_display = (
        'id',
        'full_name',
        'email',
        'status_badge',
        'is_staff',
        'is_superuser',
        'created_at',
    )
    list_filter = ('status', 'is_staff', 'is_superuser', 'is_active', 'created_at')
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('-created_at',)
    readonly_fields = (
        'created_at',
        'updated_at',
        # 'otp_created_at',
        # 'forgot_password_token',
        'avatar_preview',
    )

    # BaseUserAdmin default ordering/search expects 'username', so override them
    search_help_text = _('Search by email, first name, or last name.')

    # Form fieldsets for editing existing records
    fieldsets = (
        (_('Authentication'), {
            'fields': ('email', 'password')
        }),
        (_('Personal Information'), {
            'fields': (
                ('first_name', 'last_name'),
                'profile_picture',
                'avatar_preview',
            )
        }),
        (_('Status & Access'), {
            'fields': ('status', 'is_active', 'is_staff', 'is_superuser')
        }),
        (_('Security Tokens'), {
            'classes': ('collapse',),
            'fields': (
                'otp',
                'otp_created_at',
                'forgot_password_token',
            ),
        }),
        (_('Important Dates'), {
            'classes': ('collapse',),
            'fields': ('last_login', 'created_at', 'updated_at'),
        }),
    )

    # Form fieldsets for creating a user via the admin panel
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email',
                'first_name',
                'last_name',
                'status',
                'password1',
                'password2',
                'is_staff',
                'is_superuser',
            ),
        }),
    )

    # Custom columns & formatters
    @admin.display(description=_('Name'), ordering='first_name')
    def full_name(self, obj):
        name = f"{obj.first_name} {obj.last_name}".strip()
        return name if name else _('(No Name)')

    @admin.display(description=_('Status'), ordering='status')
    def status_badge(self, obj):
        color_map = {
            ACTIVE: '#198754',     # Green
            INACTIVE: '#6c757d',   # Gray
            SUSPENDED: '#fd7e14',  # Orange
            DELETED: '#dc3545',    # Red
        }
        color = color_map.get(obj.status, '#6c757d')
        return format_html(
            '<span style="background-color: {}; color: #fff; padding: 3px 8px; '
            'border-radius: 4px; font-weight: 600; font-size: 11px; text-transform: uppercase;">{}</span>',
            color,
            obj.get_status_display(),
        )

    @admin.display(description=_('Current Avatar'))
    def avatar_preview(self, obj):
        if obj.profile_picture:
            return format_html(
                '<img src="{}" style="max-height: 100px; max-width: 100px; '
                'border-radius: 50%; object-fit: cover; border: 1px solid #ccc;" />',
                obj.profile_picture.url,
            )
        return _('No profile picture uploaded')

    # Bulk status action methods
    actions = ['mark_as_active', 'mark_as_suspended', 'mark_as_deleted']

    @admin.action(description=_('Mark selected users as Active'))
    def mark_as_active(self, request, queryset):
        queryset.update(status=ACTIVE)

    @admin.action(description=_('Mark selected users as Suspended'))
    def mark_as_suspended(self, request, queryset):
        queryset.update(status=SUSPENDED)

    @admin.action(description=_('Mark selected users as Deleted'))
    def mark_as_deleted(self, request, queryset):
        queryset.update(status=DELETED)


