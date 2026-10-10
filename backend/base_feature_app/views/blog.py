import copy as _copy
import logging
import math

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from rest_framework import serializers, status
from rest_framework.decorators import api_view, parser_classes, permission_classes
from rest_framework.parsers import MultiPartParser
from rest_framework.permissions import AllowAny, IsAdminUser
from rest_framework.response import Response
from django_attachments.models import Attachment, Library

from base_feature_app.models import BlogPost
from base_feature_app.serializers.blog import (
    BlogPostAdminDetailSerializer,
    BlogPostAdminListSerializer,
    BlogPostCreateUpdateSerializer,
    BlogPostDetailSerializer,
    BlogPostFromJSONSerializer,
    BlogPostListSerializer,
    AVAILABLE_CATEGORIES,
    BLOG_JSON_TEMPLATE,
)


logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Public endpoints (no auth required)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([AllowAny])
def list_blog_posts(request):
    """
    List published blog posts with pagination.
    Accepts ?lang=es|en, ?page=1, ?page_size=6 query params.
    Returns {results, count, page, page_size, total_pages}.
    """
    qs = BlogPost.objects.filter(
        is_published=True, archived_at__isnull=True,
    ).select_related('cover_image__primary_attachment')

    category = request.query_params.get('category', '').strip()
    search = request.query_params.get('search', '').strip()

    if category:
        qs = qs.filter(category=category)
    if search:
        qs = qs.filter(
            Q(title_es__icontains=search) | Q(title_en__icontains=search)
            | Q(excerpt_es__icontains=search) | Q(excerpt_en__icontains=search)
            | Q(content_es__icontains=search) | Q(content_en__icontains=search)
        )

    try:
        page = max(1, int(request.query_params.get('page', 1)))
    except (ValueError, TypeError):
        page = 1
    try:
        page_size = min(50, max(1, int(request.query_params.get('page_size', 6))))
    except (ValueError, TypeError):
        page_size = 6

    total = qs.count()
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = min(page, total_pages)

    start = (page - 1) * page_size
    end = start + page_size
    page_qs = qs[start:end]

    serializer = BlogPostListSerializer(
        page_qs, many=True, context={'request': request}
    )
    return Response({
        'results': serializer.data,
        'count': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([AllowAny])
def retrieve_blog_post(request, slug):
    """
    Retrieve a single published blog post by slug.
    Accepts ?lang=es|en query param (default 'es').
    Returns 404 if not found or not published.
    """
    post = get_object_or_404(
        BlogPost,
        slug=slug,
        is_published=True,
        archived_at__isnull=True,
    )
    serializer = BlogPostDetailSerializer(
        post, context={'request': request}
    )
    return Response(serializer.data, status=status.HTTP_200_OK)


# ---------------------------------------------------------------------------
# Admin endpoints (staff only)
# ---------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsAdminUser])
def list_admin_blog_posts(request):
    """
    List all blog posts (including drafts) for admin management.
    Supports pagination via ?page=N&page_size=N query params.
    Returns all bilingual fields.
    """
    qs = BlogPost.objects.all().select_related('cover_image__primary_attachment')

    page = int(request.query_params.get('page', 1))
    page_size = int(request.query_params.get('page_size', 15))
    page = max(1, page)
    page_size = max(1, min(page_size, 100))

    total = qs.count()
    total_pages = max(1, math.ceil(total / page_size))
    start = (page - 1) * page_size
    end = start + page_size

    serializer = BlogPostAdminListSerializer(qs[start:end], many=True)
    return Response({
        'results': serializer.data,
        'count': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_blog_post(request):
    """
    Create a new blog post.
    """
    serializer = BlogPostCreateUpdateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    post = serializer.save()
    detail = BlogPostAdminDetailSerializer(post)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def retrieve_admin_blog_post(request, post_id):
    """
    Retrieve full blog post detail for admin editing.
    Returns all bilingual fields.
    """
    post = get_object_or_404(BlogPost, pk=post_id)
    serializer = BlogPostAdminDetailSerializer(post)
    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(['PATCH'])
@permission_classes([IsAdminUser])
def update_blog_post(request, post_id):
    """
    Update a blog post's fields.
    """
    post = get_object_or_404(BlogPost, pk=post_id)
    serializer = BlogPostCreateUpdateSerializer(
        post, data=request.data, partial=True
    )
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    serializer.save()
    detail = BlogPostAdminDetailSerializer(post)
    return Response(detail.data, status=status.HTTP_200_OK)


@api_view(['DELETE'])
@permission_classes([IsAdminUser])
def delete_blog_post(request, post_id):
    """
    Delete a blog post.
    """
    post = get_object_or_404(BlogPost, pk=post_id)
    post.archived_at = timezone.now()
    post.is_published = False
    post.save(update_fields=['archived_at', 'is_published', 'updated_at'])
    return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_blog_post_from_json(request):
    """
    Create a blog post from a complete JSON payload.
    """
    serializer = BlogPostFromJSONSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data
    post = BlogPost.objects.create(
        title_es=data['title_es'],
        title_en=data['title_en'],
        excerpt_es=data['excerpt_es'],
        excerpt_en=data['excerpt_en'],
        content_json_es=data['content_json_es'],
        content_json_en=data.get('content_json_en') or {},
        cover_image_url=data.get('cover_image_url', ''),
        sources=data.get('sources', []),
        category=data.get('category', ''),
        read_time_minutes=data.get('read_time_minutes', 0),
        is_featured=data.get('is_featured', False),
        is_published=data.get('is_published', False),
        author=data.get('author', 'tuhuella-team'),
        meta_title_es=data.get('meta_title_es', ''),
        meta_title_en=data.get('meta_title_en', ''),
        meta_description_es=data.get('meta_description_es', ''),
        meta_description_en=data.get('meta_description_en', ''),
        meta_keywords_es=data.get('meta_keywords_es', ''),
        meta_keywords_en=data.get('meta_keywords_en', ''),
        cover_image_credit=data.get('cover_image_credit', ''),
        cover_image_credit_url=data.get('cover_image_credit_url', ''),
    )

    detail = BlogPostAdminDetailSerializer(post)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def get_blog_json_template(request):
    """
    Return a downloadable JSON template for blog post creation.
    Includes all section types with placeholder content.
    """
    template = {
        'title_es': 'Título del artículo en español',
        'title_en': 'Article title in English',
        'excerpt_es': 'Resumen corto en español (1-2 oraciones).',
        'excerpt_en': 'Short summary in English (1-2 sentences).',
        'author': 'tuhuella-team',
        'content_json_es': _copy.deepcopy(BLOG_JSON_TEMPLATE),
        'content_json_en': _copy.deepcopy(BLOG_JSON_TEMPLATE),
        'cover_image_url': '',
        'cover_image_credit': '',
        'cover_image_credit_url': '',
        'sources': [
            {'name': 'Source Name', 'url': 'https://example.com'},
        ],
        'category': 'adopcion',
        'read_time_minutes': 8,
        'is_featured': False,
        'is_published': False,
        'meta_title_es': '',
        'meta_title_en': '',
        'meta_description_es': '',
        'meta_description_en': '',
        'meta_keywords_es': '',
        'meta_keywords_en': '',
        '_available_categories': AVAILABLE_CATEGORIES,
    }
    return Response(template, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAdminUser])
def duplicate_blog_post(request, post_id):
    """
    Duplicate a blog post: creates a deep copy reset to draft status.
    """
    post = get_object_or_404(BlogPost, pk=post_id)

    new_post = BlogPost.objects.create(
        title_es=f'{post.title_es} (copia)',
        title_en=f'{post.title_en} (copy)',
        slug='',
        excerpt_es=post.excerpt_es,
        excerpt_en=post.excerpt_en,
        content_es=post.content_es,
        content_en=post.content_en,
        content_json_es=_copy.deepcopy(post.content_json_es),
        content_json_en=_copy.deepcopy(post.content_json_en),
        cover_image_url=post.cover_image_url,
        cover_image_credit=post.cover_image_credit,
        cover_image_credit_url=post.cover_image_credit_url,
        sources=_copy.deepcopy(post.sources),
        category=post.category,
        read_time_minutes=post.read_time_minutes,
        is_featured=False,
        author=post.author,
        meta_title_es=post.meta_title_es,
        meta_title_en=post.meta_title_en,
        meta_description_es=post.meta_description_es,
        meta_description_en=post.meta_description_en,
        meta_keywords_es=post.meta_keywords_es,
        meta_keywords_en=post.meta_keywords_en,
        is_published=False,
        published_at=None,
    )

    detail = BlogPostAdminDetailSerializer(new_post)
    return Response(detail.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([IsAdminUser])
@parser_classes([MultiPartParser])
def upload_blog_cover_image(request, post_id):
    """
    Upload a cover image file for a blog post.
    Expects multipart/form-data with a 'cover_image' file field.
    """
    post = get_object_or_404(BlogPost, pk=post_id)
    cover = request.FILES.get('cover_image')
    if not cover:
        return Response(
            {'cover_image': 'No file provided.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        cover = serializers.ImageField().run_validation(cover)
    except (serializers.ValidationError, DjangoValidationError) as exc:
        detail = getattr(exc, 'detail', getattr(exc, 'messages', []))
        return Response({'cover_image': detail}, status=status.HTTP_400_BAD_REQUEST)

    attachment = None
    try:
        with transaction.atomic():
            library = Library.objects.create(title=f'Cover: {post.title_es}'[:255])
            attachment = Attachment(library=library, rank=0)
            attachment.file.save(cover.name, cover, save=False)
            attachment.save()
            library.primary_attachment = attachment
            library.save(update_fields=['primary_attachment'])
            # A previous library can be shared, including by archived records.
            post.cover_image = library
            post.save(update_fields=['cover_image', 'updated_at'])
            detail = BlogPostAdminDetailSerializer(post).data
    except Exception:
        # Storage writes are not rolled back with database rows. Only remove
        # this request's new file; existing libraries and files stay intact.
        if attachment is not None and attachment.file.name:
            attachment.file.storage.delete(attachment.file.name)
        raise

    return Response(detail, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAdminUser])
def blog_calendar(request):
    """
    Return blog posts within a date range for calendar display.

    Query params:
      - start: YYYY-MM-DD (required)
      - end: YYYY-MM-DD (required)

    Returns posts that have published_at within [start, end],
    plus drafts created within that range.
    """
    start_str = request.query_params.get('start')
    end_str = request.query_params.get('end')

    if not start_str or not end_str:
        return Response(
            {'detail': 'start and end query params are required (YYYY-MM-DD).'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    start_date = parse_date(start_str)
    end_date = parse_date(end_str)
    if not start_date or not end_date:
        return Response(
            {'detail': 'Invalid date format. Use YYYY-MM-DD.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    from datetime import datetime, time
    from django.utils import timezone as tz
    start_dt = tz.make_aware(datetime.combine(start_date, time.min))
    end_dt = tz.make_aware(datetime.combine(end_date, time.max))

    # Published or scheduled posts with published_at in range
    published_qs = BlogPost.objects.filter(
        published_at__gte=start_dt,
        published_at__lte=end_dt,
    )
    # Drafts (no published_at) created in range
    draft_qs = BlogPost.objects.filter(
        is_published=False,
        published_at__isnull=True,
        created_at__gte=start_dt,
        created_at__lte=end_dt,
    )

    all_ids = set(published_qs.values_list('id', flat=True)) | set(
        draft_qs.values_list('id', flat=True)
    )
    posts = BlogPost.objects.filter(id__in=all_ids)

    data = []
    for p in posts:
        is_scheduled = (
            not p.is_published
            and p.published_at is not None
            and p.published_at > tz.now()
        )
        cal_status = 'published' if p.is_published else ('scheduled' if is_scheduled else 'draft')
        data.append({
            'id': p.id,
            'title_es': p.title_es,
            'title_en': p.title_en,
            'slug': p.slug,
            'category': p.category,
            'is_published': p.is_published,
            'published_at': p.published_at.isoformat() if p.published_at else None,
            'created_at': p.created_at.isoformat(),
            'calendar_status': cal_status,
            'date': (
                p.published_at.strftime('%Y-%m-%d') if p.published_at
                else p.created_at.strftime('%Y-%m-%d')
            ),
        })

    return Response(data, status=status.HTTP_200_OK)
