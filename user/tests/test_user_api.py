from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
PROFILE_URL = reverse('user:profile')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserApiTest(TestCase):
    def setUp(self):
        self.api_client = APIClient()

    def test_create_valid_user_success(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'test1234',
            'name': 'test user'
        }

        res = self.api_client.post(CREATE_USER_URL, data=payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))
        self.assertNotIn(payload['password'], res.data)

    def test_create_exist_user(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'test123'
        }
        create_user(**payload)

        res = self.api_client.post(CREATE_USER_URL, data=payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_too_short(self):
        payload = {
            'email': 'test@gmail.com',
            'password': 'pw'
        }

        res = self.api_client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exist = get_user_model().objects.filter(email=payload['email']).exists()
        self.assertFalse(user_exist)

    def test_create_token_for_user(self):
        """creating token for login"""
        payload = {
            'email': 'test@gmail.com',
            'password': 'test123'
        }
        create_user(**payload)
        res = self.api_client.post(TOKEN_URL, data=payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('token', res.data)

    def test_create_token_invalid_credential(self):
        create_user(email='test@gmail.com', password='test123')
        payload = {'email': 'test@gmail.com', 'password': 'wrong123'}
        res = self.api_client.post(TOKEN_URL, data=payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_create_token_no_user(self):
        """token not created if user does not exist"""
        payload = {'email': 'test@gmail.com', 'password': 'test123'}
        res = self.api_client.post(TOKEN_URL, data=payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertNotIn('token', res.data)

    def test_create_token_missing_fields(self):
        res = self.api_client.post(TOKEN_URL, {'email': 'test@gmail.com', 'password': ''})
        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_unauthorized_user(self):
        res = self.api_client.get(PROFILE_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(
            email='test@gmail.com',
            password='test123',
            name='test user'
        )
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        res = self.client.get(PROFILE_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'email': self.user.email,
            'name': self.user.name
        })

    def test_post_not_allowed(self):
        res = self.client.post(PROFILE_URL, {})
        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        payload = {'password': 'new_pass', 'name': 'new_name'}
        res = self.client.patch(PROFILE_URL, data=payload)

        self.user.refresh_from_db()
        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
