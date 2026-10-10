"""
Authentication utility functions.
"""
from rest_framework_simplejwt.tokens import RefreshToken

# Re-export email functions for backwards compatibility with existing imports.
from base_feature_app.utils.email_utils import (  # noqa: F401
    send_password_reset_code,
    send_verification_code,
)


def generate_refresh_token(user):
    """Bind tokens to the account snapshot that authenticated the request."""
    refresh = RefreshToken.for_user(user)
    refresh['auth_version'] = user.auth_version
    return refresh


def generate_auth_tokens(user):
    """
    Generate JWT tokens for a user.

    :param user: User instance
    :return: Dictionary with refresh, access tokens and user data
    """
    refresh = generate_refresh_token(user)

    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'city': user.city,
            'role': user.role,
            'is_staff': user.is_staff,
            'date_joined': user.date_joined.isoformat(),
        }
    }
