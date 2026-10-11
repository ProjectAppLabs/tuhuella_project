"""Verify public and staff blog endpoints with private editorial media."""

from io import BytesIO

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import DatabaseError, connection
from django.urls import reverse
from django_attachments.models import Attachment, Library
from PIL import Image

from base_feature_app.models import BlogPost

# ---------------------------------------------------------------------------
# Public endpoints
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_list_blog_posts_returns_published_only(api_client, blog_post, draft_blog_post):
    """Public listing only returns published posts."""
    url = reverse('list-blog-posts')
    response = api_client.get(url)

    assert response.status_code == 200
    slugs = [p['slug'] for p in response.data['results']]
    assert blog_post.slug in slugs
    assert draft_blog_post.slug not in slugs


@pytest.mark.django_db
def test_list_blog_posts_pagination(api_client, blog_post):
    """Response includes pagination metadata."""
    url = reverse('list-blog-posts')
    response = api_client.get(url)

    assert response.status_code == 200
    assert 'count' in response.data
    assert 'page' in response.data
    assert 'total_pages' in response.data
    assert response.data['count'] >= 1


@pytest.mark.django_db
def test_retrieve_blog_post_by_slug(api_client, blog_post):
    """Public detail returns a published post by slug."""
    url = reverse('retrieve-blog-post', kwargs={'slug': blog_post.slug})
    response = api_client.get(url)

    assert response.status_code == 200
    assert response.data['slug'] == blog_post.slug
    assert response.data['title'] == blog_post.title_es


@pytest.mark.django_db
def test_retrieve_unpublished_post_returns_404(api_client, draft_blog_post):
    """Public detail returns 404 for unpublished posts."""
    url = reverse('retrieve-blog-post', kwargs={'slug': draft_blog_post.slug})
    response = api_client.get(url)

    assert response.status_code == 404


@pytest.mark.django_db
def test_list_blog_posts_filters_by_category(api_client, blog_post):
    """Public listing filters by ?category param."""
    url = reverse('list-blog-posts')
    response = api_client.get(url, {'category': blog_post.category})

    assert response.status_code == 200
    assert response.data['count'] >= 1


@pytest.mark.django_db
def test_list_blog_posts_search_filters_by_text(api_client, blog_post):
    """Public listing filters by ?search param across bilingual fields."""
    url = reverse('list-blog-posts')
    response = api_client.get(url, {'search': blog_post.title_es[:10]})

    assert response.status_code == 200
    slugs = [p['slug'] for p in response.data['results']]
    assert blog_post.slug in slugs


@pytest.mark.django_db
def test_list_blog_posts_invalid_page_defaults_to_one(api_client, blog_post):
    """Invalid page param falls back to page 1."""
    url = reverse('list-blog-posts')
    response = api_client.get(url, {'page': 'abc'})

    assert response.status_code == 200
    assert response.data['page'] == 1


@pytest.mark.django_db
def test_list_blog_posts_invalid_page_size_defaults_to_six(api_client, blog_post):
    """Invalid page_size param falls back to 6."""
    url = reverse('list-blog-posts')
    response = api_client.get(url, {'page_size': 'xyz'})

    assert response.status_code == 200
    assert response.data['page_size'] == 6


# ---------------------------------------------------------------------------
# Admin endpoints — authentication required
# ---------------------------------------------------------------------------

@pytest.mark.django_db
def test_admin_list_requires_staff(api_client):
    """Admin list returns 401/403 for anonymous users."""
    url = reverse('list-admin-blog-posts')
    response = api_client.get(url)

    assert response.status_code in (401, 403)


@pytest.mark.django_db
def test_admin_list_includes_drafts(admin_client, blog_post, draft_blog_post):
    """Admin list returns both published and draft posts."""
    url = reverse('list-admin-blog-posts')
    response = admin_client.get(url)

    assert response.status_code == 200
    ids = [p['id'] for p in response.data['results']]
    assert blog_post.id in ids
    assert draft_blog_post.id in ids


@pytest.mark.django_db
def test_admin_create_blog_post(admin_client):
    """Admin can create a new blog post."""
    url = reverse('create-blog-post')
    data = {
        'title_es': 'Nuevo artículo',
        'title_en': 'New article',
        'excerpt_es': 'Resumen',
        'excerpt_en': 'Summary',
        'category': 'adopcion',
        'author': 'tuhuella-team',
    }
    response = admin_client.post(url, data, format='json')

    assert response.status_code == 201
    assert response.data['title_es'] == 'Nuevo artículo'
    assert BlogPost.objects.filter(title_es='Nuevo artículo').exists()


