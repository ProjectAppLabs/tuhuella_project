"""Verify payment endpoints enforce authentication and ownership rules."""

from datetime import UTC, datetime

import pytest
from django.urls import reverse
from rest_framework import status

from base_feature_app.models import Payment
from base_feature_app.tests.factories import PaymentFactory, UserFactory


@pytest.fixture(params=['donation', 'sponsorship'])
def owned_payment(request):
    """Create a payment owned by existing_user through either supported parent."""
    parent = request.getfixturevalue(request.param)
    parents = {'donation': None, 'sponsorship': None, request.param: parent}
    return PaymentFactory(
        **parents,
        amount=parent.amount,
        provider_reference=f'PAY-STATUS-{request.param}',
        metadata={'receipt': f'{request.param}-private'},
    )


@pytest.fixture(params=[
    pytest.param(
        {'role': 'admin', 'is_staff': False, 'is_superuser': False},
        id='admin-role',
    ),
    pytest.param(
        {'role': 'adopter', 'is_staff': False, 'is_superuser': True},
        id='superuser',
    ),
    pytest.param(
        {'role': 'adopter', 'is_staff': True, 'is_superuser': False},
        id='staff',
    ),
])
def payment_auditor(request):
    """Each existing audit privilege is exercised independently of ownership."""
    return UserFactory(**request.param)


