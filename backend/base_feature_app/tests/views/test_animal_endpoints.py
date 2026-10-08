"""API regressions for public animal lists and shelter-managed endpoints."""

import pytest
from django.urls import reverse
from rest_framework import status

from base_feature_app.models import Animal
from base_feature_app.tests.factories import AnimalFactory, ShelterFactory

CSV_FILTERS = ('species', 'size', 'age_range', 'gender', 'energy_level')


@pytest.mark.django_db
@pytest.mark.parametrize('field', CSV_FILTERS)
@pytest.mark.parametrize('value', ['', '   ', ' , , '])
def test_animal_list_ignores_empty_csv_filters(api_client, animal, field, value):
    """Fails if a blank CSV filter crashes or removes published animals."""
    url = reverse('animal-list')
    unfiltered_response = api_client.get(url)

    response = api_client.get(url, {field: value})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == unfiltered_response.json()


@pytest.mark.django_db
@pytest.mark.parametrize(('field', 'other_value', 'excluded_value'), [
    ('species', 'cat', 'other'),
    ('size', 'small', 'large'),
    ('age_range', 'adult', 'senior'),
    ('gender', 'male', 'unknown'),
    ('energy_level', 'high', 'low'),
])
def test_animal_list_accepts_multiple_csv_values(
    api_client, animal, field, other_value, excluded_value,
):
    """Fails if comma-separated choices lose a match or include another value."""
    matching = AnimalFactory(shelter=animal.shelter, **{field: other_value})
    AnimalFactory(shelter=animal.shelter, **{field: excluded_value})
    values = f' {getattr(animal, field)} , , {other_value}, '

    response = api_client.get(reverse('animal-list'), {field: values})

    assert response.status_code == status.HTTP_200_OK
    assert {row['id'] for row in response.json()['results']} == {animal.pk, matching.pk}


@pytest.mark.django_db
@pytest.mark.parametrize('field', CSV_FILTERS)
def test_animal_list_returns_no_matches_for_unknown_csv_value(api_client, animal, field):
    """Fails if unknown filter values are ignored instead of matching no animals."""
    response = api_client.get(reverse('animal-list'), {field: 'not-a-choice'})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['count'] == 0
    assert response.json()['results'] == []


@pytest.mark.django_db
@pytest.mark.parametrize('field', CSV_FILTERS)
def test_animal_list_retains_valid_csv_value_beside_unknown(api_client, animal, field):
    """Fails if an unknown choice rejects an otherwise matching CSV filter."""
    response = api_client.get(
        reverse('animal-list'), {field: f'{getattr(animal, field)},not-a-choice'},
    )

    assert response.status_code == status.HTTP_200_OK
    assert [row['id'] for row in response.json()['results']] == [animal.pk]


@pytest.fixture
def combined_filter_animal(shelter):
    """Create a matching animal plus distractors differing in one filter each."""
    fields = {
        'species': 'dog', 'size': 'medium', 'age_range': 'young',
        'gender': 'female', 'energy_level': 'low',
        'good_with_kids': 'yes', 'good_with_dogs': 'no', 'good_with_cats': 'unknown',
    }
    matching = AnimalFactory(shelter=shelter, **fields)
    for field, value in (
        ('species', 'other'), ('size', 'large'), ('age_range', 'senior'),
        ('gender', 'male'), ('energy_level', 'high'),
        ('good_with_kids', 'no'), ('good_with_dogs', 'yes'), ('good_with_cats', 'yes'),
    ):
        AnimalFactory(shelter=shelter, **{**fields, field: value})
    other_shelter = ShelterFactory(owner=shelter.owner)
    AnimalFactory(shelter=other_shelter, **fields)
    return matching


