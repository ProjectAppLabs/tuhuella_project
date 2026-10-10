"""Exercise password revocations through the public JWT endpoints."""

from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import OperationalError
from django.urls import reverse
from requests import Response as GoogleResponse
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

from base_feature_app.models import PasswordCode
from base_feature_app.utils.auth_utils import generate_auth_tokens

OLD_PASSWORD = 'OriginalCredentials123!'
NEW_PASSWORD = 'ReplacementCredentials456!'

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def isolate_auth_settings(settings):
    settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']
    settings.RECAPTCHA_SECRET_KEY = ''
    settings.GOOGLE_OAUTH_CLIENT_ID = 'test-client'
    settings.DEBUG = False
    cache.clear()
    yield
    cache.clear()


@pytest.fixture
def user():
    return get_user_model().objects.create_user(
        email='revoked@example.test', password=OLD_PASSWORD,
    )


@pytest.fixture
def current_tokens(user):
    return generate_auth_tokens(user)


@pytest.fixture
def legacy_refresh(user):
    return RefreshToken.for_user(user)


@pytest.fixture
def authenticated_snapshot(user):
    return get_user_model().objects.get(pk=user.pk)


@pytest.fixture
def other_tokens():
    other = get_user_model().objects.create_user(
        email='unaffected@example.test', password=OLD_PASSWORD,
    )
    return generate_auth_tokens(other)


@pytest.fixture(params=[
    ('update_password', 'Password updated successfully'),
    ('verify_passcode_and_reset_password', 'Password reset successfully'),
], ids=['change-password', 'reset-password'])
def password_operation(
    request, api_client, user, current_tokens, legacy_refresh,
    authenticated_snapshot, other_tokens,
):
    endpoint, message = request.param
    PasswordCode.objects.create(user=user, code='123456')
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {current_tokens['access']}")
    response = api_client.post(reverse(endpoint), {
        'email': user.email,
        'code': '123456',
        'current_password': OLD_PASSWORD,
        'new_password': NEW_PASSWORD,
    }, format='json')
    assert response.status_code == 200
    return response, message


def test_password_operation_preserves_success_response(password_operation):
    """Keep the established message for each password operation."""
    response, message = password_operation

    assert response.json() == {'message': message}


def test_password_operation_revokes_prior_access(api_client, current_tokens, password_operation):
    """Reject an access token issued before the password operation."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {current_tokens['access']}")

    response = api_client.get(reverse('validate_token'))

    assert response.status_code == 401
    assert response.json()['code'] == 'token_not_valid'


def test_password_operation_revokes_prior_refresh(api_client, current_tokens, password_operation):
    """Prevent an earlier refresh token from obtaining fresh access."""
    response = api_client.post(
        reverse('token_refresh'), {'refresh': current_tokens['refresh']}, format='json',
    )

    assert response.status_code == 401
    assert response.json()['code'] == 'token_not_valid'


def test_password_operation_revokes_legacy_access(api_client, legacy_refresh, password_operation):
    """Reject unversioned access after the account leaves generation zero."""
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {legacy_refresh.access_token}')

    response = api_client.get(reverse('validate_token'))

    assert response.status_code == 401


def test_password_operation_revokes_legacy_refresh(api_client, legacy_refresh, password_operation):
    """Reject unversioned refresh after the account leaves generation zero."""
    response = api_client.post(
        reverse('token_refresh'), {'refresh': str(legacy_refresh)}, format='json',
    )

    assert response.status_code == 401


def test_password_operation_preserves_other_access(api_client, other_tokens, password_operation):
    """Keep another account's existing access session usable."""
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {other_tokens['access']}")

    response = api_client.get(reverse('validate_token'))

    assert response.status_code == 200
    assert response.json()['user']['email'] == 'unaffected@example.test'


def test_password_operation_preserves_other_refresh(api_client, other_tokens, password_operation):
    """Keep another account's refresh session usable."""
    response = api_client.post(
        reverse('token_refresh'), {'refresh': other_tokens['refresh']}, format='json',
    )

    assert response.status_code == 200
    assert AccessToken(response.json()['access'])['auth_version'] == 0


def test_password_operation_advances_account_generation(user, password_operation):
    """Persist the replacement password in the next generation."""
    user.refresh_from_db()

    assert user.auth_version == 1
    assert user.check_password(NEW_PASSWORD)


def test_password_operation_accepts_new_credentials(api_client, user, password_operation):
    """Allow fresh authentication despite the previous Bearer header."""
    response = api_client.post(reverse('sign_in'), {
        'email': user.email, 'password': NEW_PASSWORD,
    }, format='json')

    assert response.status_code == 200
    assert AccessToken(response.json()['access'])['auth_version'] == 1
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}")
    assert api_client.get(reverse('validate_token')).status_code == 200


def test_password_operation_rejects_previous_credentials(api_client, user, password_operation):
    """Deny authentication with the previous password."""
    response = api_client.post(reverse('sign_in'), {
        'email': user.email, 'password': OLD_PASSWORD,
    }, format='json')

    assert response.status_code == 401
    assert response.json() == {'error': 'Invalid credentials'}


