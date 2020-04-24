from django.contrib.auth import get_user_model
from django.urls import reverse
from django.test import TestCase

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Ingredient, Recipe

from recipe.serializers import IngredientSerializer

INGREDIENTS_URL = reverse('recipe:ingredient-list')


class PublicIngredientTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        res = self.client.get(INGREDIENTS_URL)
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateIngredientTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            'test@gmail.com',
            'testpass'
        )
        self.client.force_authenticate(self.user)

    def test_retrieve_ingredient_list(self):
        Ingredient.objects.create(user=self.user, name='potato')
        Ingredient.objects.create(user=self.user, name='potato')
        ingredients = Ingredient.objects.all().order_by('name')

        ser = IngredientSerializer(ingredients, many=True)
        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, ser.data)

    def test_ingredient_limited_to_user(self):
        user2 = get_user_model().objects.create_user('other@gmail.com', 'other123')
        Ingredient.objects.create(user=user2, name='tomato')
        ingredient = Ingredient.objects.create(user=self.user, name='potato')

        res = self.client.get(INGREDIENTS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], ingredient.name)

    def test_create_ingredient_successful(self):
        payload = {
            'name': 'tomato'
        }
        res = self.client.post(INGREDIENTS_URL, payload)

        exist = Ingredient.objects.filter(user=self.user, name=payload['name']).exists()
        self.assertTrue(exist)

    def test_create_invalid_ingredient(self):
        payload = {'name:': ''}
        res = self.client.post(INGREDIENTS_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_ingredients_assigned_to_recipe(self):
        ingredient1 = Ingredient.objects.create(
            name='tomato',
            user=self.user
        )
        ingredient2 = Ingredient.objects.create(
            name='potato',
            user=self.user
        )
        recipe = Recipe.objects.create(
            title='nimro',
            price=5.00,
            time_minutes=12,
            user=self.user
        )
        recipe.ingredients.add(ingredient1)

        res = self.client.get(INGREDIENTS_URL, {'assigned_only': 1})

        ser1 = IngredientSerializer(ingredient1)
        ser2 = IngredientSerializer(ingredient2)

        self.assertIn(ser1.data, res.data)
        self.assertNotIn(ser2.data, res.data)