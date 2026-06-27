from datetime import timedelta
from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from activities.models import Activity
from config_daily_work_hours.models import ConfigDailyWorkHours
from subactivities.api.serializer import SubActivitySerializer
from subactivities.models import SubActivity
from users.models import User


class SubActivitiesModuleTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(
			username='sub_user',
			email='sub_user@example.com',
			password='StrongPass123!',
		)
		self.client.force_authenticate(user=self.user)
		self.activity = Activity.objects.create(
			title='Actividad principal',
			type_activity=Activity.TypeActivity.QUIZ,
			subject='Algebra',
			user=self.user,
		)
		self.config = ConfigDailyWorkHours.objects.create(user=self.user, estimated_hours=4)

	def test_p1_serializer_accepts_subactivity_within_daily_limit(self):
		target = timezone.now() + timedelta(hours=1)
		SubActivity.objects.create(
			name='Carga actual',
			activity=self.activity,
			target_date=target,
			estimated_time=1,
		)

		serializer = SubActivitySerializer(
			data={
				'name': 'Nueva subactividad',
				'description': 'ok',
				'activity': self.activity.id,
				'target_date': target.isoformat(),
				'estimated_time': 2,
				'status_subactivity': 0,
			}
		)

		self.assertTrue(serializer.is_valid(), serializer.errors)

	def test_p2_serializer_rejects_subactivity_when_daily_limit_exceeded(self):
		target = timezone.now() + timedelta(hours=2)
		SubActivity.objects.create(
			name='Carga existente',
			activity=self.activity,
			target_date=target,
			estimated_time=3,
		)

		serializer = SubActivitySerializer(
			data={
				'name': 'Subactividad que excede',
				'description': 'error esperado',
				'activity': self.activity.id,
				'target_date': target.isoformat(),
				'estimated_time': 2,
				'status_subactivity': 0,
			}
		)

		self.assertFalse(serializer.is_valid())
		self.assertIn('estimated_time', serializer.errors)

	def test_p3_subactivities_by_activity_excludes_soft_deleted(self):
		active = SubActivity.objects.create(
			name='Activa',
			activity=self.activity,
			target_date=timezone.now(),
			estimated_time=1,
		)
		SubActivity.objects.create(
			name='Eliminada',
			activity=self.activity,
			target_date=timezone.now(),
			estimated_time=1,
			deleted_at=timezone.now(),
		)

		response = self.client.get(f'/api/sub-activities/by-activity/{self.activity.id}')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]['id'], active.id)

	def test_p4_validate_tentative_date_returns_conflict_and_suggestions(self):
		tentative_date = timezone.now() + timedelta(hours=3)
		sub = SubActivity.objects.create(
			name='Sub principal',
			activity=self.activity,
			target_date=tentative_date,
			estimated_time=3,
		)
		SubActivity.objects.create(
			name='Carga extra',
			activity=self.activity,
			target_date=tentative_date,
			estimated_time=2,
		)

		response = self.client.post(
			'/api/sub-activities/validate-tentative-date',
			data={
				'subactivity': sub.id,
				'tentative_date': tentative_date.isoformat(),
			},
			format='json',
		)

		self.assertEqual(response.status_code, 409)
		self.assertFalse(response.data['valid'])
		self.assertGreaterEqual(len(response.data['suggestions']), 1)

	def test_p5_validate_tentative_date_to_create_sub_returns_valid_true(self):
		tentative_date = timezone.now() + timedelta(days=1)

		response = self.client.post(
			'/api/sub-activities/validate-tentative-date-to-create-sub',
			data={
				'tentative_date': tentative_date.isoformat(),
				'hours_estimated': 2,
			},
			format='json',
		)

		self.assertEqual(response.status_code, 200)
		self.assertTrue(response.data['valid'])
		self.assertEqual(response.data['limit'], self.config.estimated_hours)
