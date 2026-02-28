from django.db import models
from users.models import User


class Activity(models.Model):

    class TypeActivity(models.TextChoices):
        EXAM = 'Examen', 'Examen'
        QUIZ = 'Quiz', 'Quiz'
        WORKSHOP = 'Taller', 'Taller'
        PROJECT = 'Proyecto', 'Proyecto'
        OTHER = 'Otro', 'Otro'

    title = models.CharField(max_length=255)
    type_activity = models.CharField(max_length=50,choices=TypeActivity.choices)
    description = models.TextField(blank=True, null=True)
    subject = models.CharField(max_length=255)
    event_date = models.DateTimeField(blank=True, null=True)
    deadline = models.DateTimeField(blank=True, null=True)
    grade = models.FloatField(blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activities')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, default=None)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'activities'