@pytest.mark.django_db
def test_create_payment_intent_requires_auth(api_client):
    """Unauthenticated users cannot create payment intents."""
    response = api_client.post(
        reverse('payment-create-intent'),
        {'amount': '50000', 'type': 'donation', 'reference_id': 1},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_create_payment_intent_success(authenticated_client, donation):
    """Authenticated user can create a payment intent."""
    response = authenticated_client.post(
        reverse('payment-create-intent'),
        {
            'amount': '50000',
            'type': 'donation',
            'reference_id': donation.pk,
        },
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    data = response.json()
    assert data['provider'] == 'wompi'
    assert data['status'] == 'pending'
    assert Payment.objects.filter(pk=data['payment_id']).exists()


@pytest.mark.django_db
def test_create_payment_intent_missing_fields(authenticated_client):
    """Missing required fields returns 400."""
    response = authenticated_client.post(
        reverse('payment-create-intent'),
        {'amount': '50000'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_payment_webhook_receives(api_client):
    """Webhook endpoint receives and acknowledges."""
    response = api_client.post(
        reverse('payment-webhook'),
        {'event': 'transaction.updated'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['received'] is True


@pytest.mark.django_db
def test_payment_status_requires_auth(api_client, owned_payment):
    """Payment status requires authentication."""
    response = api_client.get(reverse('payment-status', args=[owned_payment.pk]))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_payment_status_returns_detail(authenticated_client, owned_payment):
    """Owners receive the existing payment detail payload, including history."""
    history = owned_payment.status_history.get()

    response = authenticated_client.get(
        reverse('payment-status', args=[owned_payment.pk])
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'id': owned_payment.pk,
        'donation': owned_payment.donation_id,
        'sponsorship': owned_payment.sponsorship_id,
        'modality': owned_payment.modality,
        'provider': 'wompi',
        'provider_reference': owned_payment.provider_reference,
        'amount': str(owned_payment.amount),
        'status': 'pending',
        'paid_at': None,
        'metadata': owned_payment.metadata,
        'status_history': [{
            'previous_status': '',
            'new_status': 'pending',
            'source': 'system',
            'metadata': {},
            'created_at': history.created_at.isoformat().replace('+00:00', 'Z'),
        }],
        'created_at': owned_payment.created_at.isoformat().replace('+00:00', 'Z'),
        'updated_at': owned_payment.updated_at.isoformat().replace('+00:00', 'Z'),
    }


@pytest.mark.django_db
@pytest.mark.parametrize('role', [
    'adopter', 'shelter_admin', 'web_manager', 'veterinarian',
])
def test_payment_status_hides_foreign_payment(
    api_client, other_user, owned_payment, role,
):
    """Non-audit roles cannot distinguish another user's payment from a missing ID."""
    other_user.role = role
    other_user.save(update_fields=['role'])
    api_client.force_authenticate(user=other_user)
    before = Payment.objects.filter(pk=owned_payment.pk).values().get()

    response = api_client.get(reverse('payment-status', args=[owned_payment.pk]))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'error': 'Payment not found'}
    assert Payment.objects.filter(pk=owned_payment.pk).values().get() == before


@pytest.mark.django_db
def test_payment_status_permits_auditor(api_client, payment_auditor, owned_payment):
    """Existing audit privileges permit reading an unarchived payment owned by someone else."""
    api_client.force_authenticate(user=payment_auditor)

    response = api_client.get(reverse('payment-status', args=[owned_payment.pk]))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['id'] == owned_payment.pk
    assert response.json()['donation'] == owned_payment.donation_id
    assert response.json()['sponsorship'] == owned_payment.sponsorship_id
    assert response.json()['metadata'] == owned_payment.metadata


@pytest.mark.django_db
def test_payment_status_hides_archived_payment_from_owner(
    authenticated_client, owned_payment,
):
    """An owner cannot read an archived payment."""
    owned_payment.archived_at = datetime(2026, 10, 8, tzinfo=UTC)
    owned_payment.save(update_fields=['archived_at'])
    before = Payment.objects.filter(pk=owned_payment.pk).values().get()

    response = authenticated_client.get(
        reverse('payment-status', args=[owned_payment.pk])
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'error': 'Payment not found'}
    assert Payment.objects.filter(pk=owned_payment.pk).values().get() == before


@pytest.mark.django_db
def test_payment_status_hides_archived_payment_from_auditor(
    api_client, payment_auditor, owned_payment,
):
    """Audit privileges do not expose archived payment details."""
    owned_payment.archived_at = datetime(2026, 10, 8, tzinfo=UTC)
    owned_payment.save(update_fields=['archived_at'])
    api_client.force_authenticate(user=payment_auditor)
    before = Payment.objects.filter(pk=owned_payment.pk).values().get()

    response = api_client.get(reverse('payment-status', args=[owned_payment.pk]))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'error': 'Payment not found'}
    assert Payment.objects.filter(pk=owned_payment.pk).values().get() == before


@pytest.mark.django_db
def test_payment_status_not_found(authenticated_client):
    """Nonexistent payment returns 404."""
    response = authenticated_client.get(reverse('payment-status', args=[99999]))

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {'error': 'Payment not found'}


@pytest.mark.django_db
def test_payment_list_requires_superadmin(authenticated_client, payment):
    """Regular users cannot list payments."""
    response = authenticated_client.get(reverse('payment-list'))

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_payment_list_returns_rows(admin_client, payment):
    """Staff/superadmin receives payment list with modality and parent ids."""
    response = admin_client.get(reverse('payment-list'))

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    row = next(r for r in data if r['id'] == payment.pk)
    assert row['modality'] == 'donation'
    assert row['donation'] == payment.donation_id


@pytest.mark.django_db
def test_payment_list_allows_is_staff_user(api_client, payment, existing_user):
    """Users with is_staff can list payments (aligned with admin UI gate)."""
    existing_user.is_staff = True
    existing_user.save(update_fields=['is_staff'])
    api_client.force_authenticate(user=existing_user)
    response = api_client.get(reverse('payment-list'))
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


@pytest.mark.django_db
def test_create_payment_intent_rejects_negative_amount(authenticated_client, donation):
    """Negative amount must 400 and create zero new Payment rows.

    Bug this catches: create_payment_intent() only checks
    `if not amount or not payment_type or not reference_id`, and a numeric
    string like "-50000" is truthy, so it never validated the sign before
    calling Payment.objects.create(amount=amount, ...) — which bypasses
    full_clean() entirely, so a negative payment was created and returned 201.
    """
    before = Payment.objects.count()

    response = authenticated_client.post(
        reverse('payment-create-intent'),
        {
            'amount': '-50000',
            'type': 'donation',
            'reference_id': donation.pk,
        },
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert Payment.objects.count() == before