@pytest.mark.django_db
def test_admin_retrieve_blog_post(admin_client, blog_post):
    """Admin can retrieve full post detail by ID."""
    url = reverse('retrieve-admin-blog-post', kwargs={'post_id': blog_post.id})
    response = admin_client.get(url)

    assert response.status_code == 200
    assert response.data['id'] == blog_post.id
    assert 'title_es' in response.data
    assert 'title_en' in response.data


@pytest.mark.django_db
def test_admin_update_blog_post(admin_client, blog_post):
    """Admin can partially update a post."""
    url = reverse('update-blog-post', kwargs={'post_id': blog_post.id})
    response = admin_client.patch(url, {'title_es': 'Título actualizado'}, format='json')

    assert response.status_code == 200
    blog_post.refresh_from_db()
    assert blog_post.title_es == 'Título actualizado'


@pytest.mark.django_db
def test_admin_delete_blog_post(admin_client, blog_post):
    """Admin archives a post (soft-delete, unpublishes)."""
    post_id = blog_post.id
    url = reverse('delete-blog-post', kwargs={'post_id': post_id})
    response = admin_client.delete(url)

    assert response.status_code == 204
    blog_post.refresh_from_db()
    assert blog_post.archived_at is not None
    assert blog_post.is_published is False


@pytest.mark.django_db
def test_admin_duplicate_blog_post(admin_client, blog_post):
    """Duplicating a post creates a new draft copy."""
    blog_post.is_featured = True
    blog_post.save(update_fields=['is_featured'])
    url = reverse('duplicate-blog-post', kwargs={'post_id': blog_post.id})
    response = admin_client.post(url)

    assert response.status_code == 201
    assert response.data['is_published'] is False
    assert '(copia)' in response.data['title_es']
    assert BlogPost.objects.count() == 2
    copy = BlogPost.objects.get(pk=response.data['id'])
    assert copy.slug != blog_post.slug
    assert copy.published_at is None
    assert copy.is_featured is False


@pytest.mark.django_db
def test_admin_get_json_template(admin_client):
    """JSON template endpoint returns expected structure."""
    url = reverse('blog-json-template')
    response = admin_client.get(url)

    assert response.status_code == 200
    assert 'title_es' in response.data
    assert 'content_json_es' in response.data
    assert '_available_categories' in response.data


@pytest.mark.django_db
def test_admin_create_from_json(admin_client):
    """Admin can create a post from a full JSON payload."""
    url = reverse('create-blog-post-from-json')
    data = {
        'title_es': 'Post desde JSON',
        'title_en': 'Post from JSON',
        'excerpt_es': 'Resumen JSON',
        'excerpt_en': 'JSON Summary',
        'content_json_es': {'intro': 'Hola', 'sections': []},
        'category': 'nutricion',
    }
    response = admin_client.post(url, data, format='json')

    assert response.status_code == 201
    assert response.data['title_es'] == 'Post desde JSON'
    assert BlogPost.objects.filter(title_es='Post desde JSON').exists()


@pytest.mark.django_db
def test_admin_calendar_returns_posts_in_range(admin_client, blog_post):
    """Calendar endpoint returns posts within the date range."""
    pub_date = blog_post.published_at
    start = (pub_date.date()).isoformat()
    end = (pub_date.date()).isoformat()
    url = reverse('blog-calendar')

    response = admin_client.get(url, {'start': start, 'end': end})

    assert response.status_code == 200
    ids = [p['id'] for p in response.data]
    assert blog_post.id in ids


@pytest.mark.django_db
def test_admin_calendar_missing_params_returns_400(admin_client):
    """Calendar endpoint requires start and end params."""
    url = reverse('blog-calendar')
    response = admin_client.get(url)

    assert response.status_code == 400


@pytest.mark.django_db
def test_admin_calendar_invalid_date_returns_400(admin_client):
    """Calendar endpoint rejects invalid date format."""
    url = reverse('blog-calendar')
    response = admin_client.get(url, {'start': 'not-a-date', 'end': 'bad'})

    assert response.status_code == 400


@pytest.mark.django_db
def test_admin_upload_cover_image_requires_file(admin_client, blog_post):
    """Cover image upload returns 400 when no file is provided."""
    url = reverse('upload-blog-cover-image', kwargs={'post_id': blog_post.id})
    response = admin_client.post(url)

    assert response.status_code == 400
    assert 'cover_image' in response.data
    assert Library.objects.count() == 0
    assert Attachment.objects.count() == 0
    blog_post.refresh_from_db()
    assert blog_post.cover_image_id is None


@pytest.mark.django_db
def test_regular_user_cannot_access_admin_endpoints(authenticated_client):
    """Non-staff users get 403 on admin endpoints."""
    url = reverse('list-admin-blog-posts')
    response = authenticated_client.get(url)

    assert response.status_code == 403


