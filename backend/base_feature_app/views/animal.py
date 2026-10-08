import math

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django.utils import timezone

from base_feature_app.models import Animal
from base_feature_app.serializers.animal_list import AnimalListSerializer
from base_feature_app.utils.shelter_access import user_can_manage_shelter
from base_feature_app.serializers.animal_detail import AnimalDetailSerializer
from base_feature_app.serializers.animal_create_update import AnimalCreateUpdateSerializer


def _filter_csv(queryset, field, raw_value):
    """Apply a multi-choice filter only when it contains non-empty values."""
    values = [value.strip() for value in (raw_value or '').split(',') if value.strip()]
    if not values:
        return queryset
    return queryset.filter(**{f'{field}__in': values})


@api_view(['GET'])
@permission_classes([AllowAny])
def animal_list(request):
    numeric_params = {}
    for name, default in (('page', 1), ('page_size', 20), ('shelter', None)):
        value = request.query_params.get(name, default)
        if name == 'shelter' and not value:
            continue
        try:
            numeric_params[name] = int(value)
        except (TypeError, ValueError):
            return Response(
                {'error': f'{name} must be an integer'},
                status=status.HTTP_400_BAD_REQUEST,
            )

    queryset = Animal.objects.filter(
        status=Animal.Status.PUBLISHED,
        archived_at__isnull=True,
    ).select_related('shelter')

    for field in ('species', 'size', 'age_range', 'gender', 'energy_level'):
        queryset = _filter_csv(queryset, field, request.query_params.get(field))
    if 'shelter' in numeric_params:
        queryset = queryset.filter(shelter_id=numeric_params['shelter'])
    good_with_kids = request.query_params.get('good_with_kids')
    if good_with_kids:
        queryset = queryset.filter(good_with_kids=good_with_kids.strip())
    good_with_dogs = request.query_params.get('good_with_dogs')
    if good_with_dogs:
        queryset = queryset.filter(good_with_dogs=good_with_dogs.strip())
    good_with_cats = request.query_params.get('good_with_cats')
    if good_with_cats:
        queryset = queryset.filter(good_with_cats=good_with_cats.strip())

    page = max(1, numeric_params['page'])
    page_size = max(1, min(numeric_params['page_size'], 100))

    total = queryset.count()
    total_pages = math.ceil(total / page_size) if total > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size

    serializer = AnimalListSerializer(queryset[start:end], many=True, context={'request': request})
    return Response({
        'count': total,
        'page': page,
        'page_size': page_size,
        'total_pages': total_pages,
        'results': serializer.data,
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def animal_detail(request, pk):
    try:
        animal = (
            Animal.objects
            .select_related('shelter')
            .prefetch_related('disease_screenings')
            .get(pk=pk)
        )
    except Animal.DoesNotExist:
        return Response({'error': 'Animal not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = AnimalDetailSerializer(animal, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def animal_create(request):
    serializer = AnimalCreateUpdateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def animal_update(request, pk):
    try:
        animal = Animal.objects.get(pk=pk)
    except Animal.DoesNotExist:
        return Response({'error': 'Animal not found'}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_manage_shelter(request.user, animal.shelter):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    serializer = AnimalCreateUpdateSerializer(
        animal, data=request.data, partial=request.method == 'PATCH', context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def animal_similar(request, pk):
    from django.core.cache import cache

    cache_key = f'animal_similar_{pk}'
    cached = cache.get(cache_key)
    if cached is not None:
        return Response(cached)

    try:
        animal = Animal.objects.get(pk=pk)
    except Animal.DoesNotExist:
        return Response({'error': 'Animal not found'}, status=status.HTTP_404_NOT_FOUND)

    similar = Animal.objects.filter(
        species=animal.species,
        size=animal.size,
        status=Animal.Status.PUBLISHED,
        archived_at__isnull=True,
    ).exclude(pk=pk).select_related('shelter')

    # Prioritize same shelter by ordering: same shelter first, then by created_at
    from django.db.models import Case, When, Value, IntegerField
    similar = similar.annotate(
        same_shelter=Case(
            When(shelter=animal.shelter, then=Value(0)),
            default=Value(1),
            output_field=IntegerField(),
        )
    ).order_by('same_shelter', '-created_at')[:4]

    serializer = AnimalListSerializer(similar, many=True, context={'request': request})
    data = serializer.data
    cache.set(cache_key, data, timeout=300)  # 5 minutes
    return Response(data)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def animal_delete(request, pk):
    try:
        animal = Animal.objects.get(pk=pk)
    except Animal.DoesNotExist:
        return Response({'error': 'Animal not found'}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_manage_shelter(request.user, animal.shelter):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    animal.archived_at = timezone.now()
    animal.status = Animal.Status.ARCHIVED
    animal.save(update_fields=['archived_at', 'status', 'updated_at'])
    return Response(status=status.HTTP_204_NO_CONTENT)
