"""Verify update post endpoints and shelter association permissions."""

import pytest
from django.urls import reverse
from freezegun import freeze_time
from rest_framework import status

from base_feature_app.models import NotificationLog, UpdatePost
from base_feature_app.tests.factories import (
    AnimalFactory,
    CampaignFactory,
    DonationFactory,
    NotificationPreferenceFactory,
    ShelterFactory,
    UpdatePostFactory,
)


@pytest.mark.django_db
def test_update_post_list_public(api_client, update_post):
    """Update post list is publicly accessible."""
    response = api_client.get(reverse('update-post-list'))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1
    assert response.json()[0]['title'] == 'Luna recovered!'


@pytest.mark.django_db
def test_update_post_list_filter_by_shelter(api_client, update_post):
    """List can be filtered by shelter."""
    response = api_client.get(
        reverse('update-post-list'),
        {'shelter': update_post.shelter.pk},
    )

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) == 1


@pytest.mark.django_db
def test_update_post_list_filter_by_campaign_excludes_other_campaigns_post(api_client):
    """Fails if campaign filtering includes another campaign's update post."""
    campaign_a = CampaignFactory()
    campaign_b = CampaignFactory()
    post_a = UpdatePostFactory(campaign=campaign_a, title_es='Campaign A update')
    post_b = UpdatePostFactory(campaign=campaign_b, title_es='Campaign B update')

    response = api_client.get(
        reverse('update-post-list'),
        {'campaign': campaign_a.pk},
    )

    assert response.status_code == status.HTTP_200_OK
    body = response.json()
    returned_ids = [post['id'] for post in body]
    assert returned_ids == [post_a.pk]
    assert body[0]['title'] == 'Campaign A update'
    assert post_b.pk not in returned_ids


@pytest.mark.django_db
def test_update_post_detail_returns_content(api_client, update_post):
    """Detail endpoint returns full content."""
    response = api_client.get(reverse('update-post-detail', args=[update_post.pk]))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['content'] == 'Luna is doing great after surgery.'


