import random
from core.base import NewAPIView
from rest_framework.response import Response
from rest_framework import status
from accounts.serializers import UserSignUpSerializer, EmailSerializer, EmailOTPSerializer, EmailPasswordSerializer
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model
from drf_yasg.utils import swagger_auto_schema
from django.utils import timezone
from accounts.tasks import send_activation_otp_email
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken
from rest_framework_simplejwt.tokens import RefreshToken
from datetime import timedelta

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

class ResendActivationEmailAPIView(NewAPIView):
    serializer_class = EmailSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

    @swagger_auto_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        """
        **Resend Activation Email API**\n
        This API is used for resending activation email to the user.\n

        * Request Body:*
            - email: (string) Email of the user\n

        * Response:*
            - success: (boolean) True if resend successfull, False otherwise
            - message: (string) Message indicating the status of the resend process\n

        * Status Codes:*
            - 200: Resend successfull
            - 400: Bad request (e.g., missing fields, user does not exist)
            - 500: Internal server error
        """
        try:
            email = request.data.get("email")
            if not email:
                return Response({"success": False, "message": "Email is required"}, status=status.HTTP_400_BAD_REQUEST)
            if not User.objects.filter(email=email).exists():
                return Response({"success": False, "message": "User does not exist"}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.get(email=email)
            if user.is_active:
                return Response({"success": False, "message": "User is already activated"}, status=status.HTTP_400_BAD_REQUEST)
            otp = random.randint(100000, 999999)
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.save()
            send_activation_otp_email.delay(email, otp)
            return Response({"success": True, "message": "Activation email sent successfully"}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class VerifyEmailAddressAPIView(NewAPIView):
    serializer_class = EmailOTPSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

    @swagger_auto_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        """
        **Verify Email Address (Activate Account) API**\n
        This API is used for verifying email address of the user.\n

        * Request Body:*
            - email: (string) Email of the user
            - otp: (string) OTP sent to the user's email address\n

        * Response:*
            - success: (boolean) True if verification successfull, False otherwise
            - message: (string) Message indicating the status of the verification process
            - access: (string) Access token
            - refresh: (string) Refresh token
            - user: (object) User object containing the details of the created user\n

        **Example Response**\n
        ```json
        {
            "success": true,
            "message": "Email verification successfull",
            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "user": {
                "id": 1,
                "email": "[EMAIL_ADDRESS]",
                "first_name": "John",
                "last_name": "Doe",
                "profile_picture": null,
                "role": "patient"
            }
        }
        ```

        * Status Codes:*
            - 200: Verification successfull
            - 400: Bad request (e.g., missing fields, user does not exist)
            - 500: Internal server error
        """
        try:
            email = request.data.get("email")
            otp = request.data.get("otp")
            if not email or not otp:
                return Response({"success": False, "message": "Fields are required."}, status=status.HTTP_400_BAD_REQUEST)
            if not User.objects.filter(email=email).exists():
                return Response({"success": False, "message": "User does not exist"}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.get(email=email)
            if user.is_active:
                return Response({"success": False, "message": "User is already activated"}, status=status.HTTP_400_BAD_REQUEST)
            if str(user.otp) != str(otp):
                return Response({"success": False, "message": "Invalid OTP"}, status=status.HTTP_400_BAD_REQUEST)
            if not user.otp_created_at or (timezone.now() - user.otp_created_at) > timedelta(minutes=15):
                return Response({"success": False, "message": "OTP is expired. Please request a new one."}, status=status.HTTP_400_BAD_REQUEST)
            user.is_active = True
            user.status = 'active'
            user.otp = None
            user.otp_created_at = None
            user.save()
            
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            return Response({
                "success": True, 
                "message": "Email verification successfull", 
                "access": str(access), 
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "profile_picture": request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None,
                    "role": 'patient' if not user.is_superuser else 'admin',
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class LoginAPIView(NewAPIView):
    serializer_class = EmailPasswordSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

    @swagger_auto_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        """
        **Login API**\n
        This API is used for logging in the user.\n

        * Request Body:*
            - email: (string) Email of the user
            - password: (string) Password of the user\n

        * Response:*
            - success: (boolean) True if login successfull, False otherwise
            - message: (string) Message indicating the status of the login process
            - access: (string) Access token
            - refresh: (string) Refresh token
            - user: (object) User object containing the details of the logged in user\n

        **Example Response**\n
        ```json
        {
            "success": true,
            "message": "Login successfull",
            "access": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "refresh": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            "user": {
                "id": 1,
                "email": "[EMAIL_ADDRESS]",
                "first_name": "John",
                "last_name": "Doe",
                "profile_picture": null,
                "role": "patient"
            }
        }
        ```

        * Status Codes:*
            - 200: Login successfull
            - 400: Bad request (e.g., missing fields, user does not exist, invalid password, user is not activated)
            - 500: Internal server error
        """
        try:
            email = request.data.get("email")
            password = request.data.get("password")
            if not email or not password:
                return Response({"success": False, "message": "Fields are required."}, status=status.HTTP_400_BAD_REQUEST)
            if not User.objects.filter(email=email).exists():
                return Response({"success": False, "message": "User does not exist"}, status=status.HTTP_400_BAD_REQUEST)
            user = User.objects.get(email=email)
            if not user.check_password(password):
                return Response({"success": False, "message": "Invalid password"}, status=status.HTTP_400_BAD_REQUEST)
            if not user.is_active or not user.status == 'active':
                return Response({"success": False, "message": "User is not activated"}, status=status.HTTP_400_BAD_REQUEST)
            refresh = RefreshToken.for_user(user)
            access = refresh.access_token
            return Response({
                "success": True, 
                "message": "Login successfull", 
                "access": str(access), 
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "email": user.email,
                    "first_name": user.first_name,
                    "last_name": user.last_name,
                    "profile_picture": request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None,
                    "role": 'patient' if not user.is_superuser else 'admin',
                }
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({"success": False, "message": str(e)}, status=status.HTTP_400_BAD_REQUEST)

