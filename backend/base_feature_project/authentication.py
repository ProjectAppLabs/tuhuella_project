"""JWT authentication tied to each account's credential generation."""

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken


def validate_auth_version(token, user):
    """Accept legacy tokens only before the account's first revocation."""
    version = token.get('auth_version', 0)
    if type(version) is not int or version != user.auth_version:
        raise InvalidToken('Token is invalid or expired')


class VersionedJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        validate_auth_version(validated_token, user)
        return user
