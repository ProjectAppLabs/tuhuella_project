"""Real animal-list requests must keep shelter query costs bounded."""

import pytest
from django.db import connection
from django.test.utils import CaptureQueriesContext
from django.urls import reverse
from rest_framework import status

from base_feature_app.tests.factories import AnimalFactory, ShelterFactory


@pytest.fixture
def animals_with_distinct_shelters(shelter_admin_user):
    """Create twenty published animals with different shelter records."""
    animals = []
    for index in range(20):
        shelter = ShelterFactory(
            owner=shelter_admin_user,
            name=f'Query Shelter {index}',
        )
        animals.append(AnimalFactory(shelter=shelter, name=f'Query Animal {index}'))
    return animals


@pytest.mark.django_db
@pytest.mark.parametrize('page_size', [1, 20])
def test_animal_list_stays_within_query_budget(
    api_client, animals_with_distinct_shelters, page_size, record_property,
):
    """Fails if a real list request exceeds six queries during serialization."""
    with CaptureQueriesContext(connection) as queries:
        response = api_client.get(reverse('animal-list'), {'page_size': page_size})
    record_property('query_count', len(queries))
    record_property('page_size', page_size)

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()['results']) == page_size
    assert len(queries) <= 6


@pytest.mark.django_db
def test_animal_list_query_count_is_constant(
    api_client, animals_with_distinct_shelters, record_property,
):
    """Fails if listing twenty distinct shelters needs more queries than one."""
    url = reverse('animal-list')
    with CaptureQueriesContext(connection) as small_queries:
        small_response = api_client.get(url, {'page_size': 1})
    with CaptureQueriesContext(connection) as large_queries:
        large_response = api_client.get(url, {'page_size': 20})
    record_property('small_query_count', len(small_queries))
    record_property('large_query_count', len(large_queries))

    assert small_response.status_code == status.HTTP_200_OK
    assert large_response.status_code == status.HTTP_200_OK
    assert len(small_response.json()['results']) == 1
    assert len(large_response.json()['results']) == 20
    assert len(large_queries) == len(small_queries)


@pytest.mark.django_db
def test_animal_list_preserves_distinct_shelter_names(
    api_client, animals_with_distinct_shelters,
):
    """Fails if an animal is serialized with a different shelter's identity."""
    response = api_client.get(reverse('animal-list'), {'page_size': 20})

    assert response.status_code == status.HTTP_200_OK
    assert [(row['shelter'], row['shelter_name']) for row in response.json()['results']] == [
        (animal.shelter_id, animal.shelter.name)
        for animal in reversed(animals_with_distinct_shelters)
    ]
