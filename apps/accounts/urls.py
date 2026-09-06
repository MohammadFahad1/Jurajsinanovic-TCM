from django.urls import path
from accounts import views

urlpatterns = [
    path('signup/', views.UserSignUpView.as_view(), name='signup'),
    path('resend-otp/activation/', views.ResendActivationEmailAPIView.as_view(), name='resend-otp-activation'),
    path('verify-email/', views.VerifyEmailAddressAPIView.as_view(), name='verify-email'),
]
