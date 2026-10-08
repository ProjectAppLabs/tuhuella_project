"""
Notification dispatcher service.

Dispatches notifications to users based on their preferences,
creating NotificationLog entries and scheduling async tasks for email delivery.
"""

import logging

from base_feature_app.models import NotificationPreference, NotificationLog

logger = logging.getLogger(__name__)


def dispatch_notification(event_key: str, recipient, context: dict):
    """
    Dispatch a notification for a given event to a recipient.

    Checks the user's NotificationPreference for each channel.
    If no preferences exist, defaults to email + in_app enabled.

    Args:
        event_key: One of the 12 defined event keys.
        recipient: User instance to receive the notification.
        context: Dict with template variables (user_name, shelter_name, etc.).
    """
    channels_to_notify = []

    prefs = NotificationPreference.objects.filter(
        user=recipient, event_key=event_key,
    )
    pref_map = {p.channel: p.enabled for p in prefs}

    if not pref_map:
        # No preferences set — default to email + in_app enabled
        channels_to_notify = ['email', 'in_app']
    else:
        for channel, enabled in pref_map.items():
            if enabled:
                channels_to_notify.append(channel)

    for channel in channels_to_notify:
        log = NotificationLog.objects.create(
            recipient=recipient,
            event_key=event_key,
            channel=channel,
            status=NotificationLog.Status.QUEUED,
            metadata=context,
        )

        if channel == 'email':
            try:
                from base_feature_app.tasks import send_email_notification
                send_email_notification(log.pk)
            except Exception:
                log.status = NotificationLog.Status.FAILED
                log.save(update_fields=['status'])
                logger.exception('Failed to schedule email notification %s', log.pk)
        elif channel == 'in_app':
            # In-app notifications are created as logs with SENT status
            log.status = NotificationLog.Status.SENT
            log.save(update_fields=['status'])

    logger.info(
        'Dispatched %s to %s via %s',
        event_key, recipient.email, channels_to_notify,
    )