@pytest.fixture
def cover_upload(settings, tmp_path):
    """Return a fresh valid PNG upload backed by private media storage."""
    settings.MEDIA_ROOT = str(tmp_path)
    image_data = BytesIO()
    Image.new('RGB', (3, 2), 'blue').save(image_data, format='PNG')
    return SimpleUploadedFile('cover.png', image_data.getvalue(), 'image/png')


@pytest.fixture
def illustrated_blog(blog_post, cover_upload):
    """Attach an existing illustrated Library for replacement safety tests."""
    library = Library.objects.create(title='Original cover')
    attachment = Attachment.objects.create(library=library, rank=0, file=cover_upload)
    library.primary_attachment = attachment
    library.save(update_fields=['primary_attachment'])
    blog_post.cover_image = library
    blog_post.save(update_fields=['cover_image'])
    return blog_post


@pytest.fixture
def shared_cover_blog(illustrated_blog, draft_blog_post):
    """Provide an archived second article referencing the original cover."""
    from django.utils import timezone

    draft_blog_post.cover_image = illustrated_blog.cover_image
    draft_blog_post.archived_at = timezone.now()
    draft_blog_post.save(update_fields=['cover_image', 'archived_at'])
    return illustrated_blog, draft_blog_post


@pytest.fixture
def editorial_blog(blog_post):
    """Set non-default bilingual metadata and structured editorial content."""
    blog_post.author = 'laura-blanco'
    blog_post.cover_image_credit = 'Photo Author'
    blog_post.cover_image_credit_url = 'https://example.test/photographer'
    blog_post.meta_keywords_es = 'adopción,perros'
    blog_post.meta_keywords_en = 'adoption,dogs'
    blog_post.content_json_es = {'intro': 'ES', 'sections': [{'heading': 'Original ES'}]}
    blog_post.content_json_en = {'intro': 'EN', 'sections': [{'heading': 'Original EN'}]}
    blog_post.sources = [{'name': 'Original source', 'url': 'https://example.test/source'}]
    blog_post.is_featured = True
    blog_post.save()
    return blog_post


@pytest.mark.django_db
def test_admin_upload_cover_persists_library(admin_client, blog_post, cover_upload):
    """A valid multipart image becomes an Attachment owned by the new cover Library."""
    expected_bytes = cover_upload.read()
    cover_upload.seek(0)
    url = reverse('upload-blog-cover-image', kwargs={'post_id': blog_post.pk})

    response = admin_client.post(url, {'cover_image': cover_upload}, format='multipart')

    assert response.status_code == 200
    blog_post.refresh_from_db()
    attachment = blog_post.cover_image.primary_attachment
    assert response.data['cover_image'] == blog_post.cover_image_id
    assert response.data['cover_image_display'] == attachment.file.url
    assert attachment.library_id == blog_post.cover_image_id
    assert attachment.image_width == 3
    assert attachment.image_height == 2
    with attachment.file.open('rb') as stored:
        assert stored.read() == expected_bytes


@pytest.mark.django_db
@pytest.mark.parametrize('lang', ['es', 'en'])
def test_public_blog_represents_uploaded_cover(admin_client, api_client, blog_post, cover_upload, lang):
    """Public bilingual details expose the persisted uploaded cover URL."""
    upload_url = reverse('upload-blog-cover-image', kwargs={'post_id': blog_post.pk})
    uploaded = admin_client.post(upload_url, {'cover_image': cover_upload}, format='multipart')
    assert uploaded.status_code == 200

    response = api_client.get(reverse('retrieve-blog-post', kwargs={'slug': blog_post.slug}), {'lang': lang})

    assert response.status_code == 200
    assert response.data['cover_image'] == uploaded.data['cover_image_display']
    assert response.data['title'] == getattr(blog_post, f'title_{lang}')


@pytest.mark.django_db
def test_admin_upload_cover_rejects_invalid_image(admin_client, blog_post, settings, tmp_path):
    """Invalid image bytes are rejected before creating rows or files."""
    settings.MEDIA_ROOT = str(tmp_path)
    invalid = SimpleUploadedFile('fake.png', b'not an image', 'image/png')
    url = reverse('upload-blog-cover-image', kwargs={'post_id': blog_post.pk})

    response = admin_client.post(url, {'cover_image': invalid}, format='multipart')

    assert response.status_code == 400
    assert 'cover_image' in response.data
    assert Library.objects.count() == 0
    assert Attachment.objects.count() == 0
    assert list(tmp_path.rglob('*')) == []
    blog_post.refresh_from_db()
    assert blog_post.cover_image_id is None


