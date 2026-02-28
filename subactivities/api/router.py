from rest_framework.routers import DefaultRouter
from django.urls import path
from subactivities.api.views import *


router_sub_activities = DefaultRouter()
router_sub_activities.register(prefix='', basename='sub_activities', viewset=SubActivityApiViewSet)


urlpatterns = [
    path('sub-activities/by-activity/<activity_id>', sub_activities_by_activities, name='sub-activities-by-activity'),
]