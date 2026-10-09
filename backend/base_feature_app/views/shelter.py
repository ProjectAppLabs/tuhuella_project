from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import NotAuthenticated
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from base_feature_app.models import Shelter, User
from base_feature_app.serializers.shelter_list import ShelterListSerializer
from base_feature_app.utils.shelter_access import shelters_managed_by_user
from base_feature_app.serializers.shelter_detail import ShelterDetailSerializer
from base_feature_app.serializers.shelter_create_update import ShelterCreateUpdateSerializer

# Relations ShelterListSerializer reads for every row (owner_email, logo_url,
# cover_image_url). Loading them with the shelters keeps a shelter list at a
# constant query count instead of several extra queries per shelter.
SHELTER_LIST_RELATIONS = (
    'owner',
    'logo__primary_attachment',
    'cover_image__primary_attachment',
)


@api_view(['GET'])
@permission_classes([AllowAny])
def shelter_list(request):
    if request.query_params.get('owner') == 'me':
        # Shelter panel: only the shelters this user manages (owner or team
        # member), whatever their verification state, so a pending shelter
        # shows up and the panel never picks up someone else's shelter.
        if not request.user.is_authenticated:
            raise NotAuthenticated()
        shelters = Shelter.objects.filter(
            pk__in=shelters_managed_by_user(request.user).values('pk'),
            archived_at__isnull=True,
        )
    else:
        shelters = Shelter.objects.filter(
            verification_status=Shelter.VerificationStatus.VERIFIED,
            archived_at__isnull=True,
        )
    serializer = ShelterListSerializer(
        shelters.select_related(*SHELTER_LIST_RELATIONS),
        many=True,
        context={'request': request},
    )
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def shelter_detail(request, pk):
    try:
        shelter = Shelter.objects.get(pk=pk, archived_at__isnull=True)
    except Shelter.DoesNotExist:
        return Response({'error': 'Shelter not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = ShelterDetailSerializer(shelter, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def shelter_create(request):
    if request.user.role not in (User.Role.ADMIN, User.Role.WEB_MANAGER):
        return Response(
            {'detail': 'Use POST /api/shelter-applications/ to apply as a shelter.'},
            status=status.HTTP_403_FORBIDDEN,
        )
    serializer = ShelterCreateUpdateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        serializer.save(owner=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def shelter_update(request, pk):
    try:
        shelter = shelters_managed_by_user(request.user).get(pk=pk)
    except Shelter.DoesNotExist:
        return Response({'error': 'Shelter not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = ShelterCreateUpdateSerializer(
        shelter, data=request.data, partial=request.method == 'PATCH', context={'request': request}
    )
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
