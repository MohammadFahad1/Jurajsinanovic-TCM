from django.urls import path
from accounts import views

urlpatterns = [
    path('signup/', views.UserSignUpView.as_view(), name='signup'),
    path('resend-otp/activation/', views.ResendActivationEmailAPIView.as_view(), name='resend-otp-activation'),
    path('verify-email/', views.VerifyEmailAddressAPIView.as_view(), name='verify-email'),
    path('login/', views.LoginAPIView.as_view(), name='login'),
    path('forgot-password/', views.ForgotPasswordAPIView.as_view(), name='forgot-password'),
    path('forgot-password/verify-otp/', views.ForgotPasswordVerifyOTPAPIView.as_view(), name='forgot-password-verify-otp'),
    path('reset-password/', views.ResetPasswordAPIView.as_view(), name='reset-password'),
    path('change-password/', views.ChangePasswordAPIView.as_view(), name='change-password'),
]
