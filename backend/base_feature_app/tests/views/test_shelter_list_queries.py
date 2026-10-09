"""Shelter list requests must keep their query cost constant.

ShelterListSerializer reads every shelter's owner e-mail, logo and cover image.
Unless those relations are loaded with the shelters, each listed shelter costs
extra queries, so the public directory, the shelter panel (owner=me) and the
web-manager list slow down as shelters are added (list budget of the 1 vCPU
host: six queries).
"""

from datetime import datetime
from datetime import timezone as dt_timezone

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from django_attachments.models import Attachment, Library
from rest_framework import status

from base_feature_app.models import Shelter
from base_feature_app.tests.factories import (
    ShelterAdminUserFactory,
    ShelterFactory,
    ShelterMembershipFactory,
    WebManagerUserFactory,
)

MAX_SHELTER_LIST_QUERIES = 6
STORED_AT = datetime(2026, 1, 1, tzinfo=dt_timezone.utc)


def _image_library(label):
    """Library whose primary attachment points at a stored image (no file I/O)."""
    library = Library.objects.create(title=label)
    Attachment.objects.bulk_create([
        Attachment(
            library=library, rank=0, original_name=f'{label}.jpg',
            file=f'attachments/test/{label}.jpg', filesize=1, mimetype='image/jpeg',
            image_width=1, image_height=1, created=STORED_AT, updated=STORED_AT,
        ),
    ])
    library.primary_attachment = Attachment.objects.get(library=library)
    library.save(update_fields=['primary_attachment'])
    return library


def _create_shelters_with_images(start, count, **overrides):
    """Create shelters that each have their own owner, logo and cover image."""
    return [
        ShelterFactory(
            name=f'Query Shelter {index}',
            owner=ShelterAdminUserFactory(email=f'owner{index}@example.com', password=None),
            logo=_image_library(f'logo-{index}'),
            cover_image=_image_library(f'cover-{index}'),
            **overrides,
        )
        for index in range(start, start + count)
    ]


def _create_managed_shelters(manager, start, count):
    """Pending shelters owned by other users where the manager is a team member."""
    shelters = _create_shelters_with_images(
        start, count, verification_status=Shelter.VerificationStatus.PENDING,
    )
    for shelter in shelters:
        ShelterMembershipFactory(shelter=shelter, user=manager)
    return shelters


@pytest.fixture
def web_manager_client(api_client, db):
    """APIClient authenticated as a web manager."""
    api_client.force_authenticate(user=WebManagerUserFactory(password=None))
    return api_client


@pytest.mark.django_db
def test_public_shelter_list_query_count_is_constant(api_client, record_property):
    """Fails if each listed shelter adds queries for its owner, logo or cover."""
    url = reverse('shelter-list')
    _create_shelters_with_images(start=0, count=1)
    with CaptureQueriesContext(connection) as one_shelter:
        small_response = api_client.get(url)
    _create_shelters_with_images(start=1, count=19)
    with CaptureQueriesContext(connection) as twenty_shelters:
        large_response = api_client.get(url)
    record_property('one_shelter_queries', len(one_shelter))
    record_property('twenty_shelters_queries', len(twenty_shelters))

    assert small_response.status_code == status.HTTP_200_OK
    assert len(small_response.json()) == 1
    assert len(large_response.json()) == 20
    assert len(twenty_shelters) == len(one_shelter)
    assert len(twenty_shelters) <= MAX_SHELTER_LIST_QUERIES


@pytest.mark.django_db
def test_web_manager_shelter_list_query_count_is_constant(web_manager_client, record_property):
    """Fails if a twenty-row web-manager page needs more queries than a one-row page."""
    url = reverse('admin-shelters-list')
    _create_shelters_with_images(start=0, count=20)
    with CaptureQueriesContext(connection) as one_row:
        small_response = web_manager_client.get(url, {'page_size': 1})
    with CaptureQueriesContext(connection) as twenty_rows:
        large_response = web_manager_client.get(url, {'page_size': 20})
    record_property('one_row_queries', len(one_row))
    record_property('twenty_rows_queries', len(twenty_rows))

    assert small_response.status_code == status.HTTP_200_OK
    assert len(small_response.json()['results']) == 1
    assert len(large_response.json()['results']) == 20
    assert len(twenty_rows) == len(one_row)
    assert len(twenty_rows) <= MAX_SHELTER_LIST_QUERIES


@pytest.mark.django_db
def test_owner_shelter_list_query_count_is_constant(api_client, record_property):
    """Fails if each shelter in a manager's panel list adds queries for owner, logo or cover."""
    manager = ShelterAdminUserFactory(password=None)
    api_client.force_authenticate(user=manager)
    url = reverse('shelter-list')
    _create_managed_shelters(manager, start=0, count=1)
    with CaptureQueriesContext(connection) as one_shelter:
        small_response = api_client.get(url, {'owner': 'me'})
    _create_managed_shelters(manager, start=1, count=4)
    with CaptureQueriesContext(connection) as five_shelters:
        large_response = api_client.get(url, {'owner': 'me'})
    record_property('one_managed_shelter_queries', len(one_shelter))
    record_property('five_managed_shelters_queries', len(five_shelters))

    assert small_response.status_code == status.HTTP_200_OK
    assert len(small_response.json()) == 1
    assert len(large_response.json()) == 5
    assert len(five_shelters) == len(one_shelter)
    assert len(five_shelters) <= MAX_SHELTER_LIST_QUERIES


@pytest.mark.django_db
def test_public_shelter_list_keeps_each_shelter_owner_with_its_images(api_client):
    """Fails if a shelter is listed with another shelter's owner, logo or cover."""
    _create_shelters_with_images(start=0, count=3)

    response = api_client.get(reverse('shelter-list'))

    assert response.status_code == status.HTTP_200_OK
    assert sorted(
        (row['name'], row['owner_email'], row['logo_url'], row['cover_image_url'])
        for row in response.json()
    ) == [
        (f'Query Shelter {index}', f'owner{index}@example.com',
         f'/media/attachments/test/logo-{index}.jpg', f'/media/attachments/test/cover-{index}.jpg')
        for index in range(3)
    ]
