"""Verify notification channel preferences and delivery states."""

from unittest.mock import patch

import pytest

from base_feature_app.models import NotificationLog, NotificationPreference
from base_feature_app.services.notification_service import dispatch_notification
from base_feature_app.tests.factories import NotificationPreferenceFactory, UserFactory


@pytest.mark.django_db
def test_dispatch_notification_defaults_to_email_and_in_app_when_no_prefs():
    """Use the default channels when no preferences exist."""
    user = UserFactory()
    dispatch_notification('adoption_submitted', user, {'user_name': 'Ana'})
    logs = NotificationLog.objects.filter(recipient=user, event_key='adoption_submitted')
    channels = set(logs.values_list('channel', flat=True))
    assert channels == {'email', 'in_app'}


@pytest.mark.django_db
def test_dispatch_notification_creates_queued_email_log():
    """Keep an accepted email task queued until delivery."""
    user = UserFactory()
    with patch('base_feature_app.tasks.send_email_notification'):
        dispatch_notification('adoption_submitted', user, {})
    log = NotificationLog.objects.get(recipient=user, channel='email')
    assert log.status == NotificationLog.Status.QUEUED


@pytest.mark.django_db
def test_dispatch_notification_sets_in_app_log_to_sent():
    """Make an enabled internal notification immediately available."""
    user = UserFactory()
    with patch('base_feature_app.tasks.send_email_notification'):
        dispatch_notification('adoption_submitted', user, {})
    log = NotificationLog.objects.get(recipient=user, channel='in_app')
    assert log.status == NotificationLog.Status.SENT


@pytest.mark.django_db
def test_dispatch_notification_schedules_email_task():
    """Schedule the email task for its persisted notification."""
    user = UserFactory()
    with patch('base_feature_app.tasks.send_email_notification') as mock_task:
        dispatch_notification('adoption_submitted', user, {})
    log = NotificationLog.objects.get(recipient=user, channel='email')
    assert log.status == NotificationLog.Status.QUEUED
    mock_task.assert_called_once_with(log.pk)


@pytest.mark.django_db
def test_dispatch_notification_respects_email_disabled_pref():
    """Omit email notifications when the recipient disables them."""
    user = UserFactory()
    NotificationPreferenceFactory(
        user=user, event_key='adoption_submitted',
        channel=NotificationPreference.Channel.EMAIL, enabled=False,
    )
    dispatch_notification('adoption_submitted', user, {})
    assert not NotificationLog.objects.filter(recipient=user, channel='email').exists()


@pytest.mark.django_db
def test_dispatch_notification_respects_in_app_enabled_pref():
    """Deliver the recipient's enabled internal channel."""
    user = UserFactory()
    NotificationPreferenceFactory(
        user=user, event_key='adoption_submitted',
        channel=NotificationPreference.Channel.IN_APP, enabled=True,
    )
    dispatch_notification('adoption_submitted', user, {})
    log = NotificationLog.objects.get(recipient=user, channel='in_app')
    assert log.status == NotificationLog.Status.SENT


@pytest.mark.django_db
def test_dispatch_notification_skips_disabled_channels():
    """Create no notifications when all selected channels are disabled."""
    user = UserFactory()
    NotificationPreferenceFactory(
        user=user, event_key='adoption_submitted',
        channel=NotificationPreference.Channel.EMAIL, enabled=False,
    )
    NotificationPreferenceFactory(
        user=user, event_key='adoption_submitted',
        channel=NotificationPreference.Channel.IN_APP, enabled=False,
    )
    dispatch_notification('adoption_submitted', user, {})
    assert not NotificationLog.objects.filter(recipient=user).exists()


@pytest.mark.django_db
def test_dispatch_notification_task_failure_marks_email_failed():
    """Persist an undelivered failure when the queue rejects the email task."""
    user = UserFactory()

    with patch('base_feature_app.tasks.send_email_notification', side_effect=ConnectionError('queue unavailable')):
        dispatch_notification('adoption_submitted', user, {})

    log = NotificationLog.objects.get(recipient=user, channel='email')
    assert log.status == NotificationLog.Status.FAILED
    assert log.sent_at is None


@pytest.mark.django_db
def test_dispatch_notification_task_failure_preserves_in_app_delivery():
    """Deliver the internal notification even when email scheduling fails."""
    user = UserFactory()

    with patch('base_feature_app.tasks.send_email_notification', side_effect=ConnectionError('queue unavailable')):
        dispatch_notification('adoption_submitted', user, {})

    log = NotificationLog.objects.get(recipient=user, channel='in_app')
    assert log.status == NotificationLog.Status.SENT
