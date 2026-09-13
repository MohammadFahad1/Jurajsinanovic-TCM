from django.urls import path
from health_check.views import (
    QuestionListCreateView,
    QuestionDetailAPIView,
    AnswerListCreateAPIView,
    AnswerDetailAPIView,
    UserCheckInListCreateAPIView,
)

urlpatterns = [
    # Question and Answer Management
    path('', QuestionListCreateView.as_view(), name='questions_list_create'),
    path('<int:question_id>/', QuestionDetailAPIView.as_view(), name='question_detail'),
    path('<int:question_id>/answers/', AnswerListCreateAPIView.as_view(), name='answer_list_create'),
    path('answers/<int:answer_id>/', AnswerDetailAPIView.as_view(), name='answer_detail'),

    # User Check-in Management
    path('check-in/', UserCheckInListCreateAPIView.as_view(), name='user_check_in_list_create'),
]