@pytest.mark.django_db
def test_update_post_detail_not_found(api_client):
    """Detail endpoint returns 404 for nonexistent post."""
    response = api_client.get(reverse('update-post-detail', args=[99999]))

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_update_post_create_requires_auth(api_client):
    """Unauthenticated users cannot create posts."""
    response = api_client.post(
        reverse('update-post-create'),
        {'title_es': 'Test'},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_update_post_create_success(shelter_admin_client, shelter):
    """Shelter admin can create an update post for their shelter."""
    response = shelter_admin_client.post(
        reverse('update-post-create'),
        {
            'shelter': shelter.pk,
            'title_es': 'Great news!',
            'content_es': 'We adopted 5 animals this week.',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert UpdatePost.objects.filter(title_es='Great news!').exists()
    post = UpdatePost.objects.get(pk=response.json()['id'])
    assert post.campaign_id is None
    assert post.animal_id is None


@pytest.mark.django_db
def test_update_post_create_rejects_missing_title(authenticated_client, shelter):
    """Create endpoint rejects missing title."""
    response = authenticated_client.post(
        reverse('update-post-create'),
        {'shelter': shelter.pk, 'content_es': 'No title'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


# ── PATCH / DELETE ───────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_update_post_patch_by_owner(shelter_admin_client, update_post):
    """Shelter owner can update their post."""
    response = shelter_admin_client.patch(
        reverse('update-post-update', args=[update_post.pk]),
        {'title_es': 'Updated title'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['title'] == 'Updated title'
    update_post.refresh_from_db()
    assert update_post.campaign.shelter_id == update_post.shelter_id
    assert update_post.animal.shelter_id == update_post.shelter_id


@pytest.mark.django_db
def test_update_post_patch_denied_for_non_owner(authenticated_client, update_post):
    """Non-owner cannot update the post."""
    response = authenticated_client.patch(
        reverse('update-post-update', args=[update_post.pk]),
        {'title_es': 'Hacked'},
        format='json',
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_update_post_patch_not_found(shelter_admin_client):
    """Nonexistent post returns 404."""
    response = shelter_admin_client.patch(
        reverse('update-post-update', args=[99999]),
        {'title_es': 'Test'},
        format='json',
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_update_post_delete_by_owner(shelter_admin_client, update_post):
    """Shelter owner archives their post (soft-delete)."""
    response = shelter_admin_client.delete(
        reverse('update-post-delete', args=[update_post.pk]),
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    update_post.refresh_from_db()
    assert update_post.archived_at is not None


@pytest.mark.django_db
def test_update_post_delete_denied_for_non_owner(authenticated_client, update_post):
    """Non-owner cannot delete the post."""
    response = authenticated_client.delete(
        reverse('update-post-delete', args=[update_post.pk]),
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_update_post_delete_not_found(shelter_admin_client):
    """Nonexistent post returns 404."""
    response = shelter_admin_client.delete(
        reverse('update-post-delete', args=[99999]),
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
@freeze_time('2026-10-08 12:00:00')
class TestUpdatePostShelterRelations:
    """Verify effective associations during creation and partial updates."""

    @pytest.mark.parametrize(('field', 'factory'), [('campaign', CampaignFactory), ('animal', AnimalFactory)])
    def test_create_rejects_foreign_relation(self, shelter_admin_client, shelter, field, factory):
        """Fails if a shelter publishes an update associated with another shelter's object."""
        foreign_shelter = ShelterFactory()
        foreign_object = factory(shelter=foreign_shelter)
        payload = {
            'shelter': shelter.pk,
            'title_es': 'Unauthorized update',
            'content_es': 'This belongs to another shelter.',
            field: foreign_object.pk,
        }

        response = shelter_admin_client.post(reverse('update-post-create'), payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()[field] == ['This object does not belong to the selected shelter.']
        assert UpdatePost.objects.filter(title_es='Unauthorized update').count() == 0
        foreign_object.refresh_from_db()
        assert foreign_object.shelter_id == foreign_shelter.pk

    def test_create_rejects_foreign_campaign_notification(self, shelter_admin_client, shelter, existing_user):
        """Fails if a rejected campaign association still notifies another shelter's donors."""
        foreign_campaign = CampaignFactory()
        DonationFactory(user=existing_user, campaign=foreign_campaign, status='paid')
        NotificationPreferenceFactory(
            user=existing_user, event_key='campaign_update_published', channel='in_app'
        )
        payload = {
            'shelter': shelter.pk,
            'campaign': foreign_campaign.pk,
            'title_es': 'Unauthorized donor update',
            'content_es': 'Do not notify this campaign.',
        }

        response = shelter_admin_client.post(reverse('update-post-create'), payload, format='json')

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert UpdatePost.objects.filter(campaign=foreign_campaign).count() == 0
        assert NotificationLog.objects.filter(
            recipient=existing_user, event_key='campaign_update_published'
        ).count() == 0

    @pytest.mark.parametrize(('field', 'factory'), [('campaign', CampaignFactory), ('animal', AnimalFactory)])
    def test_patch_rejects_foreign_relation(self, shelter_admin_client, update_post, field, factory):
        """Fails if PATCH bypasses ownership by omitting shelter while replacing an association."""
        foreign_object = factory()
        original_relation_id = getattr(update_post, field + '_id')
        payload = {field: foreign_object.pk, 'title_es': 'Unauthorized replacement'}

        response = shelter_admin_client.patch(
            reverse('update-post-update', args=[update_post.pk]), payload, format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()[field] == ['This object does not belong to the selected shelter.']
        update_post.refresh_from_db()
        assert getattr(update_post, field + '_id') == original_relation_id
        assert update_post.title_es == 'Luna recovered!'

    @pytest.mark.parametrize(('field', 'factory'), [('campaign', CampaignFactory), ('animal', AnimalFactory)])
    def test_transfer_rejects_retained_relation(
        self, shelter_admin_client, shelter_admin_user, shelter, field, factory
    ):
        """Fails if changing only shelter leaves a foreign association on the transferred post."""
        related_object = factory(shelter=shelter)
        post = UpdatePostFactory(shelter=shelter, **{field: related_object})
        destination = ShelterFactory(owner=shelter_admin_user)
        payload = {'shelter': destination.pk}

        response = shelter_admin_client.patch(
            reverse('update-post-update', args=[post.pk]), payload, format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()[field] == ['This object does not belong to the selected shelter.']
        post.refresh_from_db()
        assert post.shelter_id == shelter.pk
        assert getattr(post, field + '_id') == related_object.pk

    @pytest.mark.parametrize('field', ['campaign', 'animal'])
    def test_patch_clears_explicit_null(self, shelter_admin_client, update_post, field):
        """Fails if an explicit null incorrectly retains the previous association."""
        payload = {field: None}

        response = shelter_admin_client.patch(
            reverse('update-post-update', args=[update_post.pk]), payload, format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        update_post.refresh_from_db()
        assert getattr(update_post, field + '_id') is None
        assert update_post.title_es == 'Luna recovered!'

    def test_transfer_accepts_post_without_relations(
        self, shelter_admin_client, shelter_admin_user, shelter
    ):
        """Fails if an association-free post cannot move between managed shelters."""
        post = UpdatePostFactory(shelter=shelter)
        destination = ShelterFactory(owner=shelter_admin_user)
        payload = {'shelter': destination.pk}

        response = shelter_admin_client.patch(
            reverse('update-post-update', args=[post.pk]), payload, format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        post.refresh_from_db()
        assert post.shelter_id == destination.pk
        assert post.campaign_id is None
        assert post.animal_id is None

    def test_transfer_accepts_cleared_relations(
        self, shelter_admin_client, shelter_admin_user, update_post
    ):
        """Fails if clearing associations cannot accompany a valid shelter transfer."""
        destination = ShelterFactory(owner=shelter_admin_user)
        payload = {'shelter': destination.pk, 'campaign': None, 'animal': None}

        response = shelter_admin_client.patch(
            reverse('update-post-update', args=[update_post.pk]), payload, format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        update_post.refresh_from_db()
        assert update_post.shelter_id == destination.pk
        assert update_post.campaign_id is None
        assert update_post.animal_id is None

    def test_transfer_accepts_destination_relations(
        self, shelter_admin_client, shelter_admin_user, update_post
    ):
        """Fails if valid replacement associations are checked against the previous shelter."""
        destination = ShelterFactory(owner=shelter_admin_user)
        campaign = CampaignFactory(shelter=destination)
        animal = AnimalFactory(shelter=destination)
        payload = {'shelter': destination.pk, 'campaign': campaign.pk, 'animal': animal.pk}

        response = shelter_admin_client.patch(
            reverse('update-post-update', args=[update_post.pk]), payload, format='json'
        )

        assert response.status_code == status.HTTP_200_OK
        update_post.refresh_from_db()
        assert update_post.shelter_id == destination.pk
        assert update_post.campaign_id == campaign.pk
        assert update_post.animal_id == animal.pk

    def test_transfer_rejects_unmanaged_destination(self, shelter_admin_client, update_post):
        """Fails if consistent cleared relations bypass permission on the destination shelter."""
        destination = ShelterFactory()
        original_shelter_id = update_post.shelter_id
        original_campaign_id = update_post.campaign_id
        original_animal_id = update_post.animal_id
        payload = {'shelter': destination.pk, 'campaign': None, 'animal': None}

        response = shelter_admin_client.patch(
            reverse('update-post-update', args=[update_post.pk]), payload, format='json'
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()['shelter'] == ['You cannot manage this shelter.']
        update_post.refresh_from_db()
        assert update_post.shelter_id == original_shelter_id
        assert update_post.campaign_id == original_campaign_id
        assert update_post.animal_id == original_animal_id

    def test_create_accepts_matching_relations(self, shelter_admin_client, shelter, campaign, animal):
        """Fails if relationship validation rejects a post with objects from its own shelter."""
        payload = {
            'shelter': shelter.pk,
            'campaign': campaign.pk,
            'animal': animal.pk,
            'title_es': 'Authorized update',
            'content_es': 'Both associations belong to this shelter.',
        }

        response = shelter_admin_client.post(reverse('update-post-create'), payload, format='json')

        assert response.status_code == status.HTTP_201_CREATED
        post = UpdatePost.objects.get(pk=response.json()['id'])
        assert post.shelter_id == shelter.pk
        assert post.campaign_id == campaign.pk
        assert post.animal_id == animal.pk

    def test_transfer_rejects_unmanaged_origin(self, authenticated_client, existing_user, update_post):
        """Fails if managing the destination authorizes moving a post from someone else's shelter."""
        destination = ShelterFactory(owner=existing_user)
        original_shelter_id = update_post.shelter_id
        original_campaign_id = update_post.campaign_id
        original_animal_id = update_post.animal_id
        payload = {'shelter': destination.pk, 'campaign': None, 'animal': None}

        response = authenticated_client.patch(
            reverse('update-post-update', args=[update_post.pk]), payload, format='json'
        )

        assert response.status_code == status.HTTP_403_FORBIDDEN
        update_post.refresh_from_db()
        assert update_post.shelter_id == original_shelter_id
        assert update_post.campaign_id == original_campaign_id
        assert update_post.animal_id == original_animal_id
