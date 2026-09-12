from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _
from .managers import CustomUserManager
from django.core.validators import MinValueValidator

class Plan(models.Model):
    ANNUAL = 'annual'
    MONTHLY = 'monthly'
    TRIAL = 'trial'
    
    BILLING_PERIOD_CHOICES = [
        (ANNUAL, 'Annual'),
        (MONTHLY, 'Monthly'),
        (TRIAL, 'Trial'),
    ]
    name = models.CharField(max_length=50, unique=True)
    billing_period = models.CharField(max_length=20, choices=BILLING_PERIOD_CHOICES, default=MONTHLY)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.PositiveBigIntegerField(validators=[MinValueValidator(1)])
    active = models.BooleanField(default=True)
    discount_note = models.CharField(max_length=255, null=True, blank=True)
    order = models.PositiveIntegerField(default=0)
    
    def __str__(self):
        return f"({self.get_name_display()}) - ${self.price if self.price > 0 else 'Free'} for {self.duration} day(s) - {'Active' if self.active else 'Inactive'}"
    
    class Meta:
        unique_together = ('name', 'active', 'price', 'duration')
        ordering = ['order', 'id']
        verbose_name = 'Plan'
        verbose_name_plural = 'Plans'
    
    def save(self, *args, **kwargs):
        if not self.order:
            max_order = Plan.objects.aggregate(models.Max('order'))['order__max'] or 0
            self.order = max_order + 1
        super().save(*args, **kwargs)

class PlanFeature(models.Model):
    plan = models.ForeignKey(Plan, related_name='features', on_delete=models.CASCADE)
    feature = models.CharField(max_length=255)
    
    class Meta:
        unique_together = ('plan', 'feature')
        ordering = ['id']
        verbose_name = 'Plan Feature'
        verbose_name_plural = 'Plan Features'

class User(AbstractUser):
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
    username = None
    email = models.EmailField(unique=True)
    profile_picture = models.ImageField(upload_to='profile_pictures/', null=True, blank=True)
    status = models.CharField(max_length=20, default=ACTIVE, choices=STATUS_CHOICES)
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, related_name='users', null=True, blank=True)
    plan_lock_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    plan_price = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    plan_start_date = models.DateTimeField(null=True, blank=True)
    plan_end_date = models.DateTimeField(null=True, blank=True)
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
    
    class Meta:
        verbose_name = 'User'
        verbose_name_plural = 'Users'
        ordering = ['is_superuser', '-created_at']

class HealthProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='health_profiles')
    dob = models.DateField(null=True, blank=True)
    height = models.CharField(max_length=10, null=True, blank=True)
    weight = models.CharField(max_length=10, null=True, blank=True)
    blood_group = models.CharField(max_length=5, null=True, blank=True)
    sleep_hours = models.CharField(max_length=10, null=True, blank=True)
    cycle = models.CharField(max_length=10, null=True, blank=True)
    diet = models.CharField(max_length=255, null=True, blank=True)
    mind_health = models.JSONField(default=list, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Health Profile of {self.user.first_name} {self.user.last_name} ({self.user.email})"
    
    class Meta:
        verbose_name = 'Health Profile'
        verbose_name_plural = 'Health Profiles'


