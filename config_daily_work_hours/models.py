from django.db import models
from django.core.validators import MinValueValidator
from users.models import User


class ConfigDailyWorkHours(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='config_daily_work_hours')
    estimated_hours = models.PositiveIntegerField(default=6, validators=[MinValueValidator(1)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, default=None)

    class Meta:
        db_table = 'config_daily_work_hours'