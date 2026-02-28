from rest_framework.routers import DefaultRouter
from django.urls import path
from activities.api.views import *


router_activities = DefaultRouter()
router_activities.register(prefix='', basename='activities', viewset=ActivityApiViewSet)


urlpatterns = [
    path('activities/by-user/', activities_by_user, name='activities_by_user'),
]