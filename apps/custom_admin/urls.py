from django.urls import path
from custom_admin.views import UserListAPIView

urlpatterns = [
    path('users/', UserListAPIView.as_view(), name='admin-user-list'),
]