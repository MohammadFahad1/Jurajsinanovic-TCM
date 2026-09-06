from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager

ACTIVE = 'active'
INACTIVE = 'inactive'
SUSPENDED = 'suspended'
DELETED = 'deleted'

STATUS_CHOICES = (
    (ACTIVE, 'Active'),
    (INACTIVE, 'Inactive'),
    (SUSPENDED, 'Suspended'),
    (DELETED, 'Deleted'),
)

class User(AbstractUser):
    username = None
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    status = models.CharField(max_length=20, default=ACTIVE, choices=STATUS_CHOICES)
    otp = models.IntegerField(null=True, blank=True)
    otp_created_at = models.DateTimeField(null=True, blank=True)
    forgot_password_token = models.UUIDField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    objects = CustomUserManager()

    def __str__(self):
        return f"#{self.pk} - {self.first_name} {self.last_name} ({self.email})"