@pytest.mark.django_db
def test_admin_upload_cover_preserves_shared_previous_library(admin_client, shared_cover_blog):
    """Replacing a cover leaves archived references and their original file intact."""
    post, archived = shared_cover_blog
    old_library = post.cover_image
    old_attachment = old_library.primary_attachment
    old_name = old_attachment.file.name
    with old_attachment.file.open('rb') as stored:
        image_bytes = stored.read()
    replacement = SimpleUploadedFile('replacement.png', image_bytes, 'image/png')

    response = admin_client.post(
        reverse('upload-blog-cover-image', kwargs={'post_id': post.pk}),
        {'cover_image': replacement}, format='multipart',
    )

    assert response.status_code == 200
    post.refresh_from_db()
    archived.refresh_from_db()
    assert post.cover_image_id != old_library.pk
    assert archived.cover_image_id == old_library.pk
    assert Library.objects.count() == 2
    assert Attachment.objects.count() == 2
    assert old_attachment.file.storage.exists(old_name)
    with old_attachment.file.open('rb') as stored:
        assert stored.read() == image_bytes


@pytest.mark.django_db
@pytest.mark.parametrize('failure_table', ['django_attachments_attachment', 'base_feature_app_blogpost'])
def test_admin_upload_cover_compensates_failed_database_write(
    admin_client, shared_cover_blog, failure_table, tmp_path,
):
    """A database failure after writing new media removes only that request's file."""
    post, archived = shared_cover_blog
    old_library_id = post.cover_image_id
    old_file = post.cover_image.primary_attachment.file
    with old_file.open('rb') as stored:
        original_bytes = stored.read()
    existing_files = sorted(path for path in tmp_path.rglob('*') if path.is_file())
    replacement = SimpleUploadedFile('replacement.png', original_bytes, 'image/png')

    def fail_database_write(execute, sql, params, many, context):
        """Raise at the database boundary once the new image has been stored."""
        if failure_table in sql and sql.lstrip().upper().startswith(('INSERT', 'UPDATE')):
            raise DatabaseError('Injected private database write failure')
        return execute(sql, params, many, context)

    with connection.execute_wrapper(fail_database_write):
        with pytest.raises(DatabaseError, match='Injected private database write failure'):
            admin_client.post(
                reverse('upload-blog-cover-image', kwargs={'post_id': post.pk}),
                {'cover_image': replacement}, format='multipart',
            )

    post.refresh_from_db()
    archived.refresh_from_db()
    assert post.cover_image_id == old_library_id
    assert archived.cover_image_id == old_library_id
    assert Library.objects.count() == 1
    assert Attachment.objects.count() == 1
    assert sorted(path for path in tmp_path.rglob('*') if path.is_file()) == existing_files
    with old_file.open('rb') as stored:
        assert stored.read() == original_bytes


@pytest.mark.django_db
@pytest.mark.parametrize('endpoint', ['upload-blog-cover-image', 'duplicate-blog-post'])
def test_editorial_writes_reject_non_staff(authenticated_client, blog_post, cover_upload, endpoint):
    """Non-staff requests cannot change editorial data or create media."""
    url = reverse(endpoint, kwargs={'post_id': blog_post.pk})

    response = authenticated_client.post(url, {'cover_image': cover_upload}, format='multipart')

    assert response.status_code == 403
    assert BlogPost.objects.count() == 1
    assert Library.objects.count() == 0
    assert Attachment.objects.count() == 0


@pytest.mark.django_db
@pytest.mark.parametrize('field', [
    'author', 'cover_image_credit', 'cover_image_credit_url', 'meta_keywords_es', 'meta_keywords_en',
])
def test_duplicate_blog_preserves_editorial_metadata(admin_client, editorial_blog, field):
    """Duplicating an article preserves this non-default editorial field."""
    original_value = getattr(editorial_blog, field)

    response = admin_client.post(reverse('duplicate-blog-post', kwargs={'post_id': editorial_blog.pk}))

    assert response.status_code == 201
    copy = BlogPost.objects.get(pk=response.data['id'])
    editorial_blog.refresh_from_db()
    assert response.data[field] == original_value
    assert getattr(copy, field) == original_value
    assert getattr(editorial_blog, field) == original_value


@pytest.mark.django_db
@pytest.mark.parametrize('field', ['content_json_es', 'content_json_en', 'sources'])
def test_duplicate_blog_content_remains_independent(admin_client, editorial_blog, field):
    """Editing duplicated structured content leaves the original persisted content unchanged."""
    original_value = getattr(editorial_blog, field)
    response = admin_client.post(reverse('duplicate-blog-post', kwargs={'post_id': editorial_blog.pk}))
    assert response.status_code == 201
    copy = BlogPost.objects.get(pk=response.data['id'])
    replacements = {'content_json_es': {}, 'content_json_en': {}, 'sources': []}
    setattr(copy, field, replacements[field])

    copy.save(update_fields=[field])

    editorial_blog.refresh_from_db()
    assert getattr(editorial_blog, field) == original_value
