"""Verify SMTP wait limits through configuration and real delivery paths."""

from pathlib import Path
import subprocess
import sys
from unittest.mock import ANY, MagicMock, patch

from django.core.mail import get_connection
from django.urls import reverse
import pytest

from base_feature_app.models import NotificationLog
from base_feature_app.tasks import send_email_notification
from base_feature_app.tests.factories import NotificationLogFactory


SETTINGS_IMPORT = """
import os
import sys
import decouple

sys.path.insert(0, sys.argv[1])
# Exercise real settings without consulting the worktree's linked .env.
decouple.config = decouple.Config(decouple.RepositoryEnv(os.devnull))
from base_feature_project import settings_dev
print(settings_dev.EMAIL_TIMEOUT)
"""


def load_settings(tmp_path, timeout_env):
    """Import real settings in a fresh interpreter with only controlled env."""
    backend_path = Path(__file__).resolve().parents[3]
    environment = {'DJANGO_ENV': 'development', **timeout_env}
    return subprocess.run(
        [sys.executable, '-c', SETTINGS_IMPORT, str(backend_path)],
        cwd=tmp_path,
        env=environment,
        capture_output=True,
        text=True,
        timeout=15,
        check=False,
    )


@pytest.fixture
def smtp_settings(settings):
    """Use SMTP with harmless addresses while preserving its configured timeout."""
    settings.EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    settings.EMAIL_HOST = 'smtp.example.test'
    settings.EMAIL_PORT = 25
    settings.EMAIL_USE_TLS = False
    settings.EMAIL_USE_SSL = False
    settings.EMAIL_HOST_USER = ''
    settings.EMAIL_HOST_PASSWORD = ''
    settings.DEFAULT_FROM_EMAIL = 'sender@example.test'
    settings.CONTACT_FORM_RECIPIENT_EMAIL = 'team@example.test'
    return settings


def test_email_timeout_defaults_to_five_seconds(tmp_path):
    """An absent timeout gives the SMTP backend a five-second wait limit."""
    result = load_settings(tmp_path, {})

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == '5'


def test_email_timeout_accepts_positive_integer(tmp_path):
    """A positive integer environment value replaces the default wait limit."""
    result = load_settings(tmp_path, {'DJANGO_EMAIL_TIMEOUT': '9'})

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == '9'


@pytest.mark.parametrize('timeout_value', ['0', '-1', 'abc', '1.5', ''])
def test_email_timeout_rejects_invalid_configuration(tmp_path, timeout_value):
    """Invalid wait limits stop configuration instead of permitting endless I/O."""
    result = load_settings(tmp_path, {'DJANGO_EMAIL_TIMEOUT': timeout_value})

    assert result.returncode != 0
    assert 'ImproperlyConfigured' in result.stderr
    assert 'DJANGO_EMAIL_TIMEOUT must be a positive integer.' in result.stderr


def test_smtp_connection_receives_configured_timeout(smtp_settings):
    """Django passes the configured wait limit to the real SMTP boundary."""
    smtp_settings.EMAIL_TIMEOUT = 9
    smtp_connection = MagicMock()
    backend = get_connection()

    with patch('django.core.mail.backends.smtp.smtplib.SMTP', return_value=smtp_connection) as smtp:
        opened = backend.open()

    assert opened is True
    smtp.assert_called_once_with(
        'smtp.example.test', 25, local_hostname=ANY, timeout=9,
    )


@pytest.mark.django_db
def test_contact_timeout_returns_service_unavailable(api_client, smtp_settings):
    """An SMTP timeout returns a contact failure after one transport attempt."""
    payload = {
        'name': 'Maria Garcia',
        'email': 'maria@example.test',
        'subject': 'Pregunta sobre adopcion',
        'message': 'Hola, me gustaria saber mas sobre el proceso.',
    }

    with patch(
        'django.core.mail.backends.smtp.smtplib.SMTP',
        side_effect=TimeoutError('SMTP timeout'),
    ) as smtp:
        response = api_client.post(reverse('contact-form-submit'), payload, format='json')

    assert response.status_code == 503
    assert response.json()['message'] == 'Could not send your message. Please try again later.'
    smtp.assert_called_once_with(
        'smtp.example.test', 25, local_hostname=ANY, timeout=5,
    )


@pytest.mark.django_db
def test_notification_timeout_marks_delivery_failed(smtp_settings):
    """An SMTP timeout persists an undelivered notification without retrying."""
    log = NotificationLogFactory(
        event_key='adoption_submitted', status=NotificationLog.Status.QUEUED,
        channel='email', sent_at=None,
        metadata={
            'user_name': 'Ana', 'animal_name': 'Luna',
            'shelter_name': 'Refugio', 'link': '/shelter/applications',
        },
    )

    with patch(
        'django.core.mail.backends.smtp.smtplib.SMTP',
        side_effect=TimeoutError('SMTP timeout'),
    ) as smtp:
        send_email_notification.call_local(log.pk)
    log.refresh_from_db()

    assert log.status == NotificationLog.Status.FAILED
    assert log.sent_at is None
    smtp.assert_called_once_with(
        'smtp.example.test', 25, local_hostname=ANY, timeout=5,
    )
