"""Shelter endpoints: public directory, shelter panel list (owner=me), detail, create, update."""

from datetime import datetime
from datetime import timezone as dt_timezone

import pytest
from django.urls import reverse
from rest_framework import status

from base_feature_app.models import Shelter
from base_feature_app.tests.factories import (
    ShelterAdminUserFactory,
    ShelterFactory,
    ShelterMembershipFactory,
    UserFactory,
)

ARCHIVED_AT = datetime(2026, 1, 1, tzinfo=dt_timezone.utc)


@pytest.fixture(autouse=True)
def fast_shelter_password_hashing(settings):
    """These permission requests use real users but do not test hashing cost."""
    settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']


@pytest.fixture(params=['shelter-list', 'shelter-detail'])
def shelter_read_endpoint(request, shelter):
    """Both public response shapes expose the same shelter in these cases."""
    args = [shelter.pk] if request.param == 'shelter-detail' else None
    return reverse(request.param, args=args)


def _shelter_row(response):
    body = response.json()
    return body[0] if isinstance(body, list) else body


@pytest.mark.django_db
def test_public_shelter_responses_omit_owner_email(api_client, shelter, shelter_read_endpoint):
    response = api_client.get(shelter_read_endpoint)

    assert response.status_code == status.HTTP_200_OK
    assert _shelter_row(response)['name'] == shelter.name
    assert 'owner_email' not in _shelter_row(response)


@pytest.mark.django_db
@pytest.mark.parametrize('role', ['adopter', 'shelter_admin'])
def test_unrelated_user_shelter_responses_omit_owner_email(api_client, shelter, shelter_read_endpoint, role):
    user = UserFactory(role=role, password=None)
    api_client.force_authenticate(user=user)

    response = api_client.get(shelter_read_endpoint)

    assert response.status_code == status.HTTP_200_OK
    assert _shelter_row(response)['name'] == shelter.name
    assert 'owner_email' not in _shelter_row(response)


@pytest.mark.django_db
def test_shelter_owner_responses_include_owner_email(shelter_admin_client, shelter, shelter_read_endpoint):
    response = shelter_admin_client.get(shelter_read_endpoint)

    assert response.status_code == status.HTTP_200_OK
    assert _shelter_row(response)['owner_email'] == shelter.owner.email


@pytest.mark.django_db
def test_shelter_team_responses_include_owner_email(api_client, shelter, shelter_read_endpoint):
    member = ShelterAdminUserFactory(password=None)
    ShelterMembershipFactory(shelter=shelter, user=member)
    api_client.force_authenticate(user=member)

    response = api_client.get(shelter_read_endpoint)

    assert response.status_code == status.HTTP_200_OK
    assert _shelter_row(response)['owner_email'] == shelter.owner.email


@pytest.mark.django_db
@pytest.mark.parametrize('role,is_superuser', [
    ('admin', False), ('web_manager', False), ('adopter', True),
], ids=['admin', 'web-manager', 'superuser'])
def test_platform_operator_shelter_responses_include_owner_email(
    api_client, shelter, shelter_read_endpoint, role, is_superuser,
):
    operator = UserFactory(role=role, is_superuser=is_superuser, password=None)
    api_client.force_authenticate(user=operator)

    response = api_client.get(shelter_read_endpoint)

    assert response.status_code == status.HTTP_200_OK
    assert _shelter_row(response)['owner_email'] == shelter.owner.email


@pytest.mark.django_db
def test_owner_me_keeps_shelter_owner_email(shelter_admin_client, shelter):
    response = shelter_admin_client.get(reverse('shelter-list'), {'owner': 'me'})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]['owner_email'] == shelter.owner.email


@pytest.mark.django_db
def test_team_member_owner_me_keeps_shelter_owner_email(api_client, shelter):
    member = ShelterAdminUserFactory(password=None)
    ShelterMembershipFactory(shelter=shelter, user=member)
    api_client.force_authenticate(user=member)

    response = api_client.get(reverse('shelter-list'), {'owner': 'me'})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()[0]['owner_email'] == shelter.owner.email


@pytest.mark.django_db
def test_shelter_list_returns_only_verified(api_client, shelter):
    """Only verified shelters appear in the public list."""
    Shelter.objects.create(
        name='Unverified Place',
        city='Medellín',
        verification_status=Shelter.VerificationStatus.PENDING,
        owner=shelter.owner,
    )
    response = api_client.get(reverse('shelter-list'))

    assert response.status_code == status.HTTP_200_OK
    names = [s['name'] for s in response.json()]
    assert 'Happy Paws' in names
    assert 'Unverified Place' not in names


@pytest.mark.django_db
def test_owner_me_lists_only_shelters_the_user_manages(shelter_admin_client, shelter):
    """The shelter panel must not receive another shelter, even a newer verified one."""
    ShelterFactory(name='Other Verified Shelter')

    response = shelter_admin_client.get(reverse('shelter-list'), {'owner': 'me'})

    assert response.status_code == status.HTTP_200_OK
    assert [row['name'] for row in response.json()] == ['Happy Paws']


@pytest.mark.django_db
def test_owner_me_includes_shelter_pending_verification(shelter_admin_client, shelter_admin_user):
    """A shelter still awaiting verification appears in its owner's panel."""
    ShelterFactory(
        owner=shelter_admin_user,
        name='Pending Paws',
        verification_status=Shelter.VerificationStatus.PENDING,
    )

    response = shelter_admin_client.get(reverse('shelter-list'), {'owner': 'me'})

    assert response.status_code == status.HTTP_200_OK
    assert [(row['name'], row['verification_status']) for row in response.json()] == [
        ('Pending Paws', 'pending'),
    ]


