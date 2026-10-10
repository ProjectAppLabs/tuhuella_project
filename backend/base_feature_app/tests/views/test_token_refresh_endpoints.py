"""Verify native refresh responses and isolated deleted-user handling."""

from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.db import OperationalError
from rest_framework import status
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken


@pytest.mark.django_db
def test_token_refresh_returns_401_when_user_deleted(api_client):
    """Token refresh returns 401 instead of 500 when the referenced user no longer exists."""
    user_model = get_user_model()
    user = user_model.objects.create_user(email='deleted@example.com', password='pass1234')
    refresh = RefreshToken.for_user(user)
    refresh_str = str(refresh)

    user.delete()

    response = api_client.post('/api/token/refresh/', {'refresh': refresh_str}, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['code'] == 'token_not_valid'
    assert not user_model.objects.filter(email='deleted@example.com').exists()


@pytest.mark.django_db
def test_token_refresh_returns_new_access_for_valid_token(api_client):
    """Token refresh returns a new access token when the refresh token is valid."""
    user_model = get_user_model()
    user = user_model.objects.create_user(email='valid@example.com', password='pass1234')
    refresh = RefreshToken.for_user(user)

    response = api_client.post('/api/token/refresh/', {'refresh': str(refresh)}, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert int(AccessToken(response.json()['access'])['user_id']) == user.pk


@pytest.mark.django_db
def test_token_refresh_rejects_invalid_token(api_client):
    """Token refresh returns 401 for a completely invalid token string."""
    response = api_client.post('/api/token/refresh/', {'refresh': 'not-a-real-token'}, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['code'] == 'token_not_valid'
    assert response['WWW-Authenticate'].startswith('Bearer')


@pytest.mark.django_db
def test_token_refresh_rejects_expired_token(api_client):
    """Keep expired refresh tokens classified as invalid credentials."""
    user = get_user_model().objects.create_user(email='expired@example.test', password='pass1234')
    refresh = RefreshToken.for_user(user)
    refresh.set_exp(lifetime=timedelta(days=-1))

    response = api_client.post('/api/token/refresh/', {'refresh': str(refresh)}, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['code'] == 'token_not_valid'


@pytest.mark.django_db
def test_token_refresh_preserves_native_rejection_for_inactive_user(api_client):
    """Let the native authentication handler reject inactive accounts."""
    user = get_user_model().objects.create_user(email='inactive@example.test', password='pass1234')
    refresh = RefreshToken.for_user(user)
    user.is_active = False
    user.save(update_fields=['is_active'])

    response = api_client.post('/api/token/refresh/', {'refresh': str(refresh)}, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response['WWW-Authenticate'].startswith('Bearer')


@pytest.mark.django_db
@pytest.mark.parametrize(
    'payload',
    [{}, {'refresh': None}, {'refresh': {}}, []],
    ids=['missing-refresh', 'null-refresh', 'object-refresh', 'non-object-body'],
)
def test_token_refresh_returns_native_validation_error(api_client, payload):
    """Report invalid input as a client error without rejecting credentials."""
    response = api_client.post('/api/token/refresh/', payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@pytest.mark.parametrize(
    'failure',
    [OperationalError('simulated database outage'), RuntimeError('simulated internal failure')],
    ids=['database-outage', 'unexpected-failure'],
)
def test_token_refresh_preserves_internal_server_error(api_client, settings, failure):
    """Keep internal failures as server errors so valid credentials survive."""
    settings.DEBUG = False
    api_client.raise_request_exception = False
    user_model = get_user_model()
    user = user_model.objects.create_user(email='failure@example.test', password='pass1234')
    refresh = RefreshToken.for_user(user)

    with patch.object(user_model.objects, 'get', side_effect=failure):
        response = api_client.post('/api/token/refresh/', {'refresh': str(refresh)}, format='json')

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


@pytest.mark.django_db
def test_token_refresh_internal_error_hides_sensitive_message(api_client, settings):
    """A production error response does not expose internal failure details."""
    settings.DEBUG = False
    api_client.raise_request_exception = False
    user_model = get_user_model()
    user = user_model.objects.create_user(email='private-error@example.test', password='pass1234')
    refresh = RefreshToken.for_user(user)
    sensitive_marker = 'diagnostic-secret-that-must-not-be-public'

    with patch.object(user_model.objects, 'get', side_effect=OperationalError(sensitive_marker)):
        response = api_client.post('/api/token/refresh/', {'refresh': str(refresh)}, format='json')

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert sensitive_marker.encode() not in response.content
