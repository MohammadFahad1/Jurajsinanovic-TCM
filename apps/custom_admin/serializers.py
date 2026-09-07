from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class UserListSerializer(serializers.ModelSerializer):
    joined_at = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "first_name", "last_name", "profile_picture", "email", "status", "plan", "plan_start_date", "plan_end_date", "joined_at"]
    
    def get_joined_at(self, obj):
        return obj.created_at.strftime("%b %d, %Y") if getattr(obj, 'created_at', None) else None

    

