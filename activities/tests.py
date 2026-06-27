from datetime import timedelta
from unittest.mock import patch

from django.test import TestCase
from django.utils import timezone
from rest_framework.test import APIClient

from activities.models import Activity
from subactivities.models import SubActivity
from users.models import User


class ActivityModuleTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(
			username='activity_owner',
			email='activity_owner@example.com',
			password='StrongPass123!',
		)
		self.other_user = User.objects.create_user(
			username='other_user',
			email='other_user@example.com',
			password='StrongPass123!',
		)
		self.client.force_authenticate(user=self.user)

	def _activity_payload(self, title='Actividad base'):
		now = timezone.now()
		return {
			'title': title,
			'type_activity': Activity.TypeActivity.QUIZ,
			'description': 'Descripcion',
			'subject': 'Matematicas',
			'event_date': now.isoformat(),
			'deadline': (now + timedelta(days=1)).isoformat(),
			'grade': 4.5,
			'user': self.user.id,
		}

	def test_p1_activity_str_returns_title(self):
		activity = Activity.objects.create(
			title='Parcial Final',
			type_activity=Activity.TypeActivity.EXAM,
			subject='Calculo',
			user=self.user,
		)

		self.assertEqual(str(activity), 'Parcial Final')

	def test_p2_activities_by_user_only_returns_owner_data(self):
		own_activity = Activity.objects.create(
			title='Quiz 1',
			type_activity=Activity.TypeActivity.QUIZ,
			subject='Fisica',
			user=self.user,
		)
		Activity.objects.create(
			title='Proyecto Externo',
			type_activity=Activity.TypeActivity.PROJECT,
			subject='Quimica',
			user=self.other_user,
		)

		SubActivity.objects.create(
			name='Resolver guia',
			activity=own_activity,
			target_date=timezone.now(),
			estimated_time=2,
			status_subactivity=2,
		)

		response = self.client.get('/api/activities/by-user/')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data), 1)
		self.assertEqual(response.data[0]['title'], 'Quiz 1')
		self.assertEqual(response.data[0]['total_subactivities'], 1)
		self.assertEqual(response.data[0]['total_completed'], 1)

	def test_p3_activity_retrieve_includes_subactivity_counters(self):
		activity = Activity.objects.create(
			title='Taller Integrador',
			type_activity=Activity.TypeActivity.WORKSHOP,
			subject='Programacion',
			user=self.user,
		)
		SubActivity.objects.create(
			name='Parte 1',
			activity=activity,
			target_date=timezone.now(),
			estimated_time=1,
			status_subactivity=0,
		)
		SubActivity.objects.create(
			name='Parte 2',
			activity=activity,
			target_date=timezone.now(),
			estimated_time=1,
			status_subactivity=2,
		)

		response = self.client.get(f'/api/activities/{activity.id}/')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data['total_subactivities'], 2)
		self.assertEqual(response.data['total_completed'], 1)

	def test_p4_create_activity_with_nested_subactivities(self):
		payload = self._activity_payload(title='Actividad con sub')
		payload['subactivities'] = [
			{
				'name': 'Sub tarea inicial',
				'description': 'Detalle',
				'target_date': (timezone.now() + timedelta(hours=2)).isoformat(),
				'estimated_time': 2,
				'status_subactivity': 0,
			}
		]

		response = self.client.post('/api/activities/', data=payload, format='json')

		self.assertEqual(response.status_code, 201)
		created = Activity.objects.get(id=response.data['id'])
		self.assertEqual(created.user, self.user)
		self.assertEqual(created.subactivities.count(), 1)

	def test_p5_sub_activities_for_today_classifies_items(self):
		activity = Activity.objects.create(
			title='Clasificacion diaria',
			type_activity=Activity.TypeActivity.OTHER,
			subject='General',
			user=self.user,
		)

		base = timezone.now().replace(hour=12, minute=0, second=0, microsecond=0)

		SubActivity.objects.create(
			name='Vencida',
			activity=activity,
			target_date=base - timedelta(hours=1),
			estimated_time=1,
			status_subactivity=0,
		)
		SubActivity.objects.create(
			name='Hoy mas tarde',
			activity=activity,
			target_date=base + timedelta(hours=1),
			estimated_time=2,
			status_subactivity=0,
		)
		SubActivity.objects.create(
			name='Proxima',
			activity=activity,
			target_date=base + timedelta(days=1),
			estimated_time=1,
			status_subactivity=0,
		)

		with patch('activities.api.views.timezone.now', return_value=base):
			response = self.client.get('/api/today/')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(len(response.data['expired']), 1)
		self.assertEqual(len(response.data['today']), 1)
		self.assertEqual(len(response.data['upcoming']), 1)
