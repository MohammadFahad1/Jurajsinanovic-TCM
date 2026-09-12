from django.urls import path
from health_check.views import QuestionListCreateView, QuestionDetailAPIView

urlpatterns = [
    path('', QuestionListCreateView.as_view(), name='questions_list_create'),
    path('<int:question_id>/', QuestionDetailAPIView.as_view(), name='question_detail'),
]
