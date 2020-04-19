import tempfile
import os
from PIL import Image

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Recipe, Ingredient, Tag
from recipe.serializers import RecipeSerializer, RecipeDetailSerializer


def image_upload_url(recipe_id):
    return reverse('recipe:recipe-upload-image', args=[recipe_id])


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

    def test_create_basic_recipe(self):
        payload = {
            'title': 'Ghorme',
            'time_minutes': 30,
            'price': 52.00
        }

        res = self.client.post(RECIPES_URL, payload)
        recipe = Recipe.objects.get(id=res.data['id'])

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        for key in payload.keys():
            self.assertEqual(payload[key], getattr(recipe, key))

    def test_create_recipe_with_tags(self):
        tag1 = sample_tag(self.user, 'vegan')
        tag2 = sample_tag(self.user, 'desert')
        payload = {
            'title': 'Ice Cream',
            'tags': [tag1.id, tag2.id],
            'time_minutes': 20,
            'price': 34.00
        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        recipe = Recipe.objects.get(id=res.data['id'])
        tags = recipe.tags.all()
        self.assertEqual(tags.count(), 2)
        self.assertIn(tag1, tags)
        self.assertIn(tag2, tags)

    def test_create_recipe_with_ingredients(self):
        ing1 = sample_ingredient(self.user, 'potato')
        ing2 = sample_ingredient(self.user, 'onion')
        payload = {
            'title': 'soup',
            'time_minutes': 45,
            'price': 35,
            'ingredients': [ing1.id, ing2.id]
        }

        res = self.client.post(RECIPES_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        recipe = Recipe.objects.get(id=res.data['id'])
        ingredients = recipe.ingredients.all()
        self.assertEqual(ingredients.count(), 2)

        self.assertIn(ing1, ingredients)
        self.assertIn(ing2, ingredients)

    # def test_partial_update_recipe(self):
    #     recipe = sample_recipe(self.user)
    #     recipe.tags.add(sample_tag(self.user))
    #     new_tag = sample_tag(self.user, 'desert')
    #
    #     payload = {'title': 'other recipe', 'tags': [new_tag]}
    #     url = get_recipe_detail_url(recipe.id)
    #     res = self.client.patch(url, payload)
    #
    #     recipe.refresh_from_db()
    #     self.assertEqual(recipe.title, payload['title'])
    #     tags = recipe.tags.all()
    #
    #     self.assertEqual(len(tags), 1)
    #     self.assertIn(new_tag, tags)

    def test_full_update_recipe(self):
        recipe = sample_recipe(self.user)
        recipe.tags.add(sample_tag(self.user))
        payload = {
            'title': 'other recipe',
            'time_minutes': 20,
            'price': 5.00
        }

        url = get_recipe_detail_url(recipe.id)
        self.client.put(url, payload)
        recipe.refresh_from_db()
        self.assertEqual(recipe.title, payload['title'])
        self.assertEqual(recipe.time_minutes, payload['time_minutes'])
        self.assertEqual(recipe.price, payload['price'])

        tags = recipe.tags.all()
        self.assertEqual(len(tags), 0)


class RecipeUploadImageTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = get_user_model().objects.create_user(
            email='test@gmail.com',
            password='testpass'
        )
        self.client.force_authenticate(self.user)
        self.recipe = sample_recipe(self.user)

    def tearDown(self):
        self.recipe.image.delete()

    def test_upload_image_to_recipe(self):
        url = image_upload_url(self.recipe.id)
        with tempfile.NamedTemporaryFile(suffix='.jpg') as ntf:
            img = Image.new('RGB', (10, 10))
            img.save(ntf, format='JPEG')
            ntf.seek(0)
            res = self.client.post(url, {'image': ntf}, format='multipart')

        self.recipe.refresh_from_db()
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('image', res.data)
        self.assertTrue(os.path.exists(self.recipe.image.path))

    def test_upload_image_bad_request(self):
        url = image_upload_url(self.recipe.id)
        res = self.client.post(url, {'image': 'not image'}, format='multipart')

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_filter_recipe_with_tags(self):
        recipe1 = sample_recipe(self.user, title="ghorme")
        recipe2 = sample_recipe(self.user, title='ab gosht')
        tag1 = sample_tag(self.user, name='desert')
        tag2 = sample_tag(self.user, name='vegan')
        recipe1.tags.add(tag1)
        recipe2.tags.add(tag2)
        recipe3 = sample_recipe(self.user, title='polo')

        res = self.client.get(
            RECIPES_URL,
            {'tags': f'{tag1.id},{tag2.id}'}
        )

        ser1 = RecipeSerializer(recipe1)
        ser2 = RecipeSerializer(recipe2)
        ser3 = RecipeSerializer(recipe3)

        self.assertIn(ser1.data, res.data)
        self.assertIn(ser2.data, res.data)
        self.assertNotIn(ser3.data, res.data)

    def test_filter_recipe_with_ingredient(self):
        recipe1 = sample_recipe(self.user, title='ab paz')
        recipe2 = sample_recipe(self.user, title='cake')
        ingredient1 = sample_ingredient(self.user, name='sabzi')
        ingredient2 = sample_ingredient(self.user, name='namak')
        recipe1.ingredients.add(ingredient1)
        recipe2.ingredients.add(ingredient2)
        recipe3 = sample_recipe(self.user, title='salad')

        res = self.client.get(
            RECIPES_URL,
            {'ingredients': f'{ingredient1.id},{ingredient2.id}'}
        )

        ser1 = RecipeSerializer(recipe1)
        ser2 = RecipeSerializer(recipe2)
        ser3 = RecipeSerializer(recipe3)

        self.assertIn(ser1.data, res.data)
        self.assertIn(ser2.data, res.data)
        self.assertNotIn(ser3.data, res.data)
