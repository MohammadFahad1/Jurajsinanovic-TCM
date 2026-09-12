from django.urls import path
from health_check.views import QuestionListCreateView

urlpatterns = [
	path('', QuestionListCreateView.as_view(), name='questions_list_create'),
]
