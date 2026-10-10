from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenRefreshView


class SafeTokenRefreshView(TokenRefreshView):
    """Gracefully handle refresh tokens referencing deleted users."""

    def post(self, request, *args, **kwargs):
        """Preserve native errors except for a deleted token owner."""
        try:
            return super().post(request, *args, **kwargs)
        except get_user_model().DoesNotExist:
            return Response(
                {'detail': 'Token is invalid or expired', 'code': 'token_not_valid'},
                status=status.HTTP_401_UNAUTHORIZED,
            )
