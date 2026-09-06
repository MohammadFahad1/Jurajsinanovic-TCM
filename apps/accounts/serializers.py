from rest_framework import serializers
from accounts.models import Plan, PlanFeature
from django.contrib.auth import get_user_model

User = get_user_model()

class UserSignUpSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('email', 'password', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': True},
            'last_name': {'required': True},
            'email': {'required': True},
            'password': {'required': True}
        }




