from django.db import models
from activities.models import Activity
from django.core.validators import MinValueValidator


class SubActivity(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name='subactivities')
    target_date = models.DateTimeField()
    estimated_time = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    status_subactivity = models.IntegerField(default=0)  # 0: Active, #1:postalizes, 2: Completed
    notes = models.JSONField(blank=True, null=True)  # Store notes as a list of strings
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    deleted_at = models.DateTimeField(null=True, default=None)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'subactivities'