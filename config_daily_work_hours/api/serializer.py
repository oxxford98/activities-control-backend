from rest_framework import serializers
from config_daily_work_hours.models import ConfigDailyWorkHours


class ConfigDailyWorkHoursSerializer(serializers.ModelSerializer):
    class Meta:
        model = ConfigDailyWorkHours
        fields = '__all__'