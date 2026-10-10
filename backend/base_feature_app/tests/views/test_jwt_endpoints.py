from datetime import datetime, timezone
from types import SimpleNamespace

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from rest_framework import status

from base_feature_app.tests.factories import UserFactory
from base_feature_app.views.auth import SignInThrottle


@pytest.fixture(autouse=True)
def clear_token_throttle_cache():
    cache.clear()
    yield
    cache.clear()


@pytest.fixture(autouse=True)
def fast_token_password_hashing(settings):
    """Exercise real password checks without spending the host budget on PBKDF2."""
    settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']


@pytest.fixture
def token_user(db):
    return UserFactory(email='token@example.com', password='StrongTokenPass123!')


@pytest.fixture
def captcha_enabled(settings):
    settings.DEBUG = False
    settings.RECAPTCHA_SECRET_KEY = 'test-recaptcha-secret'


TOKEN_CREDENTIALS = {'email': 'token@example.com', 'password': 'StrongTokenPass123!'}


@pytest.mark.django_db
def test_token_obtain_pair_with_email_success(api_client):
    User = get_user_model()
    User.objects.create_user(email='token@example.com', password='pass1234')

    response = api_client.post('/api/token/', {'email': 'token@example.com', 'password': 'pass1234'}, format='json')
    assert response.status_code == status.HTTP_200_OK
    assert set(response.json()) == {'access', 'refresh'}
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}")
    authenticated_response = api_client.get(reverse('validate_token'))
    assert authenticated_response.status_code == status.HTTP_200_OK
    assert authenticated_response.json()['user']['email'] == 'token@example.com'
    refresh_response = api_client.post(
        '/api/token/refresh/', {'refresh': response.json()['refresh']}, format='json',
    )
    assert refresh_response.status_code == status.HTTP_200_OK
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh_response.json()['access']}")
    refreshed_response = api_client.get(reverse('validate_token'))
    assert refreshed_response.status_code == status.HTTP_200_OK
    assert refreshed_response.json()['user']['email'] == 'token@example.com'


