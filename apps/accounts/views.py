import uuid
import random
from datetime import timedelta
from core.base import NewAPIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils import timezone
from drf_yasg.utils import swagger_auto_schema
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from core.exceptions import _format_error_message
from accounts.serializers import (UserSignUpSerializer, EmailSerializer, EmailOTPSerializer, EmailPasswordSerializer, ResetPasswordSerializer, ChangePasswordSerializer, EmptySerializer, UpdateUserProfileSerializer, PlanSerializer, PlanFeatureSerializer)
from accounts.tasks import send_activation_otp_email, send_reset_otp_email
from rest_framework_simplejwt.tokens import RefreshToken
from accounts.models import Plan, PlanFeature

User = get_user_model()

class UserSignUpView(NewAPIView):
    serializer_class = UserSignUpSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

    @swagger_auto_schema(tags=["Authentication"])
    def post(self, request, *args, **kwargs):
        """
        **User Sign Up API - Public**\n
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
        **Resend Activation Email API - Public**\n
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
        **Verify Email Address (Activate Account) API - Public**\n
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
            user.last_login = timezone.now()
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
        **Login API - Public**\n
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
            user.last_login = timezone.now()
            user.save()
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

class ForgotPasswordAPIView(NewAPIView):
    serializer_class = EmailSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']
    
    @swagger_auto_schema(tags=['Authentication'])
    def post(self, request):
        """
        **Forgot Password - Public**\n
        Initiate forgot password process by sending a reset OTP to the user's email.
        
        **Request Body**\n
        - email: string (required, must be a valid email format)
        
        **Responses**\n
        - 200: Reset OTP sent successfully
        - 400: Bad request
        """
        try:
            email = request.data.get('email')
            if not email:
                return Response({
                    "success": False,
                    "message": "Email is required."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not User.objects.filter(email=email).exists():
                return Response({
                    "success": False,
                    "message": "User not found"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.get(email=email)
            if user.otp_created_at and (timezone.now() - user.otp_created_at) < timedelta(minutes=1):
                return Response({
                    "success": False,
                    "message": "An OTP has already been sent to your email, please try again in 1 minute."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            otp = str(random.randint(100000, 999999))
            reset_token = str(uuid.uuid4())
            user.otp = otp
            user.otp_created_at = timezone.now()
            user.forgot_password_token = reset_token
            user.save()
            
            send_reset_otp_email.delay(email, otp)
            
            return Response({
                "success": True,
                "message": "An OTP has been sent to your email! Please check your email to reset your password."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ForgotPasswordVerifyOTPAPIView(NewAPIView):
    serializer_class = EmailOTPSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']
    
    @swagger_auto_schema(tags=['Authentication'])
    def post(self, request):
        """
        **Forgot Password, Verify OTP - Public**\n
        Verify the OTP sent to the user's email for password reset.
        
        **Request Body**\n
        - email: string (required)
        - otp: string (required, 6-digit OTP)
        
        **Responses**\n
        - 200: OTP verified successfully, returns reset token
        - 400: Bad request
        """
        try:
            email = request.data.get('email')
            otp = request.data.get('otp')
            if not email or not otp:
                return Response({
                    "success": False,
                    "message": "All fields are required."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not User.objects.filter(email=email).exists():
                return Response({
                    "success": False,
                    "message": "User not found"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.get(email=email)
            if str(user.otp) != str(otp):
                return Response({
                    "success": False,
                    "message": "Invalid OTP"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not user.otp_created_at or (timezone.now() - user.otp_created_at) > timedelta(minutes=15):
                user.forgot_password_token = None
                user.otp = None
                user.otp_created_at = None
                user.save()
                return Response({
                    "success": False,
                    "message": "OTP has expired, please initiate the forgot password process again."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.otp = None
            user.otp_created_at = None
            user.save()
            return Response({
                "success": True,
                "message": "OTP verified successfully",
                "email": email,
                "reset_token": str(user.forgot_password_token)
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ResetPasswordAPIView(NewAPIView):
    serializer_class = ResetPasswordSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']
    
    @swagger_auto_schema(tags=['Authentication'])
    def post(self, request):
        """
        **Reset Password - Public**\n
        Reset the user's password using the reset token obtained after OTP verification.
        
        **Request Body**\n
        - email: string (required)
        - reset_token: string (required)
        - new_password: string (required)
        
        **Responses**\n
        - 200: Password reset successfully
        - 400: Bad request
        """
        try:
            email = request.data.get('email')
            reset_token = request.data.get('reset_token')
            new_password = request.data.get('new_password')
            if not all([email, reset_token, new_password]):
                return Response({
                    "success": False,
                    "message": "All fields are required."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            if not User.objects.filter(email=email).exists():
                return Response({
                    "success": False,
                    "message": "User not found"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = User.objects.get(email=email)
            if not user.forgot_password_token or str(user.forgot_password_token) != str(reset_token):
                return Response({
                    "success": False,
                    "message": "Invalid reset token"
                }, status=status.HTTP_400_BAD_REQUEST)
            
            try:
                validate_password(new_password, user=user)
            except Exception as e:
                return Response({
                    "success": False,
                    "message": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user.set_password(new_password)
            user.forgot_password_token = None
            user.otp = None
            user.otp_created_at = None
            user.save()
            return Response({
                "success": True,
                "message": "Password reset successfully"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class ChangePasswordAPIView(NewAPIView):
    serializer_class = ChangePasswordSerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['post']

    @swagger_auto_schema(tags=['Authentication'])
    def post(self, request):
        """
        **Change Password - Authenticated Users**\n
        Allows authenticated users to change their password by providing old and new passwords.

        **Request Body**\n
        - old_password: string (required)
        - new_password: string (required)

        **Responses**\n
        - 200: Password changed successfully
        - 400: Bad request
        - 401: Unauthorized
        """
        try:
            old_password = request.data.get('old_password')
            new_password = request.data.get('new_password')
            if not old_password or not new_password:
                return Response({
                    "success": False,
                    "message": "Both old_password and new_password are required."
                }, status=status.HTTP_400_BAD_REQUEST)

            user = request.user
            if not user.check_password(old_password):
                return Response({
                    "success": False,
                    "message": "Incorrect old password."
                }, status=status.HTTP_400_BAD_REQUEST)

            if old_password == new_password:
                return Response({
                    "success": False,
                    "message": "New password cannot be the same as old password."
                }, status=status.HTTP_400_BAD_REQUEST)

            try:
                validate_password(new_password, user=user)
            except Exception as e:
                return Response({
                    "success": False,
                    "message": str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

            user.set_password(new_password)
            user.save()
            return Response({
                "success": True,
                "message": "Password changed successfully."
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class UserProfileAPIView(NewAPIView):
    serializer_class = UpdateUserProfileSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    http_method_names = ['get', 'put']

    @swagger_auto_schema(tags=['Authentication'])
    def get(self, request):
        """
        **User Profile - Authenticated Users**\n
        Retrieves the profile information for the authenticated user.

        **Responses**\n
        - 200: Profile information retrieved successfully
        - 401: Unauthorized

        **Example Response**\n
        ```json
        {
            "success": true,
            "data": {
                "id": 1,
                "first_name": "Juraj",
                "last_name": "Sinanovic",
                "email": "[EMAIL_ADDRESS]",
                "profile_picture": null,
                "is_active": true,
                "status": "active",
                "plan": null,
                "plan_start_date": null,
                "plan_end_date": null,
                "date_joined": "2026-09-06T04:22:08.448156Z",
                "last_login": "2026-09-06T06:31:31.514545Z",
                "is_staff": false,
                "is_superuser": false,
                "created_at": "2026-09-06T04:22:08.754765Z",
                "updated_at": "2026-09-06T06:31:31.514682Z"
            }
        }
        ```

        * Status Codes:*
            - 200: Profile information retrieved successfully
            - 401: Unauthorized
            - 500: Internal server error
        """
        try:
            user = request.user
            profile_data = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'profile_picture': request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None,
                'is_active': user.is_active,
                'status': user.status,
                'plan': user.plan,
                'plan_start_date': user.plan_start_date,
                'plan_end_date': user.plan_end_date,
                'date_joined': user.date_joined,
                'last_login': user.last_login,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
            }
            return Response({
                "success": True,
                "data": profile_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(
        tags=['Authentication'],
        request_body=UpdateUserProfileSerializer,
        responses={
            200: "Profile updated successfully",
            400: "Bad request",
            401: "Unauthorized",
            500: "Internal server error"
        }
    )
    def put(self, request, *args, **kwargs):
        """
        **Update User Profile - Authenticated Users**\n
        Updates first_name, last_name, and/or profile_picture for the authenticated user.

        **Request Body (multipart/form-data)**\n
        ```
        {
            "first_name": "Juraj",
            "last_name": "Sinanovic",
            "profile_picture": "<profile_picture>"
        }
        ```

        **Example Response**\n
        ```json
        {
            "success": true,
            "message": "Profile updated successfully",
            "data": {
                "id": 1,
                "first_name": "Juraj",
                "last_name": "Sinanovic",
                "email": "[EMAIL_ADDRESS]",
                "profile_picture": null,
                "is_active": true,
                "status": "active",
                "plan": null,
                "plan_start_date": null,
                "plan_end_date": null,
                "date_joined": "2026-09-06T04:22:08.448156Z",
                "last_login": "2026-09-06T06:31:31.514545Z",
                "is_staff": false,
                "is_superuser": false,
                "created_at": "2026-09-06T04:22:08.754765Z",
                "updated_at": "2026-09-06T06:31:31.514682Z"
            }
        }
        ```

        * Status Codes:*    
            - 200: Profile updated successfully
            - 400: Bad request
            - 401: Unauthorized
            - 500: Internal server error
        """
        try:
            user = request.user
            serializer = UpdateUserProfileSerializer(user, data=request.data, partial=True)
            if not serializer.is_valid():
                return Response({
                    "success": False,
                    "message": _format_error_message(serializer.errors)
                }, status=status.HTTP_400_BAD_REQUEST)

            serializer.save()

            profile_data = {
                'id': user.id,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': user.email,
                'profile_picture': request.build_absolute_uri(user.profile_picture.url) if user.profile_picture else None,
                'is_active': user.is_active,
                'status': user.status,
                'plan': user.plan,
                'plan_start_date': user.plan_start_date,
                'plan_end_date': user.plan_end_date,
                'date_joined': user.date_joined,
                'last_login': user.last_login,
                'is_staff': user.is_staff,
                'is_superuser': user.is_superuser,
                'created_at': user.created_at,
                'updated_at': user.updated_at,
            }
            return Response({
                "success": True,
                "message": "Profile updated successfully",
                "data": profile_data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class DeleteUserAccountAPIView(NewAPIView):
    serializer_class = EmptySerializer
    permission_classes = [IsAuthenticated]
    http_method_names = ['delete']

    @swagger_auto_schema(tags=['Authentication'])
    def delete(self, request):
        """
        **Delete User Account - Authenticated Users**\n
        Deletes the account of the authenticated user.

        **Responses**\n
        - 204: Account deleted successfully
        - 400: Bad request
        - 401: Unauthorized
        - 500: Internal server error
        """
        try:
            user = request.user
            if request.user.is_superuser:
                return Response({
                    "success": False,
                    "message": "Superuser account cannot be deleted."
                }, status=status.HTTP_400_BAD_REQUEST)
            user.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class PlanListCreateAPIView(NewAPIView):
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'post']

    @swagger_auto_schema(tags=["Subscription Plan"])
    def get(self, request):
        """
        **Plan List API - Public**\n
        This API is used for getting list of plans.\n
        * Response:*
            - success: (boolean) True if list retrieval successfull, False otherwise
            - message: (string) Message indicating the status of the list retrieval process
            - data: (object) List of plans
        """
        try:
            plans = Plan.objects.filter(active=True).order_by('order')
            serializer = PlanSerializer(plans, many=True)
            return Response({
                "success": True,
                "message": "Plans retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @swagger_auto_schema(tags=["Subscription Plan"])
    def post(self, request):
        """
        **Plan Create API - Admin Only**\n
        This API is used for creating a new plan.\n
        * Request Body:*
            - name: (string) Name of the plan
            - billing_period: (string) Billing period of the plan
            - price: (float) Price of the plan
            - duration: (integer) Duration of the plan
            - active: (boolean) Whether the plan is active
            - discount_note: (string) Discount note of the plan
            - order: (integer) Order of the plan
            - features: (list) List of features. Each feature is an object with a 'feature' field.
                - feature: (string) Name of the feature.
        
        * Response:*
            - success: (boolean) True if plan creation successfull, False otherwise
            - message: (string) Message indicating the status of the plan creation process
            - data: (object) Created plan
        
        **Example Request**\n
        ```json
        {
            "name": "Trial",
            "billing_period": "trial",
            "price": 0,
            "duration": 7,
            "active": true,
            "discount_note": "Free Trial",
            "order": 1,
            "features": [
                {
                    "feature": "Full 24-question constitution assessment"
                },
                {
                    "feature": "Personalized organ & element insights"
                },
                {
                    "feature": "Saved assessment history & trends"
                },
                {
                    "feature": "Complete video library (Tai Chi, Qigong, etc)"
                },
                {
                    "feature": "Seasonal herbal & lifestyle plans"
                }
            ]
        }
        ```

        **Example Response**\n
        ```json
        {
            "success": true,
            "message": "Plan created successfully",
            "data": {
                "id": 1,
                "name": "Trial",
                "billing_period": "trial",
                "price": 0,
                "duration": 7,
                "active": true,
                "discount_note": "Free Trial",
                "order": 1,
                "features": [
                    {
                        "id": 1,
                        "feature": "Full 24-question constitution assessment"
                    },
                    {
                        "id": 2,
                        "feature": "Personalized organ & element insights"
                    },
                    {
                        "id": 3,
                        "feature": "Saved assessment history & trends"
                    },
                    {
                        "id": 4,
                        "feature": "Complete video library (Tai Chi, Qigong, etc)"
                    },
                    {
                        "id": 5,
                        "feature": "Seasonal herbal & lifestyle plans"
                    }
                ]
            }
        }
        ```

        **Error Responses**\n
        - 403: You are not authorized to create a plan.
        - 500: Internal server error
        """
        if not request.user.is_authenticated or not request.user.is_superuser:
            return Response({
                "success": False,
                "message": "You are not authorized to create a plan."
            }, status=status.HTTP_403_FORBIDDEN)
        try:
            serializer = PlanSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                "success": True,
                "message": "Plan created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class PlanDetailUpdateDeleteAPIView(NewAPIView):
    serializer_class = PlanSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'put', 'delete']

    @swagger_auto_schema(tags=["Subscription Plan"])
    def get(self, request, plan_id):
        """
        **Plan Detail API - Public**\n
        This API is used for getting details of a specific plan.\n
        * Response:*
            - success: (boolean) True if plan detail retrieval successfull, False otherwise
            - message: (string) Message indicating the status of the plan detail retrieval process
            - data: (object) Plan details
        
        **Example Response**\n
        ```json
        {
            "success": true,
            "message": "Plan details retrieved successfully",
            "data": {
                "id": 1,
                "name": "Trial",
                "billing_period": "trial",
                "price": 0,
                "duration": 7,
                "active": true,
                "discount_note": "Free Trial",
                "order": 1,
                "features": [
                    {
                        "id": 1,
                        "feature": "Full 24-question constitution assessment"
                    },
                    {
                        "id": 2,
                        "feature": "Personalized organ & element insights"
                    },
                    {
                        "id": 3,
                        "feature": "Saved assessment history & trends"
                    },
                    {
                        "id": 4,
                        "feature": "Complete video library (Tai Chi, Qigong, etc)"
                    },
                    {
                        "id": 5,
                        "feature": "Seasonal herbal & lifestyle plans"
                    }
                ]
            }
        }
        ```

        **Error Responses**\n
        - 500: Internal server error
        """
        try:
            plan = Plan.objects.get(pk=plan_id)
            serializer = PlanSerializer(plan)
            return Response({
                "success": True,
                "message": "Plan details retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Plan.DoesNotExist:
            return Response({
                "success": False,
                "message": "Plan not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["Subscription Plan"])
    def put(self, request, plan_id):
        """
        **Plan Update API - Admin Only**\n
        This API is used for updating a plan.\n
        * Request Body:*
            - name: (string) Name of the plan
            - billing_period: (string) Billing period of the plan
            - price: (float) Price of the plan
            - duration: (integer) Duration of the plan
            - active: (boolean) Whether the plan is active
            - discount_note: (string) Discount note of the plan
            - order: (integer) Order of the plan
            - features: (list) List of features. Each feature is an object with a 'feature' field.
                - feature: (string) Name of the feature.
        
        * Response:*
            - success: (boolean) True if plan update successfull, False otherwise
            - message: (string) Message indicating the status of the plan update process
            - data: (object) Updated plan
        
        **Example Request**\n
        ```json
        {
            "name": "Trial",
            "billing_period": "trial",
            "price": 0,
            "duration": 7,
            "active": true,
            "discount_note": "Free Trial",
            "order": 1,
            "features": [
                {
                    "feature": "Full 24-question constitution assessment"
                },
                {
                    "feature": "Personalized organ & element insights"
                },
                {
                    "feature": "Saved assessment history & trends"
                },
                {
                    "feature": "Complete video library (Tai Chi, Qigong, etc)"
                },
                {
                    "feature": "Seasonal herbal & lifestyle plans"
                }
            ]
        }
        ```

        **Example Response**\n
        ```json
        {
            "success": true,
            "message": "Plan updated successfully",
            "data": {
                "id": 1,
                "name": "Trial",
                "billing_period": "trial",
                "price": 0,
                "duration": 7,
                "active": true,
                "discount_note": "Free Trial",
                "order": 1,
                "features": [
                    {
                        "id": 1,
                        "feature": "Full 24-question constitution assessment"
                    },
                    {
                        "id": 2,
                        "feature": "Personalized organ & element insights"
                    },
                    {
                        "id": 3,
                        "feature": "Saved assessment history & trends"
                    },
                    {
                        "id": 4,
                        "feature": "Complete video library (Tai Chi, Qigong, etc)"
                    },
                    {
                        "id": 5,
                        "feature": "Seasonal herbal & lifestyle plans"
                    }
                ]
            }
        }
        ```

        **Error Responses**\n
        - 403: You are not authorized to update this plan.
        - 500: Internal server error
        """
        if not request.user.is_authenticated or not request.user.is_superuser:
            return Response({
                "success": False,
                "message": "You are not authorized to update this plan."
            }, status=status.HTTP_403_FORBIDDEN)
        try:
            plan = Plan.objects.get(pk=plan_id)
            serializer = PlanSerializer(plan, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                "success": True,
                "message": "Plan updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=["Subscription Plan"])
    def delete(self, request, plan_id):
        """
        **Plan Delete API - Admin Only**\n
        This API is used for deleting a plan.\n
        * Response:*
            - success: (boolean) True if plan deletion successfull, False otherwise
            - message: (string) Message indicating the status of the plan deletion process
        
        **Example Response**\n
        ```json
        {
            "success": true,
            "message": "Plan deleted successfully"
        }
        ```

        **Error Responses**\n
        - 403: You are not authorized to delete this plan.
        - 500: Internal server error
        """
        if not request.user.is_authenticated or not request.user.is_superuser:
            return Response({
                "success": False,
                "message": "You are not authorized to delete this plan."
            }, status=status.HTTP_403_FORBIDDEN)
        try:
            plan = Plan.objects.get(pk=plan_id)
            plan.delete()
            return Response({
                "success": True,
                "message": "Plan deleted successfully"
            }, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class PlanFeatureCreateAPIView(NewAPIView):
    serializer_class = PlanFeatureSerializer
    permission_classes = [AllowAny]
    http_method_names = ['post']

    @swagger_auto_schema(tags=['Subscription Plan'])
    def post(self, request, *args, **kwargs):
        """
        **Plan Feature Create API - Admin Only**\n
        This API is used for creating a plan feature.\n
        * Request Body:*
            - plan: (integer) ID of the plan
            - feature: (string) Name of the feature
        
        * Response:*
            - success: (boolean) True if plan feature creation successfull, False otherwise
            - message: (string) Message indicating the status of the plan feature creation process
            - data: (object) Created plan feature
        
        **Example Request**\n
        ```json
        {
            "plan": 1,
            "feature": "Full 24-question constitution assessment"
        }
        ```

        **Example Response**\n
        ```json
        {
            "success": true,
            "message": "Plan feature created successfully",
            "data": {
                "id": 1,
                "plan": 1,
                "feature": "Full 24-question constitution assessment"
            }
        }
        ```

        **Error Responses**\n
        - 403: You are not authorized to create this plan feature.
        - 400: Invalid request data
        - 500: Internal server error
        """
        if not request.user.is_authenticated or not request.user.is_superuser:
            return Response({
                "success": False,
                "message": "You are not authorized to create this plan feature."
            }, status=status.HTTP_403_FORBIDDEN)
        try:
            serializer = PlanFeatureSerializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                "success": True,
                "message": "Plan feature created successfully",
                "data": serializer.data
            }, status=status.HTTP_201_CREATED)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

class PlanFeatureDetailUpdateDeleteAPIView(NewAPIView):
    serializer_class = PlanFeatureSerializer
    permission_classes = [AllowAny]
    http_method_names = ['get', 'put', 'delete']

    @swagger_auto_schema(tags=['Subscription Plan'])
    def get(self, request, feature_id):
        """
        **Plan Feature Detail API - Public**\n
        This API is used for getting details of a specific plan feature.\n
        * Response:*
            - success: (boolean) True if plan feature detail retrieval successfull, False otherwise
            - message: (string) Message indicating the status of the plan feature detail retrieval process
            - data: (object) Plan feature details
        
        **Example Response**\n
        ```json
        {
            "success": true,
            "message": "Plan feature details retrieved successfully",
            "data": {
                "id": 1,
                "plan": 1,
                "feature": "Full 24-question constitution assessment"
            }
        }
        ```

        **Error Responses**\n
        - 404: Plan feature not found
        - 500: Internal server error
        """
        try:
            feature = PlanFeature.objects.get(pk=feature_id)
            serializer = PlanFeatureSerializer(feature)
            return Response({
                "success": True,
                "message": "Plan feature details retrieved successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except PlanFeature.DoesNotExist:
            return Response({
                "success": False,
                "message": "Plan feature not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Subscription Plan'])
    def put(self, request, feature_id):
        """
        **Plan Feature Update API - Admin Only**\n
        This API is used for updating a plan feature.\n
        * Request Body:*
            - plan: (integer, optional) ID of the plan
            - feature: (string, optional) Name of the feature
        
        * Response:*
            - success: (boolean) True if plan feature update successfull, False otherwise
            - message: (string) Message indicating the status of the plan feature update process
            - data: (object) Updated plan feature
        
        **Example Request**\n
        ```json
        {
            "plan": 1,
            "feature": "Full 24-question constitution assessment"
        }
        ```

        **Example Response**\n
        ```json
        {
            "success": true,
            "message": "Plan feature updated successfully",
            "data": {
                "id": 1,
                "plan": 1,
                "feature": "Full 24-question constitution assessment"
            }
        }
        ```

        **Error Responses**\n
        - 403: You are not authorized to update this plan feature.
        - 404: Plan feature not found
        - 500: Internal server error
        """
        if not request.user.is_authenticated or not request.user.is_superuser:
            return Response({
                "success": False,
                "message": "You are not authorized to update this plan feature."
            }, status=status.HTTP_403_FORBIDDEN)
        try:
            feature = PlanFeature.objects.get(pk=feature_id)
            serializer = PlanFeatureSerializer(feature, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({
                "success": True,
                "message": "Plan feature updated successfully",
                "data": serializer.data
            }, status=status.HTTP_200_OK)
        except PlanFeature.DoesNotExist:
            return Response({
                "success": False,
                "message": "Plan feature not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    @swagger_auto_schema(tags=['Subscription Plan'])
    def delete(self, request, feature_id):
        """
        **Plan Feature Delete API - Admin Only**\n
        This API is used for deleting a plan feature.\n
        * Response:*
            - success: (boolean) True if plan feature deletion successfull, False otherwise
            - message: (string) Message indicating the status of the plan feature deletion process
        
        **Example Response**\n
        ```json
        {
            "success": true,
            "message": "Plan feature deleted successfully"
        }
        ```

        **Error Responses**\n
        - 403: You are not authorized to delete this plan feature.
        - 404: Plan feature not found
        - 500: Internal server error
        """
        if not request.user.is_authenticated or not request.user.is_superuser:
            return Response({
                "success": False,
                "message": "You are not authorized to delete this plan feature."
            }, status=status.HTTP_403_FORBIDDEN)
        try:
            feature = PlanFeature.objects.get(pk=feature_id)
            feature.delete()
            return Response({
                "success": True,
                "message": "Plan feature deleted successfully"
            }, status=status.HTTP_200_OK)
        except PlanFeature.DoesNotExist:
            return Response({
                "success": False,
                "message": "Plan feature not found"
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "success": False,
                "message": str(e)
            }, status=status.HTTP_400_BAD_REQUEST)


