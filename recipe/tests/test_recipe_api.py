from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Ingredient, Tag
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


def get_recipe_detail_url(recipe_id):
    return reverse('recipe:recipe-detail', args=[recipe_id])


def sample_tag(user, name='sweet'):
    return Tag.objects.create(user=user, name=name)


def sample_ingredient(user, name='tomato'):
    return Ingredient.objects.create(user=user, name=name)


def sample_recipe(user, **params):
    default = {
        'title': 'mushroom',
        'time_minutes': 7,
        'price': 3.56
    }
    default.update(params)

    return Recipe.objects.create(user=user, **default)


RECIPES_URL = reverse('recipe:recipe-list')


class PublicRecipeTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_auth_required(self):
        res = self.client.get(RECIPES_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateRecipeTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='clone@gmail.com',
            password='testpass123'
        )

        self.client.force_authenticate(self.user)

    def test_retrieve_recipes(self):
        sample_recipe(user=self.user)
        sample_recipe(user=self.user)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.all()
        ser = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(ser.data, res.data)

    def test_recipes_limited_to_user(self):
        user2 = get_user_model().objects.create_user(
            email='other@gmail.com',
            password='otherpass'
        )
        sample_recipe(user=self.user)
        sample_recipe(user=user2)

        res = self.client.get(RECIPES_URL)
        recipes = Recipe.objects.filter(user=self.user)
        ser = RecipeSerializer(recipes, many=True)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, ser.data)
        self.assertEqual(len(res.data), 1)

    def test_view_recipe_detail(self):
        recipe = sample_recipe(user=self.user)
        recipe.tags.add(sample_tag(user=self.user))
        recipe.ingredients.add(sample_ingredient(user=self.user))
        ser = RecipeDetailSerializer(recipe)

        url = get_recipe_detail_url(recipe.id)

        res = self.client.get(url)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, ser.data)
