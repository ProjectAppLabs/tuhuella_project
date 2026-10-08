"""Verify email delivery contracts and safe failure diagnostics."""

import logging
from functools import partial
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from base_feature_app.tests.factories import UserFactory, VolunteerPositionFactory
from base_feature_app.utils.email_utils import (
    TEAM_EMAIL,
    send_contact_form_email,
    send_password_reset_code,
    send_verification_code,
    send_volunteer_application_notification,
)


@pytest.mark.django_db
def test_send_password_reset_code_sends_email():
    """Deliver the password reset email to the user's address."""
    user = UserFactory(first_name='Laura')
    with patch('base_feature_app.utils.email_utils.send_mail') as mock_send, \
         patch('base_feature_app.utils.email_utils.render_to_string', return_value='<html/>'):
        send_password_reset_code(user, '123456')
    mock_send.assert_called_once()
    call_args = mock_send.call_args
    assert user.email in call_args.args[3]


@pytest.mark.django_db
def test_send_password_reset_code_returns_true_on_success():
    """Return success after delivering a password reset email."""
    user = UserFactory()
    with patch('base_feature_app.utils.email_utils.send_mail'), \
         patch('base_feature_app.utils.email_utils.render_to_string', return_value='<html/>'):
        result = send_password_reset_code(user, '123456')
    assert result is True


@pytest.mark.django_db
def test_send_password_reset_code_returns_false_on_smtp_error():
    """Report failure when password reset delivery raises an error."""
    user = UserFactory()
    with patch('base_feature_app.utils.email_utils.send_mail', side_effect=Exception('SMTP error')), \
         patch('base_feature_app.utils.email_utils.render_to_string', return_value='<html/>'):
        result = send_password_reset_code(user, '123456')
    assert result is False


@pytest.fixture(params=[
    'password_reset', 'verification', 'volunteer_application', 'contact_form',
])
def email_operation(request, settings):
    """Build each supported email operation with private sample content."""
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    settings.DEFAULT_FROM_EMAIL = 'team@example.com'
    user = UserFactory.build(first_name='Laura', email='private@example.com')
    application = SimpleNamespace(
        user=user, position=VolunteerPositionFactory.build(),
        motivation='Private application message',
    )
    operations = {
        'password_reset': partial(send_password_reset_code, user, '123456'),
        'verification': partial(send_verification_code, user.email, '123456'),
        'volunteer_application': partial(
            send_volunteer_application_notification, application,
        ),
        'contact_form': partial(
            send_contact_form_email, name=user.first_name, email=user.email,
            subject='Private subject', message='Private contact message',
        ),
    }
    return request.param, operations[request.param]


@pytest.mark.django_db
def test_email_failure_emits_sanitized_diagnostic(email_operation, caplog):
    """A provider failure identifies its operation without leaking its payload."""
    operation_name, send = email_operation
    error = RuntimeError('private@example.com 123456 Private contact message')

    with caplog.at_level(logging.ERROR, logger='base_feature_app.utils.email_utils'):
        with patch(
            'django.core.mail.backends.locmem.EmailBackend.send_messages',
            side_effect=error,
        ):
            result = send()

    assert result is False
    assert len(caplog.records) == 1
    record = caplog.records[0]
    assert record.name == 'base_feature_app.utils.email_utils'
    assert record.levelno == logging.ERROR
    assert record.getMessage() == (
        f'Email delivery failed: operation={operation_name} error_type=RuntimeError'
    )
    assert record.exc_info is None
    assert str(error) not in caplog.text


@pytest.mark.django_db
def test_email_template_failure_emits_sanitized_diagnostic(email_operation, caplog):
    """A rendering failure produces the same safe diagnostic as a send failure."""
    operation_name, send = email_operation
    error = RuntimeError('private@example.com 123456 Private application message')

    with caplog.at_level(logging.ERROR, logger='base_feature_app.utils.email_utils'):
        with patch(
            'base_feature_app.utils.email_utils.render_to_string',
            side_effect=error,
        ):
            send()

    assert len(caplog.records) == 1
    assert caplog.records[0].getMessage() == (
        f'Email delivery failed: operation={operation_name} error_type=RuntimeError'
    )
    assert caplog.records[0].exc_info is None
    assert str(error) not in caplog.text


@pytest.mark.django_db
def test_email_success_delivers_message(email_operation, mailoutbox):
    """Deliver one message for each supported email operation."""
    _, send = email_operation

    result = send()

    assert result is True
    assert len(mailoutbox) == 1