@pytest.mark.django_db
def test_animal_list_combines_all_filters(api_client, combined_filter_animal):
    """Fails if any CSV, compatibility, or shelter filter stops narrowing the list."""
    response = api_client.get(reverse('animal-list'), {
        'species': 'dog,cat', 'size': 'medium,small', 'age_range': 'young,adult',
        'gender': 'female,unknown', 'energy_level': 'low,medium',
        'good_with_kids': ' yes ', 'good_with_dogs': ' no ', 'good_with_cats': 'unknown',
        'shelter': combined_filter_animal.shelter_id,
    })

    assert response.status_code == status.HTTP_200_OK
    assert [row['id'] for row in response.json()['results']] == [combined_filter_animal.pk]


@pytest.mark.django_db
@pytest.mark.parametrize('field', ['page', 'page_size', 'shelter'])
@pytest.mark.parametrize('value', ['invalid', '1.5', '   '])
def test_animal_list_rejects_malformed_integer(api_client, field, value):
    """Fails if malformed numeric parameters crash the public list."""
    response = api_client.get(reverse('animal-list'), {field: value})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'error': f'{field} must be an integer'}


@pytest.mark.django_db
@pytest.mark.parametrize('field', ['page', 'page_size'])
def test_animal_list_rejects_empty_pagination_value(api_client, field):
    """Fails if an explicitly empty page parameter silently becomes a default."""
    response = api_client.get(reverse('animal-list'), {field: ''})

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {'error': f'{field} must be an integer'}


@pytest.mark.django_db
def test_animal_list_ignores_empty_shelter_filter(api_client, animal):
    """Fails if an empty optional shelter filter rejects the request."""
    response = api_client.get(reverse('animal-list'), {'shelter': ''})

    assert response.status_code == status.HTTP_200_OK
    assert [row['id'] for row in response.json()['results']] == [animal.pk]


@pytest.mark.django_db
def test_animal_list_returns_no_matches_for_missing_shelter(api_client, animal):
    """Fails if a valid but absent shelter identifier stops filtering animals."""
    response = api_client.get(reverse('animal-list'), {'shelter': animal.shelter_id + 1})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['count'] == 0
    assert response.json()['results'] == []


@pytest.mark.django_db
@pytest.mark.parametrize(('field', 'value', 'expected'), [
    ('page', -3, 1), ('page', 0, 1), ('page', 2, 2),
    ('page_size', -3, 1), ('page_size', 0, 1),
    ('page_size', 101, 100), ('page_size', 100, 100),
])
def test_animal_list_preserves_integer_limits(api_client, animal, field, value, expected):
    """Fails if integer pagination no longer preserves its existing limits."""
    response = api_client.get(reverse('animal-list'), {field: value})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()[field] == expected


@pytest.mark.django_db
def test_animal_list_returns_requested_page(api_client, shelter, animal):
    """Fails if pagination returns animals from the wrong slice."""
    AnimalFactory(shelter=shelter)
    response = api_client.get(reverse('animal-list'), {'page': 2, 'page_size': 1})

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['count'] == 2
    assert response.json()['total_pages'] == 2
    assert [row['id'] for row in response.json()['results']] == [animal.pk]


@pytest.mark.django_db
def test_animal_list_returns_empty_out_of_range_page(api_client, animal):
    """Fails if an out-of-range page repeats the last page or changes its metadata."""
    response = api_client.get(reverse('animal-list'), {'page': 5, 'page_size': 1})

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'count': 1, 'page': 5, 'page_size': 1, 'total_pages': 1, 'results': [],
    }


@pytest.mark.django_db
def test_animal_list_preserves_public_payload(api_client, animal, shelter):
    """Fails if optimizing the query changes any public animal field or metadata."""
    response = api_client.get(reverse('animal-list'))

    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        'count': 1, 'page': 1, 'page_size': 20, 'total_pages': 1,
        'results': [{
            'id': animal.pk, 'name': 'Luna', 'species': 'dog', 'breed': 'Labrador',
            'age_range': 'young', 'gender': 'female', 'size': 'medium',
            'status': 'published', 'is_vaccinated': True, 'is_sterilized': False,
            'energy_level': 'medium', 'good_with_kids': 'unknown',
            'good_with_dogs': 'unknown', 'good_with_cats': 'unknown',
            'shelter': shelter.pk, 'shelter_name': 'Happy Paws',
            'created_at': animal.created_at.isoformat().replace('+00:00', 'Z'),
        }],
    }


