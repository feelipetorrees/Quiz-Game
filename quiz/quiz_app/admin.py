from django.contrib import admin
from .models import Quiz, Player, Question, Answer

@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ['code', 'title', 'created_at', 'is_active']
    search_fields = ['code', 'title']

@admin.register(Player)
class PlayerAdmin(admin.ModelAdmin):
    list_display = ['username', 'quiz', 'score', 'is_online', 'joined_at']
    list_filter = ['quiz', 'is_online']

@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['text', 'quiz', 'order', 'time_limit']
    list_filter = ['quiz']

@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ['text', 'question', 'is_correct']
    list_filter = ['question', 'is_correct']