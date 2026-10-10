"""Verify platform management permissions, filters and response fields."""

import pytest

from base_feature_app.models import AdoptionApplication
from base_feature_app.tests.factories import (
    AdoptionApplicationFactory,
    ShelterFactory,
    UserFactory,
)


@pytest.fixture
def web_manager(db):
    """Create an account authorized to manage platform records."""
    return UserFactory(email='manager@example.com', role='web_manager')


@pytest.fixture
def web_manager_client(api_client, web_manager):
    """Authenticate requests as a web manager."""
    api_client.force_authenticate(user=web_manager)
    return api_client


@pytest.mark.django_db
def test_web_manager_sees_all_applications(web_manager_client):
    """Expose applications across shelters to the web manager."""
    AdoptionApplicationFactory.create_batch(3)

    response = web_manager_client.get('/api/admin/applications/')

    assert response.status_code == 200
    assert response.data['count'] == 3


@pytest.mark.django_db
def test_adopter_is_forbidden_from_global_applications(authenticated_client):
    """Deny adopters access to the global application list."""
    AdoptionApplicationFactory()

    response = authenticated_client.get('/api/admin/applications/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_shelter_applications_filter_scopes_to_shelter(web_manager_client):
    """Restrict the shelter application list to the requested shelter."""
    shelter_a = ShelterFactory()
    shelter_b = ShelterFactory()
    AdoptionApplicationFactory(animal__shelter=shelter_a)
    AdoptionApplicationFactory(animal__shelter=shelter_a)
    AdoptionApplicationFactory(animal__shelter=shelter_b)

    response = web_manager_client.get(f'/api/admin/shelters/{shelter_a.id}/applications/')

    assert response.status_code == 200
    assert response.data['count'] == 2
    for app in response.data['results']:
        assert app['shelter_name'] == shelter_a.name


@pytest.mark.django_db
def test_shelter_admin_cannot_call_shelter_applications(shelter_admin_client):
    """Deny shelter administrators access to the platform application endpoint."""
    other = ShelterFactory()
    AdoptionApplicationFactory(animal__shelter=other)

    response = shelter_admin_client.get(f'/api/admin/shelters/{other.id}/applications/')

    assert response.status_code == 403


# --- admin_shelters_list ---

@pytest.mark.django_db
def test_admin_shelters_list_returns_all_shelters(web_manager_client):
    """web_manager can list all shelters."""
    ShelterFactory.create_batch(3)

    response = web_manager_client.get('/api/admin/shelters/all/')

    assert response.status_code == 200
    assert response.data['count'] == 3


@pytest.mark.django_db
def test_admin_shelters_list_keeps_owner_email(web_manager_client):
    """Retain owner account emails in the administrative shelter list."""
    shelter = ShelterFactory()

    response = web_manager_client.get('/api/admin/shelters/all/')

    assert response.status_code == 200
    assert response.json()['results'][0]['owner_email'] == shelter.owner.email


@pytest.mark.django_db
def test_admin_shelters_list_forbidden_for_non_manager(authenticated_client):
    """Adopter receives 403 on the admin shelters endpoint."""
    response = authenticated_client.get('/api/admin/shelters/all/')

    assert response.status_code == 403


@pytest.mark.django_db
def test_admin_shelters_list_filters_by_verification_status(web_manager_client):
    """verification_status query param restricts results to matching shelters."""
    ShelterFactory(verification_status='verified')
    ShelterFactory(verification_status='pending')

    response = web_manager_client.get('/api/admin/shelters/all/?verification_status=verified')

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['verification_status'] == 'verified'


@pytest.mark.django_db
def test_admin_shelters_list_filters_by_city(web_manager_client):
    """City filters restrict results to shelters in the matching city."""
    ShelterFactory(city='Bogotá')
    ShelterFactory(city='Medellín')

    response = web_manager_client.get('/api/admin/shelters/all/?city=Bogotá')

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['city'] == 'Bogotá'


# --- admin_applications_list filters ---

@pytest.mark.django_db
def test_admin_applications_list_filters_by_status(web_manager_client):
    """Status filters restrict results to applications with matching status."""
    AdoptionApplicationFactory(status=AdoptionApplication.Status.SUBMITTED)
    AdoptionApplicationFactory(status=AdoptionApplication.Status.REVIEWING)

    response = web_manager_client.get('/api/admin/applications/?status=submitted')

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['status'] == 'submitted'


@pytest.mark.django_db
def test_admin_applications_list_filters_by_shelter(web_manager_client):
    """Shelter filters restrict applications to animals in that shelter."""
    shelter_a = ShelterFactory()
    shelter_b = ShelterFactory()
    AdoptionApplicationFactory(animal__shelter=shelter_a)
    AdoptionApplicationFactory(animal__shelter=shelter_b)

    response = web_manager_client.get(f'/api/admin/applications/?shelter={shelter_a.id}')

    assert response.status_code == 200
    assert response.data['count'] == 1
    assert response.data['results'][0]['shelter_name'] == shelter_a.name


@pytest.mark.django_db
def test_admin_applications_list_returns_pagination_metadata(web_manager_client):
    """Pagination response includes count, page, page_size, and total_pages."""
    AdoptionApplicationFactory.create_batch(5)

    response = web_manager_client.get('/api/admin/applications/?page=1&page_size=2')

    assert response.status_code == 200
    assert response.data['count'] == 5
    assert response.data['page'] == 1
    assert response.data['page_size'] == 2
    assert response.data['total_pages'] == 3


# --- shelter_applications_list status filter ---

@pytest.mark.django_db
def test_shelter_applications_list_filters_by_status(web_manager_client):
    """Status filters on the shelter endpoint restrict application results."""
    shelter = ShelterFactory()
    AdoptionApplicationFactory(animal__shelter=shelter, status=AdoptionApplication.Status.SUBMITTED)
    AdoptionApplicationFactory(animal__shelter=shelter, status=AdoptionApplication.Status.REVIEWING)

    response = web_manager_client.get(f'/api/admin/shelters/{shelter.id}/applications/?status=submitted')

    assert response.status_code == 200
    assert response.data['count'] == 1


# --- _paginate error branch ---

@pytest.mark.django_db
def test_admin_applications_list_ignores_non_integer_page_param(web_manager_client):
    """Non-integer page param falls back to page=1 without error."""
    AdoptionApplicationFactory()

    response = web_manager_client.get('/api/admin/applications/?page=abc')

    assert response.status_code == 200
    assert response.data['page'] == 1
