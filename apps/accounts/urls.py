from django.urls import path
from accounts import views

urlpatterns = [
    path('signup/', views.UserSignUpView.as_view(), name='signup'),
    path('resend-otp/activation/', views.ResendActivationEmail.as_view(), name='resend-otp-activation'),
]
