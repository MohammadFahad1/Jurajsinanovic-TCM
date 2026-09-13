import requests_oauthlib
from django.contrib.auth import get_user_model
from rest_framework import permissions
from django.utils import timezone

User = get_user_model()

class IsSubscribedUser(permissions.BasePermission):
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        
        if user.is_superuser:
            return True

        if not user.plan or user.plan and user.plan_end_date < timezone.now():
            return False

        return True
        
        