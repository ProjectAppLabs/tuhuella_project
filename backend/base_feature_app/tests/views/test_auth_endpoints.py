from datetime import timedelta
from unittest.mock import patch

import pytest
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status

from base_feature_app.models import PasswordCode
from base_feature_app.views import auth as auth_views


@pytest.fixture(autouse=True)
def _clear_throttle_cache():
    """Reset DRF throttle counters between tests so rate limits don't leak."""
    cache.clear()
    yield
    cache.clear()


class DummyResponse:
    def __init__(self, status_code=200, payload=None, text=''):
        self.status_code = status_code
        self._payload = payload or {}
        self.text = text

    def json(self):
        return self._payload


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_up_requires_email_and_password(mock_captcha, api_client):
    response = api_client.post(reverse('sign_up'), {}, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'Email and password are required'


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_up_rejects_existing_email(mock_captcha, api_client):
    User = get_user_model()
    User.objects.create_user(email='existing@example.com', password='pass1234')

    response = api_client.post(
        reverse('sign_up'),
        {'email': 'existing@example.com', 'password': 'pass1234', 'terms_accepted': True},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'User with this email already exists'


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_up_creates_user(mock_captcha, api_client):
    """Verifies sign-up creates a new user record and returns an access token on success."""
    response = api_client.post(
        reverse('sign_up'),
        {
            'email': 'new@example.com',
            'password': 'pass1234',
            'first_name': 'New',
            'last_name': 'User',
            'terms_accepted': True,
        },
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert 'access' in response.json()

    User = get_user_model()
    user = User.objects.get(email='new@example.com')
    assert user.first_name == 'New'
    assert user.terms_accepted_at is not None


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_up_rejects_without_terms_accepted(mock_captcha, api_client):
    """sign_up returns 400 when terms_accepted is not provided."""
    response = api_client.post(
        reverse('sign_up'),
        {
            'email': 'noterms@example.com',
            'password': 'pass1234',
            'first_name': 'No',
            'last_name': 'Terms',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'terms' in response.json()['error'].lower()


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_in_requires_fields(mock_captcha, api_client):
    response = api_client.post(reverse('sign_in'), {}, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'Email and password are required'


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_in_rejects_unknown_user(mock_captcha, api_client):
    response = api_client.post(
        reverse('sign_in'),
        {'email': 'missing@example.com', 'password': 'pass1234'},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['error'] == 'Invalid credentials'


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_in_rejects_invalid_password(mock_captcha, api_client):
    User = get_user_model()
    User.objects.create_user(email='user@example.com', password='pass1234')

    response = api_client.post(
        reverse('sign_in'),
        {'email': 'user@example.com', 'password': 'wrong'},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_in_rejects_inactive_user(mock_captcha, api_client):
    User = get_user_model()
    user = User.objects.create_user(email='inactive@example.com', password='pass1234')
    user.is_active = False
    user.save(update_fields=['is_active'])

    response = api_client.post(
        reverse('sign_in'),
        {'email': 'inactive@example.com', 'password': 'pass1234'},
        format='json',
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response.json()['error'] == 'Account is inactive'


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_in_success(mock_captcha, api_client):
    User = get_user_model()
    User.objects.create_user(email='active@example.com', password='pass1234')

    response = api_client.post(
        reverse('sign_in'),
        {'email': 'active@example.com', 'password': 'pass1234'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert 'access' in response.json()


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_in_updates_last_login(mock_captcha, api_client):
    """A successful sign-in must stamp `last_login` on the user."""
    User = get_user_model()
    user = User.objects.create_user(email='lastlogin@example.com', password='pass1234')
    assert user.last_login is None

    response = api_client.post(
        reverse('sign_in'),
        {'email': user.email, 'password': 'pass1234'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.last_login is not None


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_in_rate_limited(mock_captcha, api_client):
    """After exceeding the per-minute quota, sign_in must respond with 429."""
    from base_feature_app.views.auth import SignInThrottle

    original_get_rate = SignInThrottle.get_rate
    SignInThrottle.get_rate = lambda self: '3/minute'
    try:
        User = get_user_model()
        User.objects.create_user(email='brute@example.com', password='pass1234')

        for _ in range(3):
            api_client.post(
                reverse('sign_in'),
                {'email': 'brute@example.com', 'password': 'wrong'},
                format='json',
            )

        response = api_client.post(
            reverse('sign_in'),
            {'email': 'brute@example.com', 'password': 'pass1234'},
            format='json',
        )

        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
    finally:
        SignInThrottle.get_rate = original_get_rate


@pytest.mark.django_db
def test_google_login_requires_credential(api_client):
    response = api_client.post(reverse('google_login'), {}, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'Google credential is required'


@pytest.mark.django_db
@override_settings(DEBUG=False, GOOGLE_OAUTH_CLIENT_ID='')
def test_google_login_invalid_credential_when_not_debug(api_client, monkeypatch):
    """Verifies Google login returns 401 when credential is invalid and the app is not in debug mode."""

    def fake_get(*_args, **_kwargs):
        return DummyResponse(status_code=500)

    monkeypatch.setattr(auth_views.requests, 'get', fake_get)

    response = api_client.post(
        reverse('google_login'),
        {'credential': 'bad-token', 'email': 'user@example.com'},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['error'] == 'Invalid Google credential'


@pytest.mark.django_db
@override_settings(DEBUG=False, GOOGLE_OAUTH_CLIENT_ID='client-1')
def test_google_login_aud_mismatch_returns_error(api_client, monkeypatch):
    """Verifies Google login returns 401 when the token audience does not match the configured client ID."""

    def fake_get(*_args, **_kwargs):
        return DummyResponse(status_code=200, payload={'aud': 'other'})

    monkeypatch.setattr(auth_views.requests, 'get', fake_get)

    response = api_client.post(
        reverse('google_login'),
        {'credential': 'bad-aud', 'email': 'user@example.com'},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response.json()['error'] == 'Invalid Google client'


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_google_login_requires_email_when_payload_missing(api_client, monkeypatch):
    """Verifies Google login returns 400 when the Google API call fails and no fallback email is provided."""

    def fake_get(*_args, **_kwargs):
        raise auth_views.requests.RequestException('fail')

    monkeypatch.setattr(auth_views.requests, 'get', fake_get)

    response = api_client.post(
        reverse('google_login'),
        {'credential': 'token'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'Email is required'


@pytest.mark.django_db
@override_settings(DEBUG=False, GOOGLE_OAUTH_CLIENT_ID='client-1')
def test_google_login_creates_user_with_payload(api_client, monkeypatch):
    """Verifies Google login creates a new user when the token payload contains a valid audience and email."""

    payload = {
        'aud': 'client-1',
        'email': 'google@example.com',
        'given_name': 'Google',
        'family_name': 'User',
        'picture': 'pic',
    }

    def fake_get(*_args, **_kwargs):
        return DummyResponse(status_code=200, payload=payload)

    monkeypatch.setattr(auth_views.requests, 'get', fake_get)

    response = api_client.post(
        reverse('google_login'),
        {'credential': 'token', 'email': 'other@example.com'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data['created'] is True
    assert data['google_validated'] is True

    User = get_user_model()
    user = User.objects.get(email='google@example.com')
    assert user.first_name == 'Google'


@pytest.mark.django_db
@override_settings(DEBUG=False, GOOGLE_OAUTH_CLIENT_ID='client-1')
def test_google_login_updates_existing_user_names(api_client, monkeypatch):
    """Verifies Google login updates the first and last name of an existing user when the payload provides new values."""

    User = get_user_model()
    user = User.objects.create_user(email='existing@example.com', password='pass1234')
    user.first_name = ''
    user.last_name = ''
    user.save(update_fields=['first_name', 'last_name'])

    payload = {
        'aud': 'client-1',
        'email': 'existing@example.com',
        'given_name': 'Given',
        'family_name': 'Name',
    }

    def fake_get(*_args, **_kwargs):
        return DummyResponse(status_code=200, payload=payload)

    monkeypatch.setattr(auth_views.requests, 'get', fake_get)

    response = api_client.post(
        reverse('google_login'),
        {'credential': 'token'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['created'] is False

    user.refresh_from_db()
    assert user.first_name == 'Given'
    assert user.last_name == 'Name'


@pytest.mark.django_db
@override_settings(DEBUG=True)
def test_google_login_allows_debug_without_payload(api_client, monkeypatch):
    """Verifies Google login succeeds in debug mode using the fallback email when the Google API call fails."""

    def fake_get(*_args, **_kwargs):
        return DummyResponse(status_code=500)

    monkeypatch.setattr(auth_views.requests, 'get', fake_get)

    response = api_client.post(
        reverse('google_login'),
        {'credential': 'token', 'email': 'debug@example.com'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['google_validated'] is False


@pytest.mark.django_db
def test_send_passcode_requires_email(api_client):
    response = api_client.post(reverse('send_passcode'), {}, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'Email is required'


@pytest.mark.django_db
def test_send_passcode_returns_generic_message_for_missing_user(api_client):
    response = api_client.post(
        reverse('send_passcode'),
        {'email': 'missing@example.com'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['message'] == 'If the email exists, a code has been sent'
    assert PasswordCode.objects.count() == 0


@pytest.mark.django_db
def test_send_passcode_success(api_client, monkeypatch):
    User = get_user_model()
    user = User.objects.create_user(email='send@example.com', password='pass1234')

    monkeypatch.setattr(auth_views, 'send_password_reset_code', lambda *_args, **_kwargs: True)

    response = api_client.post(
        reverse('send_passcode'),
        {'email': user.email},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert PasswordCode.objects.filter(user=user).count() == 1


@pytest.mark.django_db
def test_send_passcode_failure(api_client, monkeypatch):
    User = get_user_model()
    user = User.objects.create_user(email='fail@example.com', password='pass1234')

    monkeypatch.setattr(auth_views, 'send_password_reset_code', lambda *_args, **_kwargs: False)

    response = api_client.post(
        reverse('send_passcode'),
        {'email': user.email},
        format='json',
    )

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    assert response.json()['error'] == 'Failed to send email'


@pytest.mark.django_db
def test_verify_passcode_requires_fields(api_client):
    response = api_client.post(reverse('verify_passcode_reset'), {}, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'Email, code, and new password are required'


@pytest.mark.django_db
def test_verify_passcode_rejects_invalid_email(api_client):
    response = api_client.post(
        reverse('verify_passcode_reset'),
        {'email': 'missing@example.com', 'code': '123456', 'new_password': 'newpass'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
@freeze_time('2026-01-15 10:00:00')
def test_verify_passcode_rejects_expired_code(api_client):
    """Verifies passcode verification returns 400 when the code was created more than 15 minutes ago."""
    User = get_user_model()
    user = User.objects.create_user(email='expired@example.com', password='pass1234')
    password_code = PasswordCode.objects.create(user=user, code='111111')
    PasswordCode.objects.filter(id=password_code.id).update(
        created_at=timezone.now() - timedelta(minutes=16)
    )

    response = api_client.post(
        reverse('verify_passcode_reset'),
        {'email': user.email, 'code': '111111', 'new_password': 'newpass'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'Invalid or expired code'


@pytest.mark.django_db
def test_verify_passcode_handles_exception(api_client, monkeypatch):
    """Verifies passcode verification returns 400 when an unexpected exception occurs during code validation."""
    User = get_user_model()
    user = User.objects.create_user(email='boom@example.com', password='pass1234')
    PasswordCode.objects.create(user=user, code='222222')

    def boom(_self):
        raise Exception('boom')

    monkeypatch.setattr(PasswordCode, 'is_valid', boom)

    response = api_client.post(
        reverse('verify_passcode_reset'),
        {'email': user.email, 'code': '222222', 'new_password': 'newpass'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'Invalid or expired code'


@pytest.mark.django_db
def test_verify_passcode_resets_password(api_client):
    """Verifies passcode verification resets the user password and marks the code as used on success."""
    User = get_user_model()
    user = User.objects.create_user(email='reset@example.com', password='pass1234')
    password_code = PasswordCode.objects.create(user=user, code='333333')

    response = api_client.post(
        reverse('verify_passcode_reset'),
        {'email': user.email, 'code': '333333', 'new_password': 'NewStrongPass123'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    password_code.refresh_from_db()
    user.refresh_from_db()

    assert password_code.used is True
    assert user.check_password('NewStrongPass123') is True


@pytest.mark.django_db
def test_verify_passcode_rejects_weak_password(api_client):
    """Password reset must fail with 400 when the new password is below the
    project's AUTH_PASSWORD_VALIDATORS (e.g. < 8 chars), even with a valid code."""
    User = get_user_model()
    user = User.objects.create_user(email='weak@example.com', password='pass1234')
    PasswordCode.objects.create(user=user, code='444444')

    response = api_client.post(
        reverse('verify_passcode_reset'),
        {'email': user.email, 'code': '444444', 'new_password': 'short'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    body = response.json()
    assert body['error'] == 'Password does not meet requirements'
    assert isinstance(body.get('details'), list) and body['details']
    user.refresh_from_db()
    assert user.check_password('pass1234') is True


@pytest.mark.django_db
def test_send_passcode_passes_locale_to_email_helper(api_client, monkeypatch):
    """send_passcode must forward the requested locale down to send_password_reset_code."""
    User = get_user_model()
    user = User.objects.create_user(email='locale@example.com', password='pass1234')

    captured = {}

    def fake_send(user_arg, code_arg, locale='es'):
        captured['user'] = user_arg
        captured['code'] = code_arg
        captured['locale'] = locale
        return True

    monkeypatch.setattr(auth_views, 'send_password_reset_code', fake_send)

    response = api_client.post(
        reverse('send_passcode'),
        {'email': user.email, 'locale': 'en'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert captured['locale'] == 'en'
    assert captured['user'] == user


@pytest.mark.django_db
def test_update_password_requires_fields(api_client):
    User = get_user_model()
    user = User.objects.create_user(email='update-fields@example.com', password='pass1234')
    api_client.force_authenticate(user=user)

    response = api_client.post(reverse('update_password'), {}, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'Current password and new password are required'


@pytest.mark.django_db
def test_update_password_rejects_wrong_current(api_client):
    User = get_user_model()
    user = User.objects.create_user(email='update@example.com', password='pass1234')

    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse('update_password'),
        {'current_password': 'wrong', 'new_password': 'newpass'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'Current password is incorrect'


@pytest.mark.django_db
def test_update_password_success(api_client):
    """Verifies update-password endpoint successfully changes the user password when the current password is correct."""
    User = get_user_model()
    user = User.objects.create_user(email='update2@example.com', password='pass1234')

    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse('update_password'),
        {'current_password': 'pass1234', 'new_password': 'DifferentStrongPass123!'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    user.refresh_from_db()
    assert user.check_password('DifferentStrongPass123!') is True


@pytest.mark.django_db
def test_validate_token_requires_auth(api_client):
    response = api_client.get(reverse('validate_token'))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_validate_token_success(api_client):
    User = get_user_model()
    user = User.objects.create_user(email='token@example.com', password='pass1234')

    api_client.force_authenticate(user=user)
    response = api_client.get(reverse('validate_token'))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['valid'] is True


@override_settings(DEBUG=False, RECAPTCHA_SECRET_KEY='test-secret')
def test_verify_recaptcha_returns_false_when_no_token():
    """verify_recaptcha returns False when token is empty and DEBUG is False."""
    result = auth_views.verify_recaptcha('')

    assert result is False


@override_settings(DEBUG=False, RECAPTCHA_SECRET_KEY='test-secret')
def test_verify_recaptcha_calls_google_api(monkeypatch):
    """verify_recaptcha posts to Google reCAPTCHA API and returns the success value."""
    def fake_post(*_args, **_kwargs):
        return DummyResponse(status_code=200, payload={'success': True})

    monkeypatch.setattr(auth_views.requests, 'post', fake_post)

    result = auth_views.verify_recaptcha('valid-token')

    assert result is True


@override_settings(DEBUG=False, RECAPTCHA_SECRET_KEY='test-secret')
def test_verify_recaptcha_returns_false_on_exception(monkeypatch):
    """verify_recaptcha returns False when requests.post raises an exception."""
    def boom(*_args, **_kwargs):
        raise auth_views.requests.RequestException('fail')

    monkeypatch.setattr(auth_views.requests, 'post', boom)

    result = auth_views.verify_recaptcha('some-token')

    assert result is False


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_sign_up_rejects_failed_captcha(api_client, monkeypatch):
    """sign_up returns 400 when captcha verification fails."""
    monkeypatch.setattr(auth_views, 'verify_recaptcha', lambda _token: False)

    response = api_client.post(
        reverse('sign_up'),
        {'email': 'new@example.com', 'password': 'pass1234', 'captcha_token': 'bad'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'error' in response.json()


@pytest.mark.django_db
@patch('base_feature_app.views.auth.verify_recaptcha', return_value=True)
def test_sign_up_rejects_short_password(mock_captcha, api_client):
    """sign_up returns 400 when password is shorter than 8 characters."""
    response = api_client.post(
        reverse('sign_up'),
        {'email': 'short@example.com', 'password': 'short'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'Password must be at least 8 characters'


@pytest.mark.django_db
@override_settings(DEBUG=False)
def test_sign_in_rejects_failed_captcha(api_client, monkeypatch):
    """sign_in returns 400 when captcha verification fails."""
    monkeypatch.setattr(auth_views, 'verify_recaptcha', lambda _token: False)

    response = api_client.post(
        reverse('sign_in'),
        {'email': 'user@example.com', 'password': 'pass1234', 'captcha_token': 'bad'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert 'error' in response.json()


@pytest.mark.django_db
@pytest.mark.parametrize('new_password', ['x', 'password', '123456789', 'password-owner@example.com'])
def test_update_password_rejects_weak_password(api_client, new_password):
    """Rejected passwords preserve the user's existing credentials."""
    User = get_user_model()
    original = 'OriginalStrongPass123!'
    user = User.objects.create_user(email='password-owner@example.com', password=original)
    api_client.force_authenticate(user=user)

    response = api_client.post(
        reverse('update_password'),
        {'current_password': original, 'new_password': new_password},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['error'] == 'Password does not meet requirements'
    user.refresh_from_db()
    assert user.check_password(original) is True
