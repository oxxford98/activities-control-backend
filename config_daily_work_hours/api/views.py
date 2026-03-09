from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from config_daily_work_hours.api.serializer import ConfigDailyWorkHoursSerializer
from config_daily_work_hours.models import ConfigDailyWorkHours


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
    config_daily_work_hours = ConfigDailyWorkHours.objects.filter(user=user, deleted_at__isnull=True)
    serializer = ConfigDailyWorkHoursSerializer(config_daily_work_hours, many=True)
    return Response(serializer.data)