def test_password_operation_allows_fresh_refresh(api_client, user, password_operation):
    """Renew a fresh login using the new credential generation."""
    login = api_client.post(reverse('sign_in'), {
        'email': user.email, 'password': NEW_PASSWORD,
    }, format='json')
    assert login.status_code == 200

    response = api_client.post(
        reverse('token_refresh'), {'refresh': login.json()['refresh']}, format='json',
    )

    assert response.status_code == 200
    assert AccessToken(response.json()['access'])['auth_version'] == 1
    assert RefreshToken(response.json()['refresh'])['auth_version'] == 1


def test_late_token_emission_keeps_authenticated_generation(
    api_client, authenticated_snapshot, password_operation,
):
    """Do not promote a login snapshot captured before revocation."""
    tokens = generate_auth_tokens(authenticated_snapshot)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    response = api_client.get(reverse('validate_token'))

    assert response.status_code == 401
    assert RefreshToken(tokens['refresh'])['auth_version'] == 0


def test_legacy_access_remains_usable_before_revocation(api_client, legacy_refresh):
    """Preserve sessions issued before deployment for untouched accounts."""
    api_client.credentials(HTTP_AUTHORIZATION=f'Bearer {legacy_refresh.access_token}')

    response = api_client.get(reverse('validate_token'))

    assert response.status_code == 200
    assert response.json()['user']['email'] == 'revoked@example.test'


def test_legacy_refresh_keeps_legacy_generation(api_client, legacy_refresh):
    """Renew a legacy session without promoting its credential generation."""
    response = api_client.post(
        reverse('token_refresh'), {'refresh': str(legacy_refresh)}, format='json',
    )

    assert response.status_code == 200
    assert AccessToken(response.json()['access']).get('auth_version', 0) == 0
    assert RefreshToken(response.json()['refresh']).get('auth_version', 0) == 0
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {response.json()['access']}")
    assert api_client.get(reverse('validate_token')).status_code == 200


@pytest.mark.parametrize('endpoint', ['sign_in', 'token_obtain_pair'])
def test_password_login_ignores_revoked_bearer(api_client, user, current_tokens, endpoint):
    """Issue the current generation when the credential login succeeds."""
    get_user_model().objects.filter(pk=user.pk).update(auth_version=3)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {current_tokens['access']}")

    response = api_client.post(reverse(endpoint), {
        'email': user.email, 'password': OLD_PASSWORD,
    }, format='json')

    assert response.status_code == 200
    assert AccessToken(response.json()['access'])['auth_version'] == 3
    assert RefreshToken(response.json()['refresh'])['auth_version'] == 3


def test_google_login_ignores_revoked_bearer(api_client, user, current_tokens):
    """Let validated Google credentials start a new account session."""
    get_user_model().objects.filter(pk=user.pk).update(auth_version=3)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {current_tokens['access']}")
    google_response = GoogleResponse()
    google_response.status_code = 200
    google_response._content = (
        b'{"aud":"test-client","email":"revoked@example.test","given_name":"Test"}'
    )

    with patch('base_feature_app.views.auth.requests.get', return_value=google_response):
        response = api_client.post(reverse('google_login'), {
            'credential': 'synthetic-google-credential',
        }, format='json')

    assert response.status_code == 200
    assert AccessToken(response.json()['access'])['auth_version'] == 3
    assert RefreshToken(response.json()['refresh'])['auth_version'] == 3


def test_admin_login_as_issues_current_generation(api_client, user):
    """Bind administrator-issued sessions to the target account generation."""
    admin = get_user_model().objects.create_superuser(
        email='admin@example.test', password=OLD_PASSWORD,
    )
    get_user_model().objects.filter(pk=user.pk).update(auth_version=3)
    api_client.force_login(admin)

    response = api_client.get(reverse('myadmin:base_feature_app_user_login_as', args=[user.pk]))

    assert response.status_code == 302
    tokens = parse_qs(urlsplit(response['Location']).query)
    assert AccessToken(tokens['access'][0])['auth_version'] == 3
    assert RefreshToken(tokens['refresh'][0])['auth_version'] == 3


def test_sign_up_issues_initial_generation(api_client):
    """Bind a newly registered account's session to generation zero."""
    response = api_client.post(reverse('sign_up'), {
        'email': 'registered@example.test',
        'password': OLD_PASSWORD,
        'terms_accepted': True,
    }, format='json')

    assert response.status_code == 201
    assert AccessToken(response.json()['access'])['auth_version'] == 0
    assert RefreshToken(response.json()['refresh'])['auth_version'] == 0


def test_reset_rolls_back_revocation_on_code_write_failure(api_client, user):
    """Roll back credentials when consuming the reset code cannot persist."""
    code = PasswordCode.objects.create(user=user, code='123456')
    password_hash = user.password

    with patch.object(PasswordCode, 'save', side_effect=OperationalError('database write failure')):
        with pytest.raises(OperationalError):
            api_client.post(reverse('verify_passcode_and_reset_password'), {
                'email': user.email, 'code': code.code, 'new_password': NEW_PASSWORD,
            }, format='json')

    user.refresh_from_db()
    code.refresh_from_db()
    assert user.password == password_hash
    assert user.auth_version == 0
    assert code.used is False
