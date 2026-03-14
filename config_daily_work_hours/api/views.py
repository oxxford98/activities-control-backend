from django.db.models import Sum
from django.utils.timezone import now
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from config_daily_work_hours.api.serializer import ConfigDailyWorkHoursSerializer
from config_daily_work_hours.models import ConfigDailyWorkHours
from subactivities.models import SubActivity


class ConfigDailyWorkHoursApiViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ConfigDailyWorkHoursSerializer
    queryset = ConfigDailyWorkHours.objects.filter(deleted_at__isnull=True)

    def create(self, request, *args, **kwargs):
        user = request.user
        instance = ConfigDailyWorkHours.objects.filter(user=user, deleted_at__isnull=True).first()
        if instance:
            serializer = ConfigDailyWorkHoursSerializer(instance, data=request.data, partial=True)
        else:
            request.data['user'] = user.id
            serializer = ConfigDailyWorkHoursSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=201)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def config_daily_work_hours_by_user(request):
    user = request.user
    today = now().date()
    print(today)

    config_daily_work_hours = ConfigDailyWorkHours.objects.filter(user=user, deleted_at__isnull=True)

    busy_hours = SubActivity.objects.filter(
        activity__user=user,
        activity__deleted_at__isnull=True,
        target_date__date=today,
        deleted_at__isnull=True
    ).aggregate(total=Sum('estimated_time'))['total'] or 0

    serializer = ConfigDailyWorkHoursSerializer(config_daily_work_hours, many=True)
    response_data = serializer.data

    for idx, config in enumerate(config_daily_work_hours):
        available_hours = max(config.estimated_hours - busy_hours, 0)
        response_data[idx]['busy_hours'] = busy_hours
        response_data[idx]['available_hours'] = available_hours

    return Response(response_data)