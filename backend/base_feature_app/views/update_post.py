from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django.utils import timezone

from base_feature_app.models import UpdatePost
from base_feature_app.serializers.update_post_list import UpdatePostListSerializer
from base_feature_app.utils.shelter_access import user_can_manage_shelter
from base_feature_app.serializers.update_post_detail import UpdatePostDetailSerializer
from base_feature_app.serializers.update_post_create_update import UpdatePostCreateUpdateSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def update_post_list(request):
    queryset = UpdatePost.objects.filter(archived_at__isnull=True).select_related('shelter')

    campaign_id = request.query_params.get('campaign')
    if campaign_id:
        queryset = queryset.filter(campaign_id=campaign_id)
    animal_id = request.query_params.get('animal')
    if animal_id:
        queryset = queryset.filter(animal_id=animal_id)
    shelter_id = request.query_params.get('shelter')
    if shelter_id:
        queryset = queryset.filter(shelter_id=shelter_id)

    serializer = UpdatePostListSerializer(queryset, many=True, context={'request': request})
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([AllowAny])
def update_post_detail(request, pk):
    try:
        post = UpdatePost.objects.get(pk=pk)
    except UpdatePost.DoesNotExist:
        return Response({'error': 'Update post not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = UpdatePostDetailSerializer(post, context={'request': request})
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_post_create(request):
    serializer = UpdatePostCreateUpdateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        post = serializer.save()
        return Response(
            UpdatePostDetailSerializer(post, context={'request': request}).data,
            status=status.HTTP_201_CREATED,
        )
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PATCH'])
@permission_classes([IsAuthenticated])
def update_post_update(request, pk):
    try:
        post = UpdatePost.objects.select_related('shelter').get(pk=pk)
    except UpdatePost.DoesNotExist:
        return Response({'error': 'Update post not found'}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_manage_shelter(request.user, post.shelter):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    serializer = UpdatePostCreateUpdateSerializer(post, data=request.data, partial=True, context={'request': request})
    if serializer.is_valid():
        post = serializer.save()
        return Response(UpdatePostDetailSerializer(post, context={'request': request}).data)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def update_post_delete(request, pk):
    try:
        post = UpdatePost.objects.select_related('shelter').get(pk=pk)
    except UpdatePost.DoesNotExist:
        return Response({'error': 'Update post not found'}, status=status.HTTP_404_NOT_FOUND)

    if not user_can_manage_shelter(request.user, post.shelter):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

    post.archived_at = timezone.now()
    post.save(update_fields=['archived_at', 'updated_at'])
    return Response(status=status.HTTP_204_NO_CONTENT)
