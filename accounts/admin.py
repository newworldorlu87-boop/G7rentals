from django.contrib import admin
from django import forms
from django.contrib.auth import get_user_model
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import path
from django.template.response import TemplateResponse
from django.utils.html import format_html
from .models import User, Profile, Notification, EmailVerification, PasswordReset

User = get_user_model()


# ============================================
# PROFILE INLINE
# ============================================

class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile'
    fields = ['avatar', 'address', 'city', 'country', 'bio', 
              'is_landlord', 'company_name', 'business_address']


# ============================================
# CUSTOM USER ADMIN
# ============================================

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'username', 'user_type', 'phone', 
                    'is_verified', 'is_landlord', 'is_staff', 'date_joined']
    list_filter = ['user_type', 'is_verified', 'is_landlord', 'is_staff', 'date_joined']
    search_fields = ['email', 'username', 'phone']
    readonly_fields = ['date_joined', 'last_login']
    inlines = [ProfileInline]
    fieldsets = (
        ('Basic Info', {
            'fields': ('email', 'username', 'password')
        }),
        ('User Type', {
            'fields': ('user_type', 'is_landlord')
        }),
        ('Contact', {
            'fields': ('phone',)
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active', 'is_staff', 'is_superuser')
        }),
        ('Important Dates', {
            'fields': ('date_joined', 'last_login'),
            'classes': ('collapse',)
        }),
    )


# ============================================
# NOTIFICATION ADMIN — WITH SEND FEATURE
# ============================================

