from django.contrib import admin
from django.contrib.auth.models import Group
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from accounts.models import User, Plan, PlanFeature

admin.site.unregister(Group)

admin.site.site_header = "Prune Admin Panel"
admin.site.site_title = "Prune Admin Panel"
admin.site.index_title = "Welcome to Prune Admin Panel"


class PlanFeatureInline(admin.TabularInline):
    model = PlanFeature
    extra = 1
    fields = ('feature',)


@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = (
        'name',
        'billing_period_badge',
        'price_display',
        'duration_display',
        'order',
        'active',
        'features_count',
        'subscribers_count',
    )
    list_filter = ('active', 'billing_period')
    search_fields = ('name', 'discount_note')
    list_editable = ('order', 'active')
    ordering = ('order', 'id')
    inlines = (PlanFeatureInline,)

    fieldsets = (
        (_('General Information'), {
            'fields': ('name', 'billing_period', 'order', 'active')
        }),
        (_('Pricing & Billing Terms'), {
            'fields': (
                ('price', 'duration'),
                'discount_note',
            )
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related('features', 'users')

    @admin.display(description=_('Billing Period'), ordering='billing_period')
    def billing_period_badge(self, obj):
        colors = {
            Plan.ANNUAL: '#6f42c1',   # Purple
            Plan.MONTHLY: '#0d6efd',  # Blue
            Plan.TRIAL: '#ffc107',    # Amber/Yellow
        }
        color = colors.get(obj.billing_period, '#6c757d')
        text_color = '#000' if obj.billing_period == Plan.TRIAL else '#fff'
        return format_html(
            '<span style="background-color: {}; color: {}; padding: 3px 8px; border-radius: 4px; font-weight: 600; font-size: 11px;">{}</span>',
            color,
            text_color,
            obj.get_billing_period_display(),
        )

    @admin.display(description=_('Price'), ordering='price')
    def price_display(self, obj):
        if obj.price == 0:
            return format_html('<span style="color: #198754; font-weight: bold;">Free</span>')
        return f"${obj.price:,.2f}"

    @admin.display(description=_('Duration'), ordering='duration')
    def duration_display(self, obj):
        return f"{obj.duration} day{'s' if obj.duration > 1 else ''}"

    @admin.display(description=_('Features'))
    def features_count(self, obj):
        return obj.features.count()

    @admin.display(description=_('Subscribers'))
    def subscribers_count(self, obj):
        return obj.users.count()


@admin.register(User)
class CustomUserAdmin(BaseUserAdmin):
    # List view layout
    list_display = (
        'id',
        'full_name',
        'email',
        'plan__name',
        'status_badge',
        'is_staff',
        'is_superuser',
        'created_at',
    )
    list_filter = ('status', 'is_staff', 'is_superuser', 'plan', 'is_active', 'created_at')
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
        (_('Plan Details'), {
            'fields': (
                ('plan', 'plan_lock_price', 'plan_price'),
                ('plan_start_date', 'plan_end_date'),
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
            User.ACTIVE: '#198754',     # Green
            User.INACTIVE: '#6c757d',   # Gray
            User.SUSPENDED: '#fd7e14',  # Orange
            User.DELETED: '#dc3545',    # Red
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
        queryset.update(status=User.ACTIVE)

    @admin.action(description=_('Mark selected users as Suspended'))
    def mark_as_suspended(self, request, queryset):
        queryset.update(status=User.SUSPENDED)

    @admin.action(description=_('Mark selected users as Deleted'))
    def mark_as_deleted(self, request, queryset):
        queryset.update(status=User.DELETED)


