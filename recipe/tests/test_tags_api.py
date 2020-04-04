from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from rest_framework import status
from rest_framework.test import APIClient

from core.models import Tag

from recipe.serializers import TagSerializer

TAGS_URL = reverse('recipe:tag-list')


def create_user(email, password):
    return get_user_model().objects.create_user(email, password)


class PublicTagsTest(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_login_required(self):
        """Test that needing to login for retrieve tags list"""
        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateTagsTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user('test@gmail.com', 'test1234')
        self.client.force_authenticate(self.user)

    def test_retrieve_tags(self):
        Tag.objects.create(user=self.user, name='tag1')
        Tag.objects.create(user=self.user, name='tag2')
        tags = Tag.objects.all().order_by('name')
        serializer = TagSerializer(tags, many=True)

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, serializer.data)

    def test_tag_owned(self):
        user2 = create_user('other@gmail.com', 'pass123')
        Tag.objects.create(user=user2, name='apple')
        tag = Tag.objects.create(user=self.user, name='fruit')

        res = self.client.get(TAGS_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(len(res.data), 1)
        self.assertEqual(res.data[0]['name'], tag.name)