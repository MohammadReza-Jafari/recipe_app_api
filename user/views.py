from rest_framework import generics, authentication, permissions
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.settings import api_settings

from user import serializers


class CreateUserView(generics.CreateAPIView):
    serializer_class = serializers.UserSerializer


class CreateTokenView(ObtainAuthToken):
    renderer_classes = api_settings.DEFAULT_RENDERER_CLASSES
    serializer_class = serializers.AuthTokenSerializer


class ManageUserApiView(generics.RetrieveUpdateAPIView):
    authentication_classes = (authentication.TokenAuthentication,
                              authentication.SessionAuthentication)
    permission_classes = (permissions.IsAuthenticated, )
    serializer_class = serializers.UserSerializer

    def get_object(self):
        return self.request.user