@pytest.mark.django_db
@pytest.mark.parametrize('missing_field', ['email', 'password'])
def test_token_obtain_pair_preserves_missing_field_errors(api_client, missing_field):
    payload = TOKEN_CREDENTIALS.copy()
    payload.pop(missing_field)

    response = api_client.post(reverse('token_obtain_pair'), payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {missing_field: ['This field is required.']}


@pytest.mark.django_db
@pytest.mark.parametrize('field,value', [('email', {}), ('password', [])])
def test_token_obtain_pair_rejects_invalid_field_types(api_client, field, value):
    payload = {**TOKEN_CREDENTIALS, field: value}

    response = api_client.post(reverse('token_obtain_pair'), payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {field: ['Not a valid string.']}


@pytest.mark.django_db
@pytest.mark.parametrize('body', ['[]', 'null', '"plain"'])
def test_token_obtain_pair_preserves_non_mapping_body_validation(api_client, captcha_enabled, body):
    response = api_client.generic(
        'POST', reverse('token_obtain_pair'), body, content_type='application/json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'non_field_errors' in response.json()
    assert 'access' not in response.json()


@pytest.mark.django_db
@pytest.mark.parametrize('payload', [
    {'email': 'missing@example.com', 'password': 'StrongTokenPass123!'},
    {'email': 'token@example.com', 'password': 'WrongPassword123!'},
], ids=['unknown-user', 'wrong-password'])
def test_token_obtain_pair_rejects_invalid_credentials_with_401(api_client, token_user, payload):
    response = api_client.post(reverse('token_obtain_pair'), payload, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {'detail': 'No active account found with the given credentials'}
    assert response['WWW-Authenticate'] == 'Bearer realm="api"'
    token_user.refresh_from_db()
    assert token_user.last_login is None
    assert token_user.check_password(TOKEN_CREDENTIALS['password'])


@pytest.mark.django_db
def test_token_obtain_pair_rejects_inactive_user(api_client, token_user):
    token_user.is_active = False
    token_user.save(update_fields=['is_active'])

    response = api_client.post(reverse('token_obtain_pair'), TOKEN_CREDENTIALS, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {'detail': 'No active account found with the given credentials'}
    assert response['WWW-Authenticate'] == 'Bearer realm="api"'
    token_user.refresh_from_db()
    assert token_user.is_active is False
    assert token_user.last_login is None


@pytest.mark.django_db
def test_token_obtain_pair_rejects_archived_user(api_client, token_user):
    archived_at = datetime(2026, 1, 1, tzinfo=timezone.utc)
    token_user.archived_at = archived_at
    token_user.save(update_fields=['archived_at'])

    response = api_client.post(reverse('token_obtain_pair'), TOKEN_CREDENTIALS, format='json')

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json() == {'detail': 'No active account found with the given credentials'}
    assert response['WWW-Authenticate'] == 'Bearer realm="api"'
    token_user.refresh_from_db()
    assert token_user.archived_at == archived_at
    assert token_user.is_active is True
    assert token_user.last_login is None


@pytest.mark.django_db
@pytest.mark.parametrize('first,second', [
    ('sign_in', 'token_obtain_pair'),
    ('token_obtain_pair', 'sign_in'),
], ids=['sign-in-first', 'token-first'])
def test_token_obtain_pair_shares_sign_in_rate_limit(api_client, monkeypatch, first, second):
    monkeypatch.setattr(SignInThrottle, 'get_rate', lambda self: '2/minute')
    payload = {'email': 'missing@example.com', 'password': 'WrongPassword123!'}

    first_response = api_client.post(reverse(first), payload, format='json')
    second_response = api_client.post(reverse(second), payload, format='json')
    blocked_response = api_client.post(reverse(first), payload, format='json')

    assert first_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert second_response.status_code == status.HTTP_401_UNAUTHORIZED
    assert blocked_response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    assert 'access' not in blocked_response.json()
    assert int(blocked_response['Retry-After']) > 0


@pytest.mark.django_db
def test_token_obtain_pair_rejects_missing_recaptcha_when_enabled(api_client, token_user, captcha_enabled):
    response = api_client.post(reverse('token_obtain_pair'), TOKEN_CREDENTIALS, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'error': 'reCAPTCHA verification failed.'}
    token_user.refresh_from_db()
    assert token_user.last_login is None
    assert token_user.check_password(TOKEN_CREDENTIALS['password'])


@pytest.mark.django_db
def test_token_obtain_pair_rejects_failed_recaptcha(api_client, token_user, captcha_enabled, monkeypatch):
    monkeypatch.setattr(
        'base_feature_app.views.auth.requests.post',
        lambda *args, **kwargs: SimpleNamespace(json=lambda: {'success': False}),
    )

    response = api_client.post(
        reverse('token_obtain_pair'), {**TOKEN_CREDENTIALS, 'captcha_token': 'failed'}, format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'error': 'reCAPTCHA verification failed.'}
    token_user.refresh_from_db()
    assert token_user.last_login is None
    assert token_user.check_password(TOKEN_CREDENTIALS['password'])


@pytest.mark.django_db
def test_token_obtain_pair_accepts_valid_recaptcha(api_client, token_user, captcha_enabled, monkeypatch):
    monkeypatch.setattr(
        'base_feature_app.views.auth.requests.post',
        lambda *args, **kwargs: SimpleNamespace(json=lambda: {'success': True}),
    )

    response = api_client.post(
        reverse('token_obtain_pair'), {**TOKEN_CREDENTIALS, 'captcha_token': 'valid'}, format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert set(response.json()) == {'access', 'refresh'}


@pytest.mark.django_db
def test_token_obtain_pair_preserves_ignored_authorization_header(api_client, token_user):
    api_client.credentials(HTTP_AUTHORIZATION='Bearer invalid-token')

    response = api_client.post(reverse('token_obtain_pair'), TOKEN_CREDENTIALS, format='json')

    assert response.status_code == status.HTTP_200_OK
    assert set(response.json()) == {'access', 'refresh'}


@pytest.mark.django_db
def test_token_obtain_pair_does_not_update_last_login(api_client, token_user):
    last_login = datetime(2026, 1, 1, tzinfo=timezone.utc)
    token_user.last_login = last_login
    token_user.save(update_fields=['last_login'])

    response = api_client.post(reverse('token_obtain_pair'), TOKEN_CREDENTIALS, format='json')

    assert response.status_code == status.HTTP_200_OK
    token_user.refresh_from_db()
    assert token_user.last_login == last_login


@pytest.mark.django_db
def test_token_obtain_pair_preserves_email_case(api_client):
    user = UserFactory(email='CaseSensitive@example.com', password='StrongTokenPass123!')

    response = api_client.post(reverse('token_obtain_pair'), {
        'email': 'CaseSensitive@example.com', 'password': 'StrongTokenPass123!',
    }, format='json')

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.email == 'CaseSensitive@example.com'
