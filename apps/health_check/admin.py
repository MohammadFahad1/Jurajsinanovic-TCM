from django.contrib import admin
from health_check.models import Question, Answer, UserCheckIn, UserAnswer

admin.site.register(Question)
admin.site.register(Answer)
admin.site.register(UserCheckIn)
admin.site.register(UserAnswer)
