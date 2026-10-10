"""Preserve native JWT contracts while checking account revocations."""

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.serializers import (
    TokenObtainPairSerializer,
    TokenRefreshSerializer,
)
from rest_framework_simplejwt.settings import api_settings

from base_feature_app.utils.auth_utils import generate_refresh_token
from base_feature_project.authentication import validate_auth_version


class VersionedTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        return generate_refresh_token(user)


class VersionedTokenRefreshSerializer(TokenRefreshSerializer):
    def validate(self, attrs):
        refresh = self.token_class(attrs['refresh'])
        user = get_user_model().objects.get(
            **{api_settings.USER_ID_FIELD: refresh[api_settings.USER_ID_CLAIM]},
        )
        validate_auth_version(refresh, user)
        # The native serializer copies the original claim into access/rotated
        # refresh tokens. Never replace it with a later database generation.
        return super().validate(attrs)
