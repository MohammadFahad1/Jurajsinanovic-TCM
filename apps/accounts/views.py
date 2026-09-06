import random
from core.base import NewAPIView
from rest_framework.response import Response
from rest_framework import status
from accounts.serializers import UserSignUpSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from accounts.tasks import send_activation_otp_email

User = get_user_model()

class UserSignUpView(NewAPIView):
    serializer_class = UserSignUpSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

    @swagger_auto_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        """
        **User Sign Up API**\n
        This API is used for user sign up process. User can sign up using email and password. OTP will be sent to the user's email address. User needs to verify the OTP to complete the sign up process.\n
        
        * Request Body:*
            - first_name: (string) First name of the user
            - last_name: (string) Last name of the user
            - email: (string) Email of the user
            - password: (string) Password of the user

        * Response:*
            - success: (boolean) True if signup successfull, False otherwise
            - message: (string) Message indicating the status of the signup process
            - user: (object) User object containing the details of the created user

        * Status Codes:*
            - 200: Signup successfull
            - 400: Bad request (e.g., missing fields, user already exists)
            - 500: Internal server error
        """
        try:
            first_name = request.data.get("first_name")
            last_name = request.data.get("last_name")
            email = request.data.get("email")
            password = request.data.get("password")

            if not first_name or not last_name or not email or not password:
                return Response({"success": False, "message": "All fields are required"}, status=status.HTTP_400_BAD_REQUEST)

            if User.objects.filter(email=email, is_active=True).exists():
                return Response({"success": False, "message": "User already exists"}, status=status.HTTP_400_BAD_REQUEST)
            
            if User.objects.filter(email=email, is_active=False).exists():
                user = User.objects.get(email=email, is_active=False)
                user.first_name = first_name
                user.last_name = last_name
                user.set_password(password)
                otp = random.randint(100000, 999999)
                user.otp = otp
                user.otp_created_at = timezone.now()
                user.status = 'inactive'
                user.save()
                send_activation_otp_email.delay(email, otp)
                serializer = UserSignUpSerializer(user)
                return Response({"success": True, "message": "Signup successfull! OTP sent to your email", "user": serializer.data}, status=status.HTTP_200_OK)
            
            otp = random.randint(100000, 999999)
            user = User.objects.create_user(email=email, password=password, first_name=first_name, last_name=last_name, is_active=False, status="inactive", otp=otp, otp_created_at=timezone.now())
            send_activation_otp_email.delay(email, otp)
            serializer = UserSignUpSerializer(user)
            return Response({"success": True, "message": "Signup successfull! OTP sent to your email", "user": serializer.data}, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

