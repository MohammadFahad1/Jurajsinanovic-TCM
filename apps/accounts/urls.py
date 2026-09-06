from django.urls import path
from accounts import views

urlpatterns = [
    path('signup/', views.UserSignUpView.as_view(), name='signup'),
]
