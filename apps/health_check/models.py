from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Question(models.Model):
    title = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    answer = models.CharField(max_length=500)
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.answer

    class Meta:
        verbose_name = 'Answer'
        verbose_name_plural = 'Answers'

class UserCheckIn(models.Model):
    INCOMPLETE = 'incomplete'
    COMPLETED = 'completed'
    
    STATUS_CHOICES = [
        (INCOMPLETE, 'Incomplete'),
        (COMPLETED, 'Completed'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='check_ins')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=INCOMPLETE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Check-in by {self.user} at {self.created_at}"

    def calculate_score(self):
        """Calculate total score from all answers in this check-in."""
        return self.answers.aggregate(models.Sum('answer__score'))['answer__score__sum'] or 0
    
    class Meta:
        verbose_name = 'User Check-in'
        verbose_name_plural = 'User Check-ins'

class UserAnswer(models.Model):
    check_in = models.ForeignKey(UserCheckIn, on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='user_answers')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name='user_answers')
    score = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Answer by {self.check_in.user} to {self.question} at {self.created_at}"

    class Meta:
        unique_together = ['check_in', 'question']
        verbose_name = 'User Answer'
        verbose_name_plural = 'User Answers'