class SendNotificationForm(forms.Form):
    RECIPIENT_CHOICES = (
        ('ALL', '🌍 All Users'),
        ('TENANTS', '🏠 All Tenants'),
        ('LANDLORDS', '🏢 All Landlords'),
        ('SPECIFIC', '👤 Specific User'),
    )

    target_group = forms.ChoiceField(
        choices=RECIPIENT_CHOICES,
        widget=forms.RadioSelect,
        initial='ALL',
        label="Send To"
    )

    specific_user = forms.ModelChoiceField(
        queryset=User.objects.filter(is_active=True),
        required=False,
        label="Select Specific User",
        empty_label="-- Choose a user --"
    )

    title = forms.CharField(
        max_length=200,
        label="Notification Title",
        widget=forms.TextInput(attrs={'placeholder': 'e.g. System Maintenance'})
    )

    message = forms.CharField(
        widget=forms.Textarea(attrs={
            'rows': 5, 
            'placeholder': 'Enter your notification message here...'
        }),
        label="Message"
    )

    priority = forms.ChoiceField(
        choices=Notification.PRIORITY_CHOICES,
        initial='NORMAL',
        label="Priority"
    )


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['title', 'sender_display', 'target_badge', 
                    'priority_badge', 'is_read', 'created_at', 'recipient_count']
    list_filter = ['target_group', 'priority', 'is_read', 'created_at']
    search_fields = ['title', 'message', 'recipient__email', 'recipient__username']
    readonly_fields = ['created_at', 'read_at', 'recipient_count_display']
    date_hierarchy = 'created_at'

    change_list_template = 'admin/notifications/notification_changelist.html'

    fieldsets = (
        ('Sender Info', {'fields': ('sender',)}),
        ('Recipient', {'fields': ('target_group', 'recipient')}),
        ('Content', {'fields': ('title', 'message')}),
        ('Status', {'fields': ('priority', 'is_read', 'read_at')}),
        ('Metadata', {
            'fields': ('created_at', 'recipient_count_display'),
            'classes': ('collapse',)
        }),
    )

    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(
                'send-notification/',
                self.admin_site.admin_view(self.send_notification_view),
                name='send-notification',
            ),
        ]
        return custom_urls + urls

    def send_notification_view(self, request):
        if request.method == 'POST':
            form = SendNotificationForm(request.POST)
            if form.is_valid():
                data = form.cleaned_data
                target_group = data['target_group']
                title = data['title']
                message_text = data['message']
                priority = data['priority']
                specific_user = data.get('specific_user')

                if target_group == 'ALL':
                    recipients = User.objects.filter(is_active=True)
                elif target_group == 'TENANTS':
                    recipients = User.objects.filter(is_active=True, user_type='tenant')
                elif target_group == 'LANDLORDS':
                    recipients = User.objects.filter(is_active=True, user_type='landlord')
                else:
                    if not specific_user:
                        self.message_user(request, 'Please select a specific user.', messages.ERROR)
                        return redirect('admin:send-notification')
                    recipients = [specific_user]

                count = 0
                for user in recipients:
                    Notification.objects.create(
                        sender=request.user,
                        recipient=user,
                        target_group=target_group,
                        title=title,
                        message=message_text,
                        priority=priority
                    )
                    count += 1

                self.message_user(request, f'✅ Sent "{title}" to {count} user(s).', messages.SUCCESS)
                return redirect('admin:accounts_notification_changelist')
        else:
            form = SendNotificationForm()

        context = {
            **self.admin_site.each_context(request),
            'form': form,
            'title': 'Send Notification to Users',
            'opts': self.model._meta,
            'all_users_count': User.objects.filter(is_active=True).count(),
            'tenant_count': User.objects.filter(is_active=True, user_type='tenant').count(),
            'landlord_count': User.objects.filter(is_active=True, user_type='landlord').count(),
        }
        return TemplateResponse(request, 'admin/notifications/send_notification.html', context)

    def sender_display(self, obj):
        if obj.sender:
            return format_html('<span style="color:#2563eb;font-weight:600;">{}</span>', obj.sender.email)
        return '-'
    sender_display.short_description = 'Sent By'

    def target_badge(self, obj):
        colors = {'ALL': '#7c3aed', 'TENANTS': '#059669', 'LANDLORDS': '#d97706', 'SPECIFIC': '#2563eb'}
        color = colors.get(obj.target_group, '#64748b')
        return format_html(
            '<span style="background:{};color:white;padding:3px 10px;border-radius:999px;font-size:11px;font-weight:700;">{}</span>',
            color, obj.get_target_group_display())
    target_badge.short_description = 'Target'

    def priority_badge(self, obj):
        colors = {'LOW': '#94a3b8', 'NORMAL': '#2563eb', 'HIGH': '#d97706', 'URGENT': '#dc2626'}
        color = colors.get(obj.priority, '#64748b')
        return format_html(
            '<span style="background:{}20;color:{};padding:3px 10px;border-radius:999px;font-size:11px;font-weight:700;">{}</span>',
            color, color, obj.get_priority_display())
    priority_badge.short_description = 'Priority'

    def recipient_count(self, obj):
        if obj.target_group == 'SPECIFIC':
            return 1
        elif obj.target_group == 'ALL':
            return User.objects.filter(is_active=True).count()
        elif obj.target_group == 'TENANTS':
            return User.objects.filter(is_active=True, user_type='tenant').count()
        elif obj.target_group == 'LANDLORDS':
            return User.objects.filter(is_active=True, user_type='landlord').count()
        return 0
    recipient_count.short_description = 'Recipients'

    def recipient_count_display(self, obj):
        count = self.recipient_count(obj)
        return format_html('<span style="font-size:1.2rem;font-weight:700;color:#2563eb;">{}</span> users', count)
    recipient_count_display.short_description = 'Total Recipients'


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'city', 'country', 'is_landlord', 'created_at']
    list_filter = ['is_landlord', 'country', 'created_at']
    search_fields = ['user__email', 'user__username', 'city', 'company_name']
    readonly_fields = ['created_at']


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'is_used', 'created_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'token']
    readonly_fields = ['token', 'created_at']


@admin.register(PasswordReset)
class PasswordResetAdmin(admin.ModelAdmin):
    list_display = ['user', 'token', 'is_used', 'created_at']
    list_filter = ['is_used', 'created_at']
    search_fields = ['user__email', 'token']
    readonly_fields = ['token', 'created_at']