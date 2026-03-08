from rest_framework.routers import DefaultRouter
from django.urls import path
from config_daily_work_hours.api.views import *


router_config_daily_work_hours = DefaultRouter()
router_config_daily_work_hours.register(prefix='', basename='config-daily-work-hours', viewset=ConfigDailyWorkHoursApiViewSet)


urlpatterns = [
    path('config-daily-work-hours/by-user/', config_daily_work_hours_by_user, name='config-daily-work-hours-by-user'),
]