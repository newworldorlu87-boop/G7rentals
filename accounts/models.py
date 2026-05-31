from django.contrib.auth.models import AbstractUser
from django.db import models
from django.conf import settings
import uuid


# ============================================
# 1. USER MODEL FIRST — before anything references it
# ============================================

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('tenant', 'Tenant'),
        ('landlord', 'Landlord'),
    )

    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True, null=True)
    is_verified = models.BooleanField(default=False)
    is_landlord = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return f"{self.email} ({self.user_type})"


# ============================================
# 2. NOW define models that reference User
# ============================================

class Notification(models.Model):
    TARGET_CHOICES = [
        ('ALL', 'All Users'),
        ('LANDLORDS', 'All Landlords'),
        ('TENANTS', 'All Tenants'),
        ('SPECIFIC', 'Specific User'),
    ]
    
    PRIORITY_CHOICES = [
        ('LOW', 'Low'),
        ('NORMAL', 'Normal'),
        ('HIGH', 'High'),
        ('URGENT', 'Urgent'),
    ]

    sender = models.ForeignKey(
        'accounts.User',           # ← Use string reference (lazy, safe)
        on_delete=models.CASCADE,
        related_name='sent_notifications',
        limit_choices_to={'is_staff': True}
    )
    recipient = models.ForeignKey(
        'accounts.User',           # ← String reference
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
        help_text="Only required if Target is 'Specific User'"
    )
    target_group = models.CharField(
        max_length=20,
        choices=TARGET_CHOICES,
        default='ALL'
    )
    title = models.CharField(max_length=200)
    message = models.TextField()
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='NORMAL'
    )
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['recipient', 'is_read']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} → {self.get_target_group_display()}"


class Profile(models.Model):
    user = models.OneToOneField(
        'accounts.User',           # ← String reference
        on_delete=models.CASCADE
    )
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    address = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, default='Nigeria')
    bio = models.TextField(blank=True)
    is_landlord = models.BooleanField(default=False)
    company_name = models.CharField(max_length=255, blank=True)
    business_address = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile - {self.user.email}"


class EmailVerification(models.Model):
    user = models.ForeignKey(
        'accounts.User',           # ← String reference
        on_delete=models.CASCADE
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Verification for {self.user.email}"


class PasswordReset(models.Model):
    user = models.ForeignKey(
        'accounts.User',           # ← String reference
        on_delete=models.CASCADE
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def __str__(self):
        return f"Password reset for {self.user.email}"