@pytest.mark.django_db
def test_send_password_reset_code_uses_english_template_and_subject_for_en_locale():
    """Select the English password reset template and subject."""
    user = UserFactory(first_name='Laura')
    with patch('base_feature_app.utils.email_utils.send_mail') as mock_send, \
         patch('base_feature_app.utils.email_utils.render_to_string', return_value='<html/>') as mock_render:
        send_password_reset_code(user, '123456', locale='en')
    # subject is the first positional arg to send_mail
    assert mock_send.call_args.args[0] == 'Mi Huella - Password reset code'
    # English template selected
    assert mock_render.call_args.args[0] == 'emails/password_reset_code_en.html'


@pytest.mark.django_db
def test_send_password_reset_code_defaults_to_spanish_for_unknown_locale():
    """Use Spanish password reset content for an unknown locale."""
    user = UserFactory(first_name='Laura')
    with patch('base_feature_app.utils.email_utils.send_mail') as mock_send, \
         patch('base_feature_app.utils.email_utils.render_to_string', return_value='<html/>') as mock_render:
        send_password_reset_code(user, '123456', locale='fr')
    assert mock_send.call_args.args[0] == 'Mi Huella - Codigo de restablecimiento'
    assert mock_render.call_args.args[0] == 'emails/password_reset_code.html'


def test_send_verification_code_sends_to_correct_email():
    """Deliver the verification message to the supplied address."""
    with patch('base_feature_app.utils.email_utils.send_mail') as mock_send, \
         patch('base_feature_app.utils.email_utils.render_to_string', return_value='<html/>'):
        send_verification_code('test@example.com', '654321')
    call_args = mock_send.call_args
    assert 'test@example.com' in call_args.args[3]


def test_send_verification_code_returns_true_on_success():
    """Return success after delivering a verification email."""
    with patch('base_feature_app.utils.email_utils.send_mail'), \
         patch('base_feature_app.utils.email_utils.render_to_string', return_value='<html/>'):
        result = send_verification_code('test@example.com', '654321')
    assert result is True


@pytest.mark.django_db
def test_send_volunteer_application_notification_sends_to_team():
    """Deliver the volunteer application notification to the team."""
    from types import SimpleNamespace
    position = VolunteerPositionFactory()
    user = UserFactory()
    application = SimpleNamespace(user=user, position=position, motivation='I love animals')
    with patch('base_feature_app.utils.email_utils.send_mail') as mock_send, \
         patch('base_feature_app.utils.email_utils.render_to_string', return_value='<html/>'):
        send_volunteer_application_notification(application)
    call_args = mock_send.call_args
    assert TEAM_EMAIL in call_args.args[3]


def test_send_verification_code_returns_false_on_smtp_error():
    """Report failure when verification delivery raises an error."""
    with patch('base_feature_app.utils.email_utils.send_mail', side_effect=Exception('SMTP down')), \
         patch('base_feature_app.utils.email_utils.render_to_string', return_value='<html/>'):
        result = send_verification_code('test@example.com', '654321')
    assert result is False


@pytest.mark.django_db
def test_send_volunteer_notification_returns_false_on_smtp_error():
    """Report failure when volunteer notification delivery raises an error."""
    from types import SimpleNamespace
    position = VolunteerPositionFactory()
    user = UserFactory()
    application = SimpleNamespace(user=user, position=position, motivation='I love animals')
    with patch('base_feature_app.utils.email_utils.send_mail', side_effect=Exception('SMTP down')), \
         patch('base_feature_app.utils.email_utils.render_to_string', return_value='<html/>'):
        result = send_volunteer_application_notification(application)
    assert result is False


def test_send_contact_form_email_sets_reply_to():
    """Set the contact message reply address to its sender."""
    from types import SimpleNamespace
    stub_msg = SimpleNamespace(
        attach_alternative=lambda *_: None,
        send=lambda: None,
    )
    with patch('base_feature_app.utils.email_utils.EmailMultiAlternatives', return_value=stub_msg) as mock_cls, \
         patch('base_feature_app.utils.email_utils.render_to_string', return_value='<html/>'):
        send_contact_form_email(
            name='Pedro', email='pedro@example.com',
            subject='Help', message='I need help',
        )
    call_kwargs = mock_cls.call_args.kwargs
    assert 'pedro@example.com' in call_kwargs.get('reply_to', [])


def test_send_contact_form_email_returns_false_on_error():
    """Report failure when contact message delivery raises an error."""
    def _raise_on_send(): raise Exception('connection refused')
    from types import SimpleNamespace
    stub_msg = SimpleNamespace(
        attach_alternative=lambda *_: None,
        send=_raise_on_send,
    )
    with patch('base_feature_app.utils.email_utils.EmailMultiAlternatives', return_value=stub_msg), \
         patch('base_feature_app.utils.email_utils.render_to_string', return_value='<html/>'):
        result = send_contact_form_email(
            name='Pedro', email='pedro@example.com',
            subject='Help', message='I need help',
        )
    assert result is False
