from rest_framework import serializers

from django.contrib.auth import get_user_model, authenticate
from django.utils.translation import gettext as _


class UserSerializer(serializers.ModelSerializer):
    """serializer for user in system"""
    class Meta:
        model = get_user_model()
        fields = ('email', 'password', 'name')
        extra_kwargs = {
            'password': {
                'write_only': True,
                'min_length': 5,
                'style': {
                    'input_type': 'password'
                }
            }
        }

    def create(self, validated_data):
        """creating new user"""
        return get_user_model().objects.create_user(**validated_data)

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        user = super().update(instance, validated_data)

        if password:
            user.set_password(password)
            user.save()
        return user


class AuthTokenSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(
        style={'input_type': 'password'},
        trim_whitespace=False
    )

    def validate(self, attrs):
        email = attrs['email']
        password = attrs['password']

        user = authenticate(
            self.context['request'],
            email=email,
            password=password
        )

        if not user:
            msg = _('Unable to authenticate with provided credential')
            raise serializers.ValidationError(msg, code='authentication')

        attrs['user'] = user
        return attrs
