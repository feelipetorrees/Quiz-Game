from django.db import models
from django.contrib.auth.models import User

class Quiz(models.Model):
    code = models.CharField(max_length=10, unique=True)
    title = models.CharField(max_length=200, default="Quiz Sem Título")
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"{self.title} ({self.code})"

class Theme(models.Model):
    name = models.CharField(max_length=100, unique=True, verbose_name="Nome da Categoria/Tema")
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name

class QuizThemeSelection(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, 
                             related_name="Selected_themes_set", 
                             verbose_name="Quiz Pai")
    theme = models.ForeignKey(Theme, 
                              on_delete=models.CASCADE,
                              related_name="quiz_selections",
                              verbose_name="Tema Escolhido")

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
    category = models.ForeignKey(Theme, on_delete=models.CASCADE, related_name='questions')
    text = models.TextField()
    order = models.IntegerField(default=0)
    time_limit = models.IntegerField(default=30)  # segundos
    points = models.PositiveBigIntegerField(
        verbose_name="Pontuação",
        default=10
    )
    
    class Meta:
        unique_together = ('quiz', 'order')
        ordering = ['order']
    
    def __str__(self):
        return f"Pergunta {self.order}: {self.text[:50]}..."

class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name='answers')
    text = models.CharField(max_length=200)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.text} ({'✓' if self.is_correct else '✗'})"
    
class Option(models.Model):
    question = models.ForeignKey(Question, related_name='options', on_delete=models.CASCADE)
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)

    def __str__(self):
        return f"Opção para {self.question.id}: {self.text[:30]}"