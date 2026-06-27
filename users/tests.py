from django.contrib.auth.hashers import check_password
from django.test import TestCase
from rest_framework.test import APIClient

from config_daily_work_hours.models import ConfigDailyWorkHours
from users.api.serializers import RegisterSerializer
from users.models import User


class UsersModuleTests(TestCase):
	def setUp(self):
		self.client = APIClient()
		self.user = User.objects.create_user(
			username='base_user',
			email='base_user@example.com',
			password='StrongPass123!',
		)

	def test_p1_register_serializer_hashes_password(self):
		serializer = RegisterSerializer(
			data={
				'username': 'nuevo',
				'first_name': 'Nuevo',
				'last_name': 'Usuario',
				'password': 'PasswordSeguro123!',
				'email': 'nuevo@example.com',
				'is_staff': False,
				'is_superuser': False,
				'is_active': True,
			}
		)

		self.assertTrue(serializer.is_valid(), serializer.errors)
		user = serializer.save()
		self.assertNotEqual(user.password, 'PasswordSeguro123!')
		self.assertTrue(check_password('PasswordSeguro123!', user.password))

	def test_p2_create_user_endpoint_creates_default_config(self):
		payload = {
			'username': 'api_user',
			'first_name': 'Api',
			'last_name': 'User',
			'password': 'PasswordSeguro123!',
			'email': 'api_user@example.com',
			'is_staff': False,
			'is_superuser': False,
			'is_active': True,
		}

		response = self.client.post('/api/user/', data=payload, format='json')

		self.assertEqual(response.status_code, 201)
		created_user = User.objects.get(email='api_user@example.com')
		self.assertTrue(
			ConfigDailyWorkHours.objects.filter(user=created_user, estimated_hours=6).exists()
		)

	def test_p3_get_info_user_returns_authenticated_user_data(self):
		self.client.force_authenticate(user=self.user)

		response = self.client.get('/api/auth/me')

		self.assertEqual(response.status_code, 200)
		self.assertEqual(response.data['id'], self.user.id)
		self.assertEqual(response.data['email'], self.user.email)

	def test_p4_destroy_user_sets_deleted_at(self):
		self.client.force_authenticate(user=self.user)

		response = self.client.delete(f'/api/user/{self.user.id}/')

		self.assertEqual(response.status_code, 200)
		self.user.refresh_from_db()
		self.assertIsNotNone(self.user.deleted_at)
		self.assertEqual(response.data['status'], 'ok')

	def test_p5_list_users_requires_authentication(self):
		response_without_auth = self.client.get('/api/user/')
		self.client.force_authenticate(user=self.user)
		response_with_auth = self.client.get('/api/user/')

		self.assertEqual(response_without_auth.status_code, 401)
		self.assertEqual(response_with_auth.status_code, 200)
		self.assertGreaterEqual(len(response_with_auth.data), 1)
