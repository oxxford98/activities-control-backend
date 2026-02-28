from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from subactivities.api.serializer import SubActivitySerializer
from subactivities.models import SubActivity


class SubActivityApiViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = SubActivitySerializer
    queryset = SubActivity.objects.filter(deleted_at__isnull=True)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sub_activities_by_activities(request, activity_id):
    sub_activities = SubActivity.objects.filter(activity=activity_id, deleted_at__isnull=True)
    serializer = SubActivitySerializer(sub_activities, many=True)
    return Response(serializer.data)