@pytest.mark.django_db
def test_animal_list_filters_by_energy_level(api_client, animal):
    """Fails if a single energy level stops excluding other energy levels."""
    matching = AnimalFactory(shelter=animal.shelter, energy_level='high')
    response = api_client.get(reverse('animal-list'), {'energy_level': 'high'})

    assert response.status_code == status.HTTP_200_OK
    assert [row['id'] for row in response.json()['results']] == [matching.pk]


@pytest.mark.django_db
def test_animal_list_excludes_archived_published_animals(api_client, animal):
    """Fails if eager loading accidentally exposes an archived published animal."""
    AnimalFactory(shelter=animal.shelter, archived_at=animal.created_at)
    response = api_client.get(reverse('animal-list'))

    assert response.status_code == status.HTTP_200_OK
    assert [row['id'] for row in response.json()['results']] == [animal.pk]


@pytest.mark.django_db
def test_animal_list_returns_only_published(api_client, shelter, animal):
    """Only published animals appear in the public list."""
    Animal.objects.create(
        shelter=shelter,
        name='Hidden',
        species=Animal.Species.CAT,
        status=Animal.Status.DRAFT,
    )
    response = api_client.get(reverse('animal-list'))

    assert response.status_code == status.HTTP_200_OK
    names = [a['name'] for a in response.json()['results']]
    assert 'Luna' in names
    assert 'Hidden' not in names


@pytest.mark.django_db
def test_animal_list_filters_by_species(api_client, shelter, animal):
    """Species query param filters the animal list."""
    Animal.objects.create(
        shelter=shelter,
        name='Michi',
        species=Animal.Species.CAT,
        status=Animal.Status.PUBLISHED,
    )
    response = api_client.get(reverse('animal-list'), {'species': 'cat'})

    assert response.status_code == status.HTTP_200_OK
    names = [a['name'] for a in response.json()['results']]
    assert 'Michi' in names
    assert 'Luna' not in names


@pytest.mark.django_db
def test_animal_list_filters_by_size(api_client, animal):
    """Size query param filters the animal list."""
    response = api_client.get(reverse('animal-list'), {'size': 'medium'})

    assert response.status_code == status.HTTP_200_OK
    results = response.json()['results']
    assert len(results) == 1
    assert results[0]['name'] == 'Luna'


@pytest.mark.django_db
def test_animal_detail_returns_existing(api_client, animal):
    """Detail endpoint returns a specific animal by pk."""
    response = api_client.get(reverse('animal-detail', args=[animal.pk]))

    assert response.status_code == status.HTTP_200_OK
    assert response.json()['name'] == 'Luna'


@pytest.mark.django_db
def test_animal_detail_returns_404_for_missing(api_client):
    """Detail endpoint returns 404 for non-existent pk."""
    response = api_client.get(reverse('animal-detail', args=[99999]))

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_animal_create_requires_auth(api_client):
    """Unauthenticated users cannot create animals."""
    response = api_client.post(
        reverse('animal-create'),
        {'name': 'Ghost'},
        format='json',
    )

    assert response.status_code == status.HTTP_401_UNAUTHORIZED


@pytest.mark.django_db
def test_animal_create_success(shelter_admin_client, shelter):
    """Authenticated user can create an animal."""
    response = shelter_admin_client.post(
        reverse('animal-create'),
        {
            'shelter': shelter.pk,
            'name': 'Rocky',
            'species': 'dog',
            'age_range': 'puppy',
            'gender': 'male',
            'size': 'small',
            'description': 'A tiny pup',
        },
        format='json',
    )

    assert response.status_code == status.HTTP_201_CREATED
    assert Animal.objects.filter(name='Rocky').exists()


