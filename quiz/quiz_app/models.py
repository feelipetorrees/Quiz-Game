from django.db import models
from django.contrib.auth.models import User

class Quiz(models.Model):
    code = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=200, default="Quiz Sem Título")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} ({self.code})"

class Player(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='players')
    username = models.CharField(max_length=100)
    score = models.IntegerField(default=0)
    is_online = models.BooleanField(default=False)
    session_id = models.CharField(max_length=100, blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['quiz', 'username']
    
    def __str__(self):
        return f"{self.username} - {self.quiz.code}"

class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    order = models.IntegerField(default=0)
    time_limit = models.IntegerField(default=30)  # segundos
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Pergunta {self.order}: {self.text[:50]}..."

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.text} ({'✓' if self.is_correct else '✗'})"