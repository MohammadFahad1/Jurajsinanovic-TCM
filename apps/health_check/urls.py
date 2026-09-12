from django.urls import path
from health_check.views import (
    QuestionListCreateView,
    QuestionDetailAPIView,
    AnswerListCreateAPIView,
    AnswerDetailAPIView,
)

urlpatterns = [
    path('', QuestionListCreateView.as_view(), name='questions_list_create'),
    path('<int:question_id>/', QuestionDetailAPIView.as_view(), name='question_detail'),
    path('<int:question_id>/answers/', AnswerListCreateAPIView.as_view(), name='answer_list_create'),
    path('answers/<int:answer_id>/', AnswerDetailAPIView.as_view(), name='answer_detail'),
]
