import pytest
from django.urls import reverse
from rest_framework import status
from freezegun import freeze_time

from base_feature_app.models import NotificationLog, ShelterInvite
from base_feature_app.tests.factories import (
    NotificationPreferenceFactory, ShelterMembershipFactory, UserFactory,
)


@pytest.mark.django_db
def test_shelter_invite_list_requires_auth(api_client):
    """Unauthenticated users cannot list invites."""
    response = api_client.get(reverse('shelter-invite-list'))

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_shelter_invite_list_shelter_admin_sees_own(
    shelter_admin_client, shelter_invite
):
    """Shelter admin sees invites for their shelters."""
    response = shelter_admin_client.get(reverse('shelter-invite-list'))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]['shelter_name'] == 'Happy Paws'


@pytest.mark.django_db
def test_shelter_invite_list_adopter_sees_own(
    authenticated_client, shelter_invite
):
    """Adopter sees invites directed at their intent."""
    response = authenticated_client.get(reverse('shelter-invite-list'))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


@pytest.mark.django_db
def test_shelter_invite_create_requires_auth(api_client):
    """Unauthenticated users cannot create invites."""
    response = api_client.post(
        reverse('shelter-invite-create'),
        {'shelter': 1, 'adopter_intent': 1},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_shelter_invite_create_success(
    shelter_admin_client, shelter, adopter_intent
):
    """Fails if the shelter owner loses permission to send an invitation."""
    response = shelter_admin_client.post(
        reverse('shelter-invite-create'),
        {
            'shelter': shelter.pk,
            'adopter_intent': adopter_intent.pk,
            'message': 'We have a dog for you!',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    invite = ShelterInvite.objects.get(pk=response.json()['id'])
    assert invite.shelter_id == shelter.pk
    assert invite.adopter_intent_id == adopter_intent.pk
    assert invite.message == 'We have a dog for you!'


@pytest.mark.django_db
def test_shelter_invite_respond_accept(authenticated_client, shelter_invite):
    """Adopter can accept an invite."""
    response = authenticated_client.patch(
        reverse('shelter-invite-respond', args=[shelter_invite.pk]),
        {'status': 'accepted'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    shelter_invite.refresh_from_db()
    assert shelter_invite.status == 'accepted'


@pytest.mark.django_db
def test_shelter_invite_respond_reject(authenticated_client, shelter_invite):
    """Adopter can reject an invite."""
    response = authenticated_client.patch(
        reverse('shelter-invite-respond', args=[shelter_invite.pk]),
        {'status': 'rejected'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    shelter_invite.refresh_from_db()
    assert shelter_invite.status == 'rejected'


@pytest.mark.django_db
def test_shelter_invite_respond_rejects_invalid_status(
    authenticated_client, shelter_invite
):
    """Invalid status value is rejected."""
    response = authenticated_client.patch(
        reverse('shelter-invite-respond', args=[shelter_invite.pk]),
        {'status': 'maybe'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    shelter_invite.refresh_from_db()
    assert shelter_invite.status == 'pending'


@pytest.mark.django_db
def test_shelter_invite_create_returns_400_for_invalid_data(shelter_admin_client):
    """Invalid payload returns 400 with serializer errors."""
    response = shelter_admin_client.post(
        reverse('shelter-invite-create'),
        {},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_shelter_invite_respond_returns_404_for_missing(authenticated_client):
    """Responding to a non-existent invite returns 404."""
    response = authenticated_client.patch(
        reverse('shelter-invite-respond', args=[99999]),
        {'status': 'accepted'},
        format='json',
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
@freeze_time('2026-10-08 12:00:00')
@pytest.mark.parametrize('role', ['adopter', 'shelter_admin', 'admin', 'web_manager'])
def test_shelter_invite_create_rejects_unmanaged_shelter(
    api_client, shelter, adopter_intent, role
):
    """Fails if an unrelated role can impersonate a shelter when sending an invite."""
    actor = UserFactory(role=role)
    api_client.force_authenticate(user=actor)
    NotificationPreferenceFactory(
        user=adopter_intent.user, event_key='shelter_invite_sent', channel='in_app'
    )
    payload = {
        'shelter': shelter.pk,
        'adopter_intent': adopter_intent.pk,
        'message': 'Unauthorized invitation',
    }

    response = api_client.post(reverse('shelter-invite-create'), payload, format='json')

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json()['shelter'] == ['You cannot manage this shelter.']
    assert ShelterInvite.objects.filter(shelter=shelter, adopter_intent=adopter_intent).count() == 0
    assert NotificationLog.objects.filter(
        recipient=adopter_intent.user, event_key='shelter_invite_sent'
    ).count() == 0


@pytest.mark.django_db
@freeze_time('2026-10-08 12:00:00')
@pytest.mark.parametrize('membership_role', ['owner', 'admin', 'staff'])
def test_shelter_invite_create_accepts_team_member(
    api_client, shelter, adopter_intent, membership_role
):
    """Fails if existing shelter team membership stops authorizing invitations."""
    actor = UserFactory(role='shelter_admin')
    ShelterMembershipFactory(shelter=shelter, user=actor, role=membership_role)
    NotificationPreferenceFactory(
        user=adopter_intent.user, event_key='shelter_invite_sent', channel='in_app'
    )
    api_client.force_authenticate(user=actor)
    payload = {
        'shelter': shelter.pk,
        'adopter_intent': adopter_intent.pk,
        'message': 'Invitation from our shelter team',
    }

    response = api_client.post(reverse('shelter-invite-create'), payload, format='json')

    assert response.status_code == status.HTTP_201_CREATED
    invite = ShelterInvite.objects.get(pk=response.json()['id'])
    assert invite.shelter_id == shelter.pk
    assert invite.message == 'Invitation from our shelter team'
    notification = NotificationLog.objects.get(
        recipient=adopter_intent.user, event_key='shelter_invite_sent', channel='in_app'
    )
    assert notification.status == 'sent'
    assert notification.metadata['shelter_name'] == 'Happy Paws'
