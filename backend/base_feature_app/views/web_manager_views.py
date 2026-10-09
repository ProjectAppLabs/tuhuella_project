"""Views for the web_manager / admin operational workspace."""
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from base_feature_app.models import AdoptionApplication, Shelter
from base_feature_app.serializers.adoption_list import AdoptionListSerializer
from base_feature_app.serializers.shelter_list import ShelterListSerializer
from base_feature_app.utils.shelter_access import is_web_manager_or_admin
from base_feature_app.views.shelter import SHELTER_LIST_RELATIONS


def _paginate(queryset, request):
    try:
        page = max(1, int(request.GET.get('page', 1)))
        page_size = min(100, max(1, int(request.GET.get('page_size', 20))))
    except (TypeError, ValueError):
        page, page_size = 1, 20
    total = queryset.count()
    start = (page - 1) * page_size
    sliced = list(queryset[start:start + page_size])
    return {
        'count': total,
        'page': page,
        'page_size': page_size,
        'total_pages': (total + page_size - 1) // page_size if page_size else 1,
    }, sliced


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_applications_list(request):
    if not is_web_manager_or_admin(request.user):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    qs = (
        AdoptionApplication.objects
        .filter(archived_at__isnull=True)
        .select_related('animal', 'animal__shelter', 'user')
        .order_by('-created_at')
    )
    status_filter = request.GET.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)
    shelter_id = request.GET.get('shelter')
    if shelter_id:
        qs = qs.filter(animal__shelter_id=shelter_id)
    date_from = request.GET.get('date_from')
    if date_from:
        qs = qs.filter(created_at__date__gte=date_from)
    date_to = request.GET.get('date_to')
    if date_to:
        qs = qs.filter(created_at__date__lte=date_to)

    meta, items = _paginate(qs, request)
    serializer = AdoptionListSerializer(items, many=True, context={'request': request})
    return Response({**meta, 'results': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def shelter_applications_list(request, pk):
    if not is_web_manager_or_admin(request.user):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    qs = (
        AdoptionApplication.objects
        .filter(animal__shelter_id=pk, archived_at__isnull=True)
        .select_related('animal', 'animal__shelter', 'user')
        .order_by('-created_at')
    )
    status_filter = request.GET.get('status')
    if status_filter:
        qs = qs.filter(status=status_filter)

    meta, items = _paginate(qs, request)
    serializer = AdoptionListSerializer(items, many=True, context={'request': request})
    return Response({**meta, 'results': serializer.data})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_shelters_list(request):
    if not is_web_manager_or_admin(request.user):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    qs = (
        Shelter.objects
        .filter(archived_at__isnull=True)
        .select_related(*SHELTER_LIST_RELATIONS)
        .order_by('name')
    )
    verification_status = request.GET.get('verification_status')
    if verification_status:
        qs = qs.filter(verification_status=verification_status)
    city = request.GET.get('city')
    if city:
        qs = qs.filter(city__icontains=city)

    meta, items = _paginate(qs, request)
    serializer = ShelterListSerializer(items, many=True, context={'request': request})
    return Response({**meta, 'results': serializer.data})