@pytest.mark.django_db
def test_owner_me_includes_shelter_where_user_is_team_member(api_client):
    """A team member manages the shelter too, so it belongs in the member's panel."""
    member = ShelterAdminUserFactory()
    team_shelter = ShelterFactory(
        name='Team Shelter',
        verification_status=Shelter.VerificationStatus.PENDING,
    )
    ShelterMembershipFactory(shelter=team_shelter, user=member)
    ShelterFactory(name='Unrelated Shelter')
    api_client.force_authenticate(user=member)

    response = api_client.get(reverse('shelter-list'), {'owner': 'me'})

    assert response.status_code == status.HTTP_200_OK
    assert [row['name'] for row in response.json()] == ['Team Shelter']


@pytest.mark.django_db
def test_owner_me_excludes_archived_shelter(shelter_admin_client, shelter_admin_user):
    """An archived shelter no longer appears in its owner's panel."""
    ShelterFactory(
        owner=shelter_admin_user,
        name='Live Paws',
        verification_status=Shelter.VerificationStatus.PENDING,
    )
    ShelterFactory(owner=shelter_admin_user, name='Archived Paws', archived_at=ARCHIVED_AT)

    response = shelter_admin_client.get(reverse('shelter-list'), {'owner': 'me'})

    assert response.status_code == status.HTTP_200_OK
    assert [row['name'] for row in response.json()] == ['Live Paws']


@pytest.mark.django_db
def test_owner_me_rejects_anonymous_request(api_client, shelter):
    """Without a session the panel list answers 401 instead of any shelter."""
    response = api_client.get(reverse('shelter-list'), {'owner': 'me'})

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert list(response.json()) == ['detail']


@pytest.mark.django_db
@pytest.mark.parametrize(
    'query',
    [{}, {'owner': '1'}, {'owner': 'ME'}, {'owner': 'someone'}],
    ids=['no-owner', 'numeric-owner', 'uppercase-me', 'other-word'],
)
def test_shelter_list_stays_public_unless_owner_is_me(
    shelter_admin_client, shelter_admin_user, query,
):
    """Without owner=me even a signed-in shelter admin gets the public verified list."""
    ShelterFactory(
        owner=shelter_admin_user,
        name='Pending Paws',
        verification_status=Shelter.VerificationStatus.PENDING,
    )
    ShelterFactory(name='Other Verified Shelter')

    response = shelter_admin_client.get(reverse('shelter-list'), query)

    assert response.status_code == status.HTTP_200_OK
    assert [row['name'] for row in response.json()] == ['Other Verified Shelter']


@pytest.mark.django_db
def test_shelter_detail_returns_existing(api_client, shelter):
    """Detail endpoint returns a specific shelter by pk."""
    response = api_client.get(reverse('shelter-detail', args=[shelter.pk]))

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    assert body['name'] == 'Happy Paws'
    assert 'video_url' in body
    assert body['video_url'] == ''


@pytest.mark.django_db
def test_shelter_detail_returns_404_for_missing(api_client):
    """Detail endpoint returns 404 for non-existent pk."""
    response = api_client.get(reverse('shelter-detail', args=[99999]))

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_shelter_create_requires_auth(api_client):
    """Unauthenticated users cannot create shelters."""
    response = api_client.post(
        reverse('shelter-create'),
        {'name': 'New Shelter', 'city': 'Cali'},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert Shelter.objects.filter(name='New Shelter').count() == 0


@pytest.mark.django_db
def test_shelter_create_blocks_adopter(authenticated_client):
    """Adopters cannot bypass the formal ShelterApplication flow via /api/shelters/create/."""
    response = authenticated_client.post(
        reverse('shelter-create'),
        {
            'name': 'Bypass Shelter',
            'city': 'Cali',
            'description_es': 'A new place',
            'phone': '3009876543',
            'email': 'bypass@shelter.org',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Shelter.objects.filter(name='Bypass Shelter').count() == 0


@pytest.mark.django_db
def test_shelter_create_blocks_shelter_admin(shelter_admin_client):
    """Even shelter_admin role cannot create new shelters directly — only admin/web_manager can."""
    response = shelter_admin_client.post(
        reverse('shelter-create'),
        {
            'name': 'Second Shelter',
            'city': 'Cali',
            'description_es': 'A new place',
            'phone': '3009876543',
            'email': 'second@shelter.org',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_shelter_create_allows_web_manager(api_client, db):
    """Web managers can create shelters directly (e.g., bulk import or operational tasks)."""
    from base_feature_app.tests.factories import WebManagerUserFactory

    web_manager = WebManagerUserFactory()
    api_client.force_authenticate(user=web_manager)

    response = api_client.post(
        reverse('shelter-create'),
        {
            'name': 'Web Manager Shelter',
            'city': 'Cali',
            'description_es': 'Created by web manager',
            'phone': '3009876543',
            'email': 'wm@shelter.org',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Shelter.objects.filter(name='Web Manager Shelter', owner=web_manager).exists()


@pytest.mark.django_db
def test_shelter_update_by_owner(shelter_admin_client, shelter):
    """Owner can update their own shelter."""
    response = shelter_admin_client.patch(
        reverse('shelter-update', args=[shelter.pk]),
        {'name': 'Happy Paws Updated'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    shelter.refresh_from_db()
    assert shelter.name == 'Happy Paws Updated'


@pytest.mark.django_db
def test_shelter_update_denied_for_non_owner(authenticated_client, shelter):
    """Non-owner cannot update a shelter they don't own."""
    response = authenticated_client.patch(
        reverse('shelter-update', args=[shelter.pk]),
        {'name': 'Hijacked'},
        format='json',
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND
    shelter.refresh_from_db()
    assert shelter.name == 'Happy Paws'
