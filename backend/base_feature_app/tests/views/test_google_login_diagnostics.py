"""Keep Google credentials out of logs for upstream validation failures."""

from unittest.mock import patch

import pytest
import requests
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.urls import reverse
from requests import Response as GoogleResponse

pytestmark = pytest.mark.django_db
LOGGER = 'base_feature_app.views.auth'
CREDENTIAL = 'synthetic-private-google-credential'
URL = 'https://oauth2.googleapis.com/tokeninfo'
UPSTREAM_BODY = 'synthetic-private-upstream-body'


@pytest.fixture(autouse=True)
def production_google_settings(settings):
    settings.DEBUG = False
    settings.GOOGLE_OAUTH_CLIENT_ID = 'test-client'
    cache.clear()
    yield
    cache.clear()


@pytest.mark.parametrize('failure_type', [requests.ConnectionError, requests.Timeout, ValueError])
def test_google_validation_logs_only_exception_type(api_client, caplog, failure_type):
    """Reject upstream failures without logging their sensitive messages."""
    failure = failure_type(
        f'{URL}?id_token={CREDENTIAL} {UPSTREAM_BODY}',
    )

    with caplog.at_level('WARNING', logger=LOGGER):
        with patch('base_feature_app.views.auth.requests.get', side_effect=failure):
            response = api_client.post(reverse('google_login'), {
                'credential': CREDENTIAL, 'email': 'blocked@example.test',
            }, format='json')

    assert response.status_code == 401
    assert response.json() == {'error': 'Invalid Google credential'}
    assert get_user_model().objects.filter(email='blocked@example.test').exists() is False
    assert f'Google token validation failed: type={failure_type.__name__}' in caplog.messages
    assert all(secret not in caplog.text for secret in (CREDENTIAL, URL, UPSTREAM_BODY))
    assert all(record.exc_info is None for record in caplog.records)
    assert all(record.stack_info is None for record in caplog.records)


def test_google_validation_omits_rejected_response_body(api_client, caplog):
    """Omit private upstream bodies when Google rejects validation."""
    upstream = GoogleResponse()
    upstream.status_code = 400
    upstream._content = f'{UPSTREAM_BODY} {CREDENTIAL} {URL}'.encode()

    with caplog.at_level('WARNING', logger=LOGGER):
        with patch('base_feature_app.views.auth.requests.get', return_value=upstream):
            response = api_client.post(reverse('google_login'), {
                'credential': CREDENTIAL, 'email': 'blocked@example.test',
            }, format='json')

    assert response.status_code == 401
    assert get_user_model().objects.filter(email='blocked@example.test').exists() is False
    assert 'Google token validation failed: type=UpstreamRejection' in caplog.messages
    assert all(secret not in caplog.text for secret in (CREDENTIAL, URL, UPSTREAM_BODY))
    assert all(record.exc_info is None for record in caplog.records)
    assert all(record.stack_info is None for record in caplog.records)


def test_google_validation_omits_untrusted_audience(api_client, caplog):
    """Omit an untrusted audience value while denying its credential."""
    upstream = GoogleResponse()
    upstream.status_code = 200
    upstream._content = (
        f'{{"aud":"{CREDENTIAL} {URL} {UPSTREAM_BODY}","email":"blocked@example.test"}}'.encode()
    )

    with caplog.at_level('WARNING', logger=LOGGER):
        with patch('base_feature_app.views.auth.requests.get', return_value=upstream):
            response = api_client.post(reverse('google_login'), {
                'credential': CREDENTIAL,
            }, format='json')

    assert response.status_code == 401
    assert response.json() == {'error': 'Invalid Google client'}
    assert get_user_model().objects.filter(email='blocked@example.test').exists() is False
    assert 'Google token validation failed: type=AudienceMismatch' in caplog.messages
    assert all(secret not in caplog.text for secret in (CREDENTIAL, URL, UPSTREAM_BODY))
    assert all(record.exc_info is None for record in caplog.records)
    assert all(record.stack_info is None for record in caplog.records)
