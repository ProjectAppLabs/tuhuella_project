"""Verify notification channel preferences and delivery states."""

from concurrent.futures import ThreadPoolExecutor
from unittest.mock import call, patch

import pytest
from django.db import connections, transaction

from base_feature_app.models import NotificationLog, NotificationPreference
from base_feature_app.services.notification_service import dispatch_notification
from base_feature_app.tasks import send_email_notification
from base_feature_app.tests.factories import NotificationPreferenceFactory, UserFactory


def _deliver_email_in_worker(log_id):
    """Deliver through a separate database connection without Redis."""
    try:
        send_email_notification.call_local(log_id)
    finally:
        connections.close_all()


def _publish_to_local_worker(log_id):
    """Model a queue consumer without sending SMTP traffic."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        executor.submit(_deliver_email_in_worker, log_id).result(timeout=5)


def _roll_back_notification(event_key, recipient):
    """Abort a real notification transaction at the caller's savepoint."""
    with transaction.atomic():
        dispatch_notification(event_key, recipient, {})
        raise RuntimeError('roll back notification')


@pytest.mark.django_db
def test_dispatch_notification_defaults_to_standard_channels():
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
def test_dispatch_notification_schedules_email_task(django_capture_on_commit_callbacks):
    """Schedule the email task for its persisted notification."""
    user = UserFactory()
    with (
        patch('base_feature_app.tasks.send_email_notification') as mock_task,
        django_capture_on_commit_callbacks(execute=True),
    ):
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
def test_dispatch_notification_task_failure_marks_email_failed(django_capture_on_commit_callbacks):
    """Persist an undelivered failure when the queue rejects the email task."""
    user = UserFactory()

    with (
        patch('base_feature_app.tasks.send_email_notification', side_effect=ConnectionError('queue unavailable')),
        django_capture_on_commit_callbacks(execute=True),
    ):
        dispatch_notification('adoption_submitted', user, {})

    log = NotificationLog.objects.get(recipient=user, channel='email')
    assert log.status == NotificationLog.Status.FAILED
    assert log.sent_at is None


@pytest.mark.django_db
def test_dispatch_notification_task_failure_preserves_in_app_delivery(django_capture_on_commit_callbacks):
    """Deliver the internal notification even when email scheduling fails."""
    user = UserFactory()

    with (
        patch('base_feature_app.tasks.send_email_notification', side_effect=ConnectionError('queue unavailable')),
        django_capture_on_commit_callbacks(execute=True),
    ):
        dispatch_notification('adoption_submitted', user, {})

    log = NotificationLog.objects.get(recipient=user, channel='in_app')
    assert log.status == NotificationLog.Status.SENT


@pytest.mark.django_db(transaction=True)
def test_dispatch_notification_waits_for_commit():
    """Do not publish an email while its database transaction is pending."""
    user = UserFactory()

    with patch('base_feature_app.tasks.send_email_notification') as queue:
        with transaction.atomic():
            dispatch_notification('adoption_submitted', user, {})
            log = NotificationLog.objects.get(recipient=user, channel='email')
            assert log.status == NotificationLog.Status.QUEUED
            queue.assert_not_called()

        queue.assert_called_once_with(log.pk)


@pytest.mark.django_db(transaction=True)
def test_dispatch_notification_discards_rolled_back_delivery():
    """A rolled-back notification never reaches the queue."""
    user = UserFactory()

    with patch('base_feature_app.tasks.send_email_notification') as queue:
        with pytest.raises(RuntimeError, match='roll back notification'):
            _roll_back_notification('adoption_submitted', user)

        queue.assert_not_called()
    assert not NotificationLog.objects.filter(recipient=user).exists()


@pytest.mark.django_db(transaction=True)
def test_dispatch_notification_discards_rolled_back_savepoint():
    """Rolling back a savepoint publishes only the outer notification."""
    user = UserFactory()

    with patch('base_feature_app.tasks.send_email_notification') as queue:
        with transaction.atomic():
            dispatch_notification('adoption_submitted', user, {})
            outer_log = NotificationLog.objects.get(recipient=user, channel='email')
            with pytest.raises(RuntimeError, match='roll back notification'):
                _roll_back_notification('donation_paid', user)

        queue.assert_called_once_with(outer_log.pk)
    assert not NotificationLog.objects.filter(recipient=user, event_key='donation_paid').exists()


@pytest.mark.django_db(transaction=True)
def test_dispatch_notification_publishes_distinct_email_ids():
    """Each queued email retains the ID belonging to its own recipient."""
    first_user = UserFactory()
    second_user = UserFactory()

    with patch('base_feature_app.tasks.send_email_notification') as queue:
        with transaction.atomic():
            dispatch_notification('adoption_submitted', first_user, {})
            dispatch_notification('adoption_submitted', second_user, {})
            first_log = NotificationLog.objects.get(recipient=first_user, channel='email')
            second_log = NotificationLog.objects.get(recipient=second_user, channel='email')

        assert queue.call_args_list == [call(first_log.pk), call(second_log.pk)]


@pytest.mark.django_db(transaction=True)
def test_dispatch_notification_queue_rejection_preserves_commit():
    """A post-commit queue failure leaves the business change confirmed."""
    user = UserFactory(city='Original city')

    with patch('base_feature_app.tasks.send_email_notification', side_effect=ConnectionError('queue unavailable')):
        with transaction.atomic():
            user.city = 'Committed city'
            user.save(update_fields=['city'])
            dispatch_notification('adoption_submitted', user, {})

    user.refresh_from_db()
    log = NotificationLog.objects.get(recipient=user, channel='email')
    assert user.city == 'Committed city'
    assert log.status == NotificationLog.Status.FAILED
    assert log.sent_at is None


@pytest.mark.django_db(transaction=True)
def test_dispatch_notification_publishes_from_autocommit():
    """Outside a transaction the committed email is published immediately."""
    user = UserFactory()

    with patch('base_feature_app.tasks.send_email_notification') as queue:
        dispatch_notification('adoption_submitted', user, {})
        log = NotificationLog.objects.get(recipient=user, channel='email')

        queue.assert_called_once_with(log.pk)
    assert log.status == NotificationLog.Status.QUEUED


@pytest.mark.django_db(transaction=True)
def test_dispatch_notification_worker_receives_committed_log():
    """A separate worker connection can deliver the confirmed notification."""
    user = UserFactory()
    context = {
        'user_name': 'Ana', 'animal_name': 'Luna',
        'shelter_name': 'Sandbox', 'link': '/my-applications',
    }

    with (
        patch('base_feature_app.tasks.send_email_notification', side_effect=_publish_to_local_worker),
        patch('base_feature_app.tasks.send_mail', return_value=1) as transport,
    ):
        with transaction.atomic():
            dispatch_notification('adoption_submitted', user, context)

    log = NotificationLog.objects.get(recipient=user, channel='email')
    assert log.status == NotificationLog.Status.SENT
    assert log.sent_at is not None
    transport.assert_called_once()