@pytest.mark.django_db
def test_animal_update_by_shelter_owner(shelter_admin_client, animal):
    """Shelter owner can update their animal."""
    response = shelter_admin_client.patch(
        reverse('animal-update', args=[animal.pk]),
        {'name': 'Luna Updated'},
        format='json',
    )

    assert response.status_code == status.HTTP_200_OK
    animal.refresh_from_db()
    assert animal.name == 'Luna Updated'


@pytest.mark.django_db
def test_animal_update_denied_for_non_owner(authenticated_client, animal):
    """Non-owner cannot update an animal."""
    response = authenticated_client.patch(
        reverse('animal-update', args=[animal.pk]),
        {'name': 'Hijacked'},
        format='json',
    )

    assert response.status_code == status.HTTP_403_FORBIDDEN
    animal.refresh_from_db()
    assert animal.name == 'Luna'


@pytest.mark.django_db
def test_animal_delete_by_shelter_owner(shelter_admin_client, animal):
    """Shelter owner archives their animal (soft-delete, no CASCADE)."""
    pk = animal.pk
    response = shelter_admin_client.delete(reverse('animal-delete', args=[pk]))

    assert response.status_code == status.HTTP_204_NO_CONTENT
    animal.refresh_from_db()
    assert animal.archived_at is not None
    assert animal.status == animal.Status.ARCHIVED


@pytest.mark.django_db
def test_animal_delete_denied_for_non_owner(authenticated_client, animal):
    """Non-owner cannot delete an animal."""
    response = authenticated_client.delete(reverse('animal-delete', args=[animal.pk]))

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert Animal.objects.filter(pk=animal.pk).exists()


@pytest.mark.django_db
def test_animal_list_filters_by_age_range(api_client, animal):
    """Age range query param filters the animal list."""
    response = api_client.get(reverse('animal-list'), {'age_range': 'young'})

    assert response.status_code == status.HTTP_200_OK
    results = response.json()['results']
    assert len(results) == 1
    assert results[0]['name'] == 'Luna'


@pytest.mark.django_db
def test_animal_list_filters_by_shelter(api_client, animal, shelter):
    """Shelter query param filters the animal list."""
    response = api_client.get(reverse('animal-list'), {'shelter': shelter.pk})

    assert response.status_code == status.HTTP_200_OK
    results = response.json()['results']
    assert len(results) == 1
    assert results[0]['name'] == 'Luna'


@pytest.mark.django_db
def test_animal_list_filters_by_gender(api_client, animal):
    """Gender query param filters the animal list."""
    response = api_client.get(reverse('animal-list'), {'gender': 'female'})

    assert response.status_code == status.HTTP_200_OK
    results = response.json()['results']
    assert len(results) == 1
    assert results[0]['name'] == 'Luna'


