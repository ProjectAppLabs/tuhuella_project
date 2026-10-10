"""Verify update serializers against real optional image libraries."""

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django_attachments.models import Attachment, Library
from PIL import Image

from base_feature_app.serializers.update_post_create_update import (
    UpdatePostCreateUpdateSerializer,
)
from base_feature_app.serializers.update_post_detail import UpdatePostDetailSerializer
from base_feature_app.serializers.update_post_list import UpdatePostListSerializer


@pytest.mark.django_db
def test_update_post_list_serializer_fields(update_post):
    """List serializer returns expected fields."""
    data = UpdatePostListSerializer(update_post).data

    assert data['id'] == update_post.pk
    assert data['title'] == 'Luna recovered!'
    assert data['shelter_name'] == 'Happy Paws'
    assert 'created_at' in data


@pytest.mark.django_db
def test_update_post_detail_serializer_includes_content(update_post):
    """Detail serializer includes content and updated_at."""
    data = UpdatePostDetailSerializer(update_post).data

    assert data['title'] == 'Luna recovered!'
    assert data['content'] == 'Luna is doing great after surgery.'
    assert 'updated_at' in data
    assert data['shelter_name'] == 'Happy Paws'


@pytest.mark.django_db
def test_update_post_create_update_serializer_valid(shelter):
    """Create serializer accepts valid data."""
    serializer = UpdatePostCreateUpdateSerializer(data={
        'shelter': shelter.pk,
        'title_es': 'New arrival',
        'content_es': 'We just rescued a kitten!',
    })

    assert serializer.is_valid(), serializer.errors


@pytest.mark.django_db
def test_update_post_create_update_serializer_rejects_missing_title(shelter):
    """Create serializer rejects missing title."""
    serializer = UpdatePostCreateUpdateSerializer(data={
        'shelter': shelter.pk,
        'content_es': 'Some content',
    })

    assert not serializer.is_valid()
    assert 'title_es' in serializer.errors


@pytest.fixture(params=['absent', 'empty', 'populated'])
def update_image(request, update_post, settings, tmp_path):
    """Prepare a real optional Library image in private media storage."""
    settings.MEDIA_ROOT = str(tmp_path)
    if request.param == 'absent':
        return update_post, None
    library = Library.objects.create(title='Update image')
    update_post.image = library
    update_post.save(update_fields=['image'])
    if request.param == 'empty':
        return update_post, None
    image_data = BytesIO()
    Image.new('RGB', (2, 2), 'green').save(image_data, format='PNG')
    attachment = Attachment.objects.create(
        library=library, rank=0,
        file=SimpleUploadedFile('update.png', image_data.getvalue(), 'image/png'),
    )
    library.primary_attachment = attachment
    library.save(update_fields=['primary_attachment'])
    return update_post, attachment.file.url


@pytest.mark.django_db
@pytest.mark.parametrize('serializer_class', [
    UpdatePostListSerializer,
    UpdatePostDetailSerializer,
    UpdatePostCreateUpdateSerializer,
])
def test_update_post_serializer_represents_library_image(serializer_class, update_image):
    """Image representation follows the real Library/Attachment relationship."""
    post, expected_url = update_image

    data = serializer_class(post).data

    assert data['image_url'] == expected_url
