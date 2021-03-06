from django.test import TestCase
from django.contrib.auth import get_user_model
from core import models

from unittest.mock import patch


def sample_user(email='test@gamil.com', password='pass123'):
    return get_user_model().objects.create_user(email, password)


class ModelTests(TestCase):
    def test_create_user_with_email_successful(self):
        """test creating user with an email"""
        email = 'chashm78@gmail.com'
        password = 'django1234'
        user = get_user_model().objects.create_user(
            email=email,
            password=password
        )
        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_create_user_with_normalized_email(self):
        email = 'chashm78@GMAIL.COM'
        password = 'django1234'
        user = get_user_model().objects.create_user(email=email, password=password)
        self.assertEqual(email.lower(), user.email)

    def test_new_user_invalid_email(self):
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'password1234')

    def test_create_new_superuser(self):
        """test create new super user"""
        user = get_user_model().objects.create_superuser('chashm78@gmail.com', 'django1234')
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)

    def test_tag_model(self):
        user = sample_user()
        tag = models.Tag.objects.create(name='tag', user=user)

        self.assertEqual(str(tag), tag.name)

    def test_ingredient_model(self):
        ingredient = models.Ingredient.objects.create(user=sample_user(), name='potato')
        self.assertEqual(str(ingredient), ingredient.name)

    def test_recipe_model(self):
        recipe = models.Recipe.objects.create(
            user=sample_user(),
            title='ghorme sabzi',
            time_minutes=5,
            price=6.00
        )

        self.assertEqual(str(recipe), recipe.title)

    @patch('uuid.uuid4')
    def test_recipe_file_name_uuid(self, mock_uuid):
        uuid = 'test-uuid'
        mock_uuid.return_value = uuid
        file_path = models.recipe_image_file_path(None, 'myimage.jpg')

        exp_path = f'uploads/recipe/{uuid}.jpg'

        self.assertEqual(file_path, exp_path)
