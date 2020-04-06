from rest_framework import viewsets, mixins
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from rest_framework.permissions import IsAuthenticated

from core.models import Tag, Ingredient
from recipe import serializers


class TagsViewSet(viewsets.GenericViewSet,
                  mixins.ListModelMixin,
                  mixins.CreateModelMixin
                  ):
    queryset = Tag.objects.all()
    authentication_classes = (TokenAuthentication, SessionAuthentication)
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.TagSerializer

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class IngredientViewSet(viewsets.GenericViewSet, mixins.ListModelMixin):
    permission_classes = (IsAuthenticated,)
    serializer_class = serializers.IngredientSerializer
    authentication_classes = (TokenAuthentication,)
    queryset = Ingredient.objects.all()

    def get_queryset(self):
        return self.queryset.filter(user=self.request.user).order_by('name')
