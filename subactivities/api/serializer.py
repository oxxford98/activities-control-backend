from django.utils import timezone
from rest_framework import serializers

from config_daily_work_hours.models import ConfigDailyWorkHours
from subactivities.models import SubActivity


class SubActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubActivity
        fields = '__all__'

    def validate(self, attrs):
        activity = attrs.get('activity', getattr(self.instance, 'activity', None))
        target_date = attrs.get('target_date', getattr(self.instance, 'target_date', None))
        estimated_time = attrs.get('estimated_time', getattr(self.instance, 'estimated_time', None))

        if activity is None or target_date is None or estimated_time is None:
            return attrs

        request = self.context.get('request')
        user = request.user if request and request.user.is_authenticated else activity.user

        if timezone.is_naive(target_date):
            target_date = timezone.make_aware(target_date, timezone.get_current_timezone())

        target_day = timezone.localtime(target_date).date()
        config = ConfigDailyWorkHours.objects.filter(
            user=user,
            deleted_at__isnull=True,
        ).order_by('-updated_at', '-created_at').first()
        daily_limit = config.estimated_hours if config else 6

        subactivities_for_day = SubActivity.objects.filter(
            activity__user=user,
            deleted_at__isnull=True,
            target_date__date=target_day,
        )

        if self.instance is not None:
            subactivities_for_day = subactivities_for_day.exclude(id=self.instance.id)

        current_load = sum(item.estimated_time for item in subactivities_for_day) + estimated_time

        if current_load > daily_limit:
            raise serializers.ValidationError(
                {
                    'estimated_time': 'Daily work hour limit exceeded for target_date.',
                    'current_load': current_load,
                    'limit': daily_limit,
                }
            )

        return attrs


class ValidateSubactivityTentativeDateSerializer(serializers.Serializer):
    subactivity = serializers.IntegerField(required=True)
    tentative_date = serializers.DateTimeField(required=True)