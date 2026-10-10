import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

from base_feature_app.serializers.shelter_create_update import (
    ShelterCreateUpdateSerializer,
)
from base_feature_app.serializers.shelter_detail import ShelterDetailSerializer
from base_feature_app.serializers.shelter_list import ShelterListSerializer


@pytest.fixture(autouse=True)
def fast_shelter_password_hashing(settings):
    """Serializer privacy tests do not need the production password hashing cost."""
    settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']


@pytest.mark.django_db
def test_shelter_list_serializer_fields(shelter):
    """List serializer returns expected fields."""
    data = ShelterListSerializer(shelter).data

    assert data['id'] == shelter.pk
    assert data['name'] == 'Happy Paws'
    assert data['city'] == 'Bogotá'
    assert data['verification_status'] == 'verified'
    assert 'owner_email' not in data
    assert 'created_at' in data


@pytest.mark.django_db
def test_shelter_detail_serializer_fields(shelter):
    """Detail serializer returns all expected fields including computed ones."""
    data = ShelterDetailSerializer(shelter).data

    assert data['name'] == 'Happy Paws'
    assert data['legal_name'] == 'Happy Paws Foundation'
    assert data['description'] == 'A great shelter'
    assert data['phone'] == '3001234567'
    assert data['email'] == 'info@happypaws.org'
    assert data['is_verified'] is True
    assert 'updated_at' in data


@pytest.mark.django_db
def test_shelter_detail_serializer_omits_owner_email_without_request(shelter):
    """A serializer without an authenticated request must not expose account data."""
    data = ShelterDetailSerializer(shelter).data

    assert 'owner_email' not in data


@pytest.mark.django_db
def test_shelter_create_update_serializer_valid(shelter_admin_user):
    """Create serializer accepts valid data."""
    serializer = ShelterCreateUpdateSerializer(data={
        'name': 'Test Shelter',
        'city': 'Cali',
        'description_es': 'New shelter',
        'phone': '3009999999',
        'email': 'test@shelter.org',
    })

    assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db
def test_shelter_create_update_serializer_rejects_missing_name():
    """Create serializer rejects missing name."""
    serializer = ShelterCreateUpdateSerializer(data={
        'city': 'Cali',
    })

    assert not serializer.is_valid()
    assert 'name' in serializer.errors


@pytest.mark.django_db
def test_shelter_detail_serializer_video_url_empty_when_no_video(shelter):
    """video_url is an empty string when the shelter has no uploaded video."""
    data = ShelterDetailSerializer(shelter).data

    assert 'video_url' in data
    assert data['video_url'] == ''


@pytest.mark.django_db
def test_shelter_detail_serializer_video_url_populated_when_video_set(
    shelter, settings, tmp_path
):
    """video_url returns the uploaded file URL under /media/shelters/videos/."""
    # quality: disable global_state_leak (pytest-django settings fixture is override_settings equivalent — auto-restores after test)
    settings.MEDIA_ROOT = str(tmp_path)

    shelter.video = SimpleUploadedFile(
        'demo.mp4', b'\x00\x00\x00\x18ftypmp42', content_type='video/mp4'
    )
    shelter.save()

    data = ShelterDetailSerializer(shelter).data

    assert data['video_url'].startswith('/media/shelters/videos/')
    assert data['video_url'].endswith('.mp4')


@pytest.mark.django_db
def test_shelter_create_update_serializer_accepts_blank_website():
    """Website is optional; empty string is valid."""
    serializer = ShelterCreateUpdateSerializer(data={
        'name': 'No Web Shelter',
        'city': 'Medellín',
        'description_es': 'Sin sitio web',
        'phone': '3001112233',
        'website': '',
    })

    assert serializer.is_valid(), serializer.errors


# ── list serializer: image URLs come from the Library, not the field ─────────
# Regression for the HTTP 500 on GET /api/shelters/ (measured 2026-08-03, 4/4
# calls): logo and cover_image are SingleImageField, i.e. FKs to a
# django_attachments Library — NOT file fields. `library.url` does not exist, so
# any shelter that actually HAS an image crashed the whole list endpoint with
# `AttributeError: 'Library' object has no attribute 'url'`. The pre-existing
# tests never caught it because the `shelter` fixture leaves both images unset,
# which short-circuits the `if` before the attribute access.

@pytest.mark.django_db
def test_shelter_list_serializer_survives_a_shelter_that_has_a_cover_image(shelter):
    """A shelter WITH a cover Library serializes instead of raising AttributeError."""
    from django_attachments.models import Library

    shelter.cover_image = Library.objects.create(title='Cover: Happy Paws')
    shelter.save(update_fields=['cover_image'])

    data = ShelterListSerializer(shelter).data

    # No primary attachment yet ⇒ empty string, the same contract the detail
    # serializer and library_primary_url already honour.
    assert data['cover_image_url'] == ''


@pytest.mark.django_db
def test_shelter_list_serializer_survives_a_shelter_that_has_a_logo(shelter):
    """A shelter WITH a logo Library serializes instead of raising AttributeError."""
    from django_attachments.models import Library

    shelter.logo = Library.objects.create(title='Logo: Happy Paws')
    shelter.save(update_fields=['logo'])

    data = ShelterListSerializer(shelter).data

    assert data['logo_url'] == ''
