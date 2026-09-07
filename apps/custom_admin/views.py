import uuid
import random
from datetime import timedelta
from core.base import NewAPIView, AutoPaginatedResponse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from core.exceptions import _format_error_message
from custom_admin.serializers import UserListSerializer
from accounts.tasks import send_activation_otp_email, send_reset_otp_email
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import Plan, PlanFeature
from drf_yasg import openapi

User = get_user_model()

class UserListAPIView(NewAPIView):
    serializer_class = UserListSerializer
    permission_classes = [IsAdminUser]
    http_method_names = ['get']
    parser_classes = [JSONParser]

    @swagger_auto_schema(
        manual_parameters=[
            openapi.Parameter('page', openapi.IN_QUERY, description='Page number', type=openapi.TYPE_INTEGER, default=1),
            openapi.Parameter('page_size', openapi.IN_QUERY, description='Number of items per page', type=openapi.TYPE_INTEGER, default=10),
            openapi.Parameter('search', openapi.IN_QUERY, description='Search query', type=openapi.TYPE_STRING),
            openapi.Parameter('order_by', openapi.IN_QUERY, description='Order by field', type=openapi.TYPE_STRING, default='created_at'),
            openapi.Parameter('order_direction', openapi.IN_QUERY, description='Order direction', type=openapi.TYPE_STRING, default='desc'),
        ],
        tags=['Admin - User Management'], 
        responses={
            status.HTTP_200_OK: UserListSerializer(many=True)
        }
    )
    def get(self, request):
        """
        **Get all users**\n\n
        Returns all users with pagination\n\n
        **Parameters**\n\n
        - `page`: Page number (default: 1)\n\n
        - `page_size`: Number of items per page (default: 10)
        - `search`: Search query (default: None)
        - `order_by`: Order by field (default: 'created_at')
        - `order_direction`: Order direction (default: 'desc')
        
        ### Response
        ```json
        {
            "message": "Users fetched successfully",
            "data": [
                {
                    "id": 1,
                    "first_name": "John",
                    "last_name": "Doe",
                    "profile_picture": "https://example.com/profile.jpg",
                    "email": "[EMAIL_ADDRESS]",
                    "status": "active",
                    "plan": {
                        "id": 1,
                        "name": "Free",
                        "price": 0.00,
                        "billing_period": "monthly",
                        "duration": 30,
                        "active": True,
                        "discount_note": None
                    },
                    "plan_start_date": "2022-01-01T00:00:00Z",
                    "plan_end_date": "2022-02-01T00:00:00Z",
                    "joined_at": "2022-01-01"
                }
            ],
            "meta": {
                "total": 100,
                "page": 1,
                "page_size": 10,
                "total_pages": 10,
                "has_next": True,
                "has_previous": False
            }
        }
        ```
        """
        users = User.objects.select_related('plan').all()
        serializer = self.get_serializer(users, many=True, context={'request': request})
        return AutoPaginatedResponse(serializer.data, request=request)


