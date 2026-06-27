from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from activities.models import Activity
from config_daily_work_hours.api.serializer import ConfigDailyWorkHoursSerializer
from config_daily_work_hours.models import ConfigDailyWorkHours
from subactivities.models import SubActivity
from users.models import User


class ConfigDailyWorkHoursModuleTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(
			username='config_user',
			email='config_user@example.com',
			password='StrongPass123!',
		)
		self.client.force_authenticate(user=self.user)

	def test_p1_model_default_estimated_hours_is_six(self):
		config = ConfigDailyWorkHours.objects.create(user=self.user)
		self.assertEqual(config.estimated_hours, 6)

	def test_p2_create_endpoint_updates_existing_record_without_duplicates(self):
		ConfigDailyWorkHours.objects.create(user=self.user, estimated_hours=6)

		response = self.client.post(
			'/api/config-daily-work-hours/',
			data={'estimated_hours': 8},
			format='json',
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(
			ConfigDailyWorkHours.objects.filter(user=self.user, deleted_at__isnull=True).count(),
			1,
		)
		self.assertEqual(
			ConfigDailyWorkHours.objects.get(user=self.user, deleted_at__isnull=True).estimated_hours,
			8,
		)

	def test_p3_by_user_includes_busy_and_available_hours(self):
		ConfigDailyWorkHours.objects.create(user=self.user, estimated_hours=6)
		activity = Activity.objects.create(
			title='Actividad horas',
			type_activity=Activity.TypeActivity.EXAM,
			subject='Fisica',
			user=self.user,
		)
		today_reference = timezone.now().replace(hour=10, minute=0, second=0, microsecond=0)
		SubActivity.objects.create(
			name='Sub de hoy',
			activity=activity,
			target_date=today_reference,
			estimated_time=2,
		)

		with patch('config_daily_work_hours.api.views.now', return_value=today_reference):
			response = self.client.get('/api/config-daily-work-hours/by-user/')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]['busy_hours'], 2)
		self.assertEqual(response.data[0]['available_hours'], 4)

	def test_p4_serializer_rejects_zero_estimated_hours(self):
		serializer = ConfigDailyWorkHoursSerializer(
			data={
				'user': self.user.id,
				'estimated_hours': 0,
			}
		)

		self.assertFalse(serializer.is_valid())
		self.assertIn('estimated_hours', serializer.errors)

	def test_p5_create_endpoint_creates_record_when_none_exists(self):
		response = self.client.post(
			'/api/config-daily-work-hours/',
			data={'estimated_hours': 7},
			format='json',
		)

		self.assertEqual(response.status_code, 201)
		self.assertEqual(
			ConfigDailyWorkHours.objects.filter(user=self.user, deleted_at__isnull=True).count(),
			1,
		)
		self.assertEqual(response.data['estimated_hours'], 7)


