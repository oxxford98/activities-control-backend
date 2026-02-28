from activities.api.serializer import ActivitySerializer
from activities.models import Activity
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response


class ActivityApiViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ActivitySerializer
    queryset = Activity.objects.filter(deleted_at__isnull=True)

    def create(self, request, *args, **kwargs):
        request.data['user'] = request.user.id
        return super().create(request, *args, **kwargs)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def activities_by_user(request):
    user = request.user
    activities = Activity.objects.filter(user=user, deleted_at__isnull=True)
    serializer = ActivitySerializer(activities, many=True)
    return Response(serializer.data)