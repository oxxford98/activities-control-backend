from django.db.models import Count, Q
from drf_yasg.utils import swagger_auto_schema
from rest_framework.exceptions import ValidationError

from activities.api.serializer import ActivitySerializer
from activities.models import Activity
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from subactivities.models import SubActivity
from subactivities.api.serializer import SubActivitySerializer
from activities.api.swagger import sub_activities_today_decorator
from django.db import transaction


class ActivityApiViewSet(ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = ActivitySerializer
    queryset = Activity.objects.filter(deleted_at__isnull=True)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        subactivities_data = request.data.pop('subactivities', [])
        request.data['user'] = request.user.id

        activity_serializer = ActivitySerializer(data=request.data)
        activity_serializer.is_valid(raise_exception=True)
        activity = activity_serializer.save()

        for i, sub_data in enumerate(subactivities_data):
            sub_data['activity'] = activity.id
            sub_serializer = SubActivitySerializer(data=sub_data)
            if not sub_serializer.is_valid():
                raise ValidationError({f'subactivities[{i}]': sub_serializer.errors})
            sub_serializer.save()

        return Response(activity_serializer.data, status=201)

    def retrieve(self, request, *args, **kwargs):
        activity = self.get_object()

        counts = SubActivity.objects.filter(
            activity=activity,
            deleted_at__isnull=True
        ).aggregate(
            total_subactivities=Count('id'),
            total_completed=Count('id', filter=Q(status_subactivity=2))
        )

        data = self.get_serializer(activity).data
        data.update(counts)

        return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def activities_by_user(request):
    user = request.user
    activities = Activity.objects.filter(user=user, deleted_at__isnull=True)
    serializer = ActivitySerializer(activities, many=True)
    return Response(serializer.data)


@sub_activities_today_decorator
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sub_activities_for_today(request):
    user = request.user

    now = timezone.localtime(timezone.now())
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)

    # Filtros opcionales 
    qs = (
        SubActivity.objects
        .filter(
            activity__user=user,
            deleted_at__isnull=True,
        )
        .select_related('activity')
    )

    status_subactivity = request.query_params.get('status_subactivity')
    if status_subactivity is not None:
        try:
            qs = qs.filter(status_subactivity=int(status_subactivity))
        except ValueError:
            return Response({'detail': 'status_subactivity debe ser un entero.'}, status=400)

    estimated_time = request.query_params.get('estimated_time')
    if estimated_time is not None:
        try:
            qs = qs.filter(estimated_time=int(estimated_time))
        except ValueError:
            return Response({'detail': 'estimated_time debe ser un entero.'}, status=400)

    type_activity = request.query_params.get('type_activity')
    if type_activity:
        qs = qs.filter(activity__type_activity=type_activity)

    subject = request.query_params.get('subject')
    if subject:
        qs = qs.filter(activity__subject__icontains=subject)

    # clasificar
    expired  = []
    today    = []
    upcoming = []

    for sub in qs:
        target = timezone.localtime(sub.target_date)

        if target < now:
            sub._status = 'expired'
            expired.append(sub)
        elif target.date() == now.date():
            sub._status = 'today'
            today.append(sub)
        else:
            sub._status = 'upcoming'
            upcoming.append(sub)

    # Ordenar: (target_date ASC, estimated_time ASC) 
    sort_key = lambda s: (s.target_date, s.estimated_time)
    expired.sort(key=sort_key)
    today.sort(key=sort_key)
    upcoming.sort(key=sort_key)

    return Response({
        'now':      now.isoformat(),
        'expired':  build(expired),
        'today':    build(today),
        'upcoming': build(upcoming),
    })



def build(items):
    result = []
    for sub in items:
        data = SubActivitySerializer(sub).data
        data['status_expired'] = sub._status
        data['activity_name']  = sub.activity.title
        data['type_activity']  = sub.activity.type_activity
        data['subject'] = sub.activity.subject
        result.append(data)
    return result
    