@pytest.mark.django_db
def test_animal_create_returns_400_for_invalid_data(shelter_admin_client):
    """Invalid payload returns 400 with serializer errors."""
    response = shelter_admin_client.post(
        reverse('animal-create'),
        {},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_animal_update_returns_404_for_missing(shelter_admin_client):
    """Updating a non-existent animal returns 404."""
    response = shelter_admin_client.patch(
        reverse('animal-update', args=[99999]),
        {'name': 'Ghost'},
        format='json',
    )

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_animal_update_returns_400_for_invalid_data(shelter_admin_client, animal):
    """Invalid update payload returns 400."""
    response = shelter_admin_client.patch(
        reverse('animal-update', args=[animal.pk]),
        {'species': 'invalid_species'},
        format='json',
    )

    assert response.status_code == status.HTTP_400_BAD_REQUEST


@pytest.mark.django_db
def test_animal_delete_returns_404_for_missing(shelter_admin_client):
    """Deleting a non-existent animal returns 404."""
    response = shelter_admin_client.delete(reverse('animal-delete', args=[99999]))

    assert response.status_code == status.HTTP_404_NOT_FOUND


# ── Similar endpoint ─────────────────────────────────────────────────────────


@pytest.fixture(autouse=False)
def clear_cache():
    """Clear Django cache before and after similar endpoint tests."""
    from django.core.cache import cache
    cache.clear()
    yield
    cache.clear()


@pytest.mark.django_db
def test_animal_similar_returns_same_species_and_size(clear_cache, api_client, shelter, animal):
    """Similar endpoint returns animals with same species and size."""
    Animal.objects.create(
        shelter=shelter, name='Similar', species='dog', size='medium',
        status=Animal.Status.PUBLISHED,
    )
    Animal.objects.create(
        shelter=shelter, name='DiffSpecies', species='cat', size='medium',
        status=Animal.Status.PUBLISHED,
    )
    Animal.objects.create(
        shelter=shelter, name='DiffSize', species='dog', size='large',
        status=Animal.Status.PUBLISHED,
    )
    response = api_client.get(reverse('animal-similar', args=[animal.pk]))

    assert response.status_code == status.HTTP_200_OK
    names = [a['name'] for a in response.json()]
    assert 'Similar' in names
    assert 'DiffSpecies' not in names
    assert 'DiffSize' not in names


@pytest.mark.django_db
def test_animal_similar_excludes_self(clear_cache, api_client, shelter, animal):
    """Similar endpoint does not include the animal itself."""
    response = api_client.get(reverse('animal-similar', args=[animal.pk]))

    assert response.status_code == status.HTTP_200_OK
    ids = [a['id'] for a in response.json()]
    assert animal.pk not in ids


@pytest.mark.django_db
def test_animal_similar_returns_max_four(clear_cache, api_client, shelter, animal):
    """Similar endpoint returns at most 4 animals."""
    for i in range(6):
        Animal.objects.create(
            shelter=shelter, name=f'Sim{i}', species='dog', size='medium',
            status=Animal.Status.PUBLISHED,
        )
    response = api_client.get(reverse('animal-similar', args=[animal.pk]))

    assert response.status_code == status.HTTP_200_OK
    assert len(response.json()) <= 4


@pytest.mark.django_db
def test_animal_similar_excludes_unpublished(clear_cache, api_client, shelter, animal):
    """Similar endpoint excludes draft/archived animals."""
    Animal.objects.create(
        shelter=shelter, name='DraftSim', species='dog', size='medium',
        status=Animal.Status.DRAFT,
    )
    response = api_client.get(reverse('animal-similar', args=[animal.pk]))

    assert response.status_code == status.HTTP_200_OK
    names = [a['name'] for a in response.json()]
    assert 'DraftSim' not in names


@pytest.mark.django_db
def test_animal_similar_returns_404_for_missing(clear_cache, api_client):
    """Similar endpoint returns 404 for non-existent animal."""
    response = api_client.get(reverse('animal-similar', args=[99999]))

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.django_db
def test_animal_similar_prioritizes_same_shelter(clear_cache, api_client, shelter, animal, shelter_admin_user):
    """Similar endpoint prioritizes animals from the same shelter."""
    from base_feature_app.tests.factories import ShelterFactory

    other_shelter = ShelterFactory(owner=shelter_admin_user, name='Other Shelter')
    Animal.objects.create(
        shelter=other_shelter, name='OtherShelter', species='dog', size='medium',
        status=Animal.Status.PUBLISHED,
    )
    Animal.objects.create(
        shelter=shelter, name='SameShelter', species='dog', size='medium',
        status=Animal.Status.PUBLISHED,
    )
    response = api_client.get(reverse('animal-similar', args=[animal.pk]))

    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data[0]['name'] == 'SameShelter'
