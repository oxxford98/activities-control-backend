from datetime import timedelta
from datetime import datetime
from django.utils import timezone
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status

from activities.models import Activity
from config_daily_work_hours.models import ConfigDailyWorkHours
from subactivities.api.serializer import (
    SubActivitySerializer,
    ValidateSubactivityTentativeDateSerializer,
)
from subactivities.models import SubActivity
from django.db.models import Sum


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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_subactivity_tentative_date(request):
    payload_serializer = ValidateSubactivityTentativeDateSerializer(data=request.data)
    payload_serializer.is_valid(raise_exception=True)

    subactivity_id = payload_serializer.validated_data['subactivity']
    parsed_datetime = payload_serializer.validated_data['tentative_date']

    try:
        subactivity = SubActivity.objects.select_related('activity').get(
            id=subactivity_id,
            deleted_at__isnull=True,
        )
    except SubActivity.DoesNotExist:
        return Response({'detail': 'Subactivity not found.'}, status=status.HTTP_404_NOT_FOUND)

    if subactivity.activity.user_id != request.user.id:
        return Response({'detail': 'You do not have access to this subactivity.'}, status=status.HTTP_403_FORBIDDEN)

    if timezone.is_naive(parsed_datetime):
        parsed_datetime = timezone.make_aware(parsed_datetime, timezone.get_current_timezone())
    tentative_day = parsed_datetime.date()

    user_activity_ids = Activity.objects.filter(
        user=request.user,
        deleted_at__isnull=True,
    ).values_list('id', flat=True)

    config = ConfigDailyWorkHours.objects.filter(
        user=request.user,
        deleted_at__isnull=True,
    ).order_by('-updated_at', '-created_at').first()
    daily_limit = config.estimated_hours if config else 6

    subactivities_for_day = SubActivity.objects.filter(
        activity_id__in=user_activity_ids,
        deleted_at__isnull=True,
        target_date__date=tentative_day,
    ).exclude(id=subactivity.id)

    base_load = sum(item.estimated_time for item in subactivities_for_day)
    current_load = base_load + subactivity.estimated_time
    is_valid = current_load <= daily_limit

    if is_valid:
        return Response(
            {
                'valid': True,
                'current_load': current_load,
                'limit': daily_limit,
            },
            status=status.HTTP_200_OK,
        )

    suggestions = []

    def load_for_day(day):
        day_load = SubActivity.objects.filter(
            activity_id__in=user_activity_ids,
            deleted_at__isnull=True,
            target_date__date=day,
        ).exclude(id=subactivity.id)
        return sum(item.estimated_time for item in day_load)

    previous_candidate = tentative_day - timedelta(days=1)
    next_candidate = tentative_day + timedelta(days=1)
    max_search_days = 365

    for _ in range(max_search_days):
        if len(suggestions) == 2:
            break

        previous_load = load_for_day(previous_candidate)
        if previous_load + subactivity.estimated_time <= daily_limit:
            previous_dt = timezone.make_aware(
                timezone.datetime.combine(previous_candidate, parsed_datetime.timetz().replace(tzinfo=None)),
                timezone.get_current_timezone(),
            )
            suggestions.append(
                {
                    'tentative_date': previous_dt.isoformat(),
                    'current_load': previous_load + subactivity.estimated_time,
                }
            )

        if len(suggestions) == 2:
            break

        next_load = load_for_day(next_candidate)
        if next_load + subactivity.estimated_time <= daily_limit:
            next_dt = timezone.make_aware(
                timezone.datetime.combine(next_candidate, parsed_datetime.timetz().replace(tzinfo=None)),
                timezone.get_current_timezone(),
            )
            suggestions.append(
                {
                    'tentative_date': next_dt.isoformat(),
                    'current_load': next_load + subactivity.estimated_time,
                }
            )

        previous_candidate -= timedelta(days=1)
        next_candidate += timedelta(days=1)

    return Response(
        {
            'valid': False,
            'current_load': current_load,
            'limit': daily_limit,
            'suggestions': suggestions,
        },
        status=status.HTTP_409_CONFLICT,
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_subactivity_tentative_date_to_create_sub(request):
    tentative_date_raw = request.data.get('tentative_date')
    hours_estimated = request.data.get('hours_estimated')

    if not tentative_date_raw or hours_estimated is None:
        return Response(
            {'detail': 'tentative_date and hours_estimated are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        hours_estimated = float(hours_estimated)
    except (ValueError, TypeError):
        return Response({'detail': 'hours_estimated must be a valid number.'}, status=status.HTTP_400_BAD_REQUEST)

    try:
        parsed_datetime = datetime.fromisoformat(tentative_date_raw.replace('Z', '+00:00'))
    except (ValueError, AttributeError):
        return Response({'detail': 'Invalid tentative_date format.'}, status=status.HTTP_400_BAD_REQUEST)

    if timezone.is_naive(parsed_datetime):
        parsed_datetime = timezone.make_aware(parsed_datetime, timezone.get_current_timezone())
    tentative_day = parsed_datetime.date()

    user_activity_ids = Activity.objects.filter(
        user=request.user,
        deleted_at__isnull=True,
    ).values_list('id', flat=True)

    config = ConfigDailyWorkHours.objects.filter(
        user=request.user,
        deleted_at__isnull=True,
    ).order_by('-updated_at', '-created_at').first()
    daily_limit = config.estimated_hours if config else 6

    # Una sola query que trae la carga por día en el rango máximo de búsqueda
    max_search_days = 365
    range_start = tentative_day - timedelta(days=max_search_days)
    range_end = tentative_day + timedelta(days=max_search_days)

    loads_by_day = (
        SubActivity.objects
        .filter(
            activity_id__in=user_activity_ids,
            deleted_at__isnull=True,
            target_date__date__range=(range_start, range_end),
        )
        .values('target_date__date')
        .annotate(total=Sum('estimated_time'))
    )

    # Convertir a dict {date: total_load}
    load_map = {entry['target_date__date']: entry['total'] for entry in loads_by_day}

    def load_for_day(day):
        return load_map.get(day, 0)

    current_load = load_for_day(tentative_day) + hours_estimated
    is_valid = current_load <= daily_limit

    if is_valid:
        return Response(
            {
                'valid': True,
                'current_load': current_load,
                'limit': daily_limit,
            },
            status=status.HTTP_200_OK,
        )

    suggestions = []
    previous_candidate = tentative_day - timedelta(days=1)
    next_candidate = tentative_day + timedelta(days=1)

    for _ in range(max_search_days):
        if len(suggestions) == 2:
            break

        previous_load = load_for_day(previous_candidate)
        if previous_load + hours_estimated <= daily_limit:
            previous_dt = timezone.make_aware(
                timezone.datetime.combine(previous_candidate, parsed_datetime.timetz().replace(tzinfo=None)),
                timezone.get_current_timezone(),
            )
            suggestions.append({
                'tentative_date': previous_dt.isoformat(),
                'current_load': previous_load + hours_estimated,
            })

        if len(suggestions) == 2:
            break

        next_load = load_for_day(next_candidate)
        if next_load + hours_estimated <= daily_limit:
            next_dt = timezone.make_aware(
                timezone.datetime.combine(next_candidate, parsed_datetime.timetz().replace(tzinfo=None)),
                timezone.get_current_timezone(),
            )
            suggestions.append({
                'tentative_date': next_dt.isoformat(),
                'current_load': next_load + hours_estimated,
            })

        previous_candidate -= timedelta(days=1)
        next_candidate += timedelta(days=1)

    return Response(
        {
            'valid': False,
            'current_load': current_load,
            'limit': daily_limit,
            'suggestions': suggestions,
        },
        status=status.HTTP_409_CONFLICT,
    )