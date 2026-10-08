from decimal import Decimal, InvalidOperation

from django.db.models import Q
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from django.shortcuts import get_object_or_404

from base_feature_app.models import Donation, Payment, Sponsorship
from base_feature_app.serializers.payment_detail import PaymentDetailSerializer
from base_feature_app.serializers.payment_list import PaymentListSerializer
from base_feature_app.views.admin_views import is_superadmin


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_list(request):
    """List payments for platform audit (matches admin UI: role admin or staff)."""
    u = request.user
    if not (is_superadmin(u) or u.is_staff):
        return Response(
            {'error': 'Permission denied'},
            status=status.HTTP_403_FORBIDDEN,
        )
    qs = (
        Payment.objects.filter(archived_at__isnull=True)
        .select_related('donation', 'sponsorship')
        .order_by('-created_at')[:500]
    )
    return Response(PaymentListSerializer(qs, many=True).data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_payment_intent(request):
    """
    Placeholder: Create a payment intent for Wompi.
    In production this would call Wompi's API to create a transaction.
    For now, returns a mock payment intent structure.
    """
    amount = request.data.get('amount')
    payment_type = request.data.get('type')  # 'donation' or 'sponsorship'
    reference_id = request.data.get('reference_id')

    if not amount or not payment_type or not reference_id:
        return Response(
            {'error': 'amount, type, and reference_id are required'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # A truthiness check passes the string "-50000": parse and require a
    # positive amount before any Payment row is created (objects.create()
    # does not run model validators).
    try:
        parsed_amount = Decimal(str(amount))
    except (InvalidOperation, TypeError, ValueError):
        return Response(
            {'error': 'amount must be a valid number'},
            status=status.HTTP_400_BAD_REQUEST,
        )
    if parsed_amount <= 0:
        return Response(
            {'error': 'amount must be greater than zero'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if payment_type == 'donation':
        donation = get_object_or_404(Donation, pk=reference_id, user=request.user)
        payment = Payment.objects.create(
            donation=donation,
            amount=amount,
            provider='wompi',
            provider_reference=f'PLACEHOLDER-donation-{reference_id}',
            status=Payment.Status.PENDING,
            metadata={'type': payment_type, 'reference_id': reference_id},
        )
    elif payment_type == 'sponsorship':
        sponsorship = get_object_or_404(Sponsorship, pk=reference_id, user=request.user)
        payment = Payment.objects.create(
            sponsorship=sponsorship,
            amount=amount,
            provider='wompi',
            provider_reference=f'PLACEHOLDER-sponsorship-{reference_id}',
            status=Payment.Status.PENDING,
            metadata={'type': payment_type, 'reference_id': reference_id},
        )
    else:
        return Response(
            {'error': 'type must be donation or sponsorship'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    return Response({
        'payment_id': payment.pk,
        'provider': 'wompi',
        'status': payment.status,
        'amount': str(payment.amount),
        'redirect_url': None,  # Wompi would provide this
        'message': 'Payment intent created (placeholder — Wompi not integrated yet)',
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def payment_webhook(request):
    """
    Placeholder: Receive Wompi webhook for payment status updates.
    In production this would verify the signature and update payment status.
    """
    return Response({
        'received': True,
        'message': 'Webhook received (placeholder — Wompi not integrated yet)',
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def payment_status(request, pk):
    """Return an unarchived payment visible to its owner or platform auditors."""
    u = request.user
    qs = Payment.objects.filter(archived_at__isnull=True)
    if not (is_superadmin(u) or u.is_staff):
        qs = qs.filter(Q(donation__user=u) | Q(sponsorship__user=u))
    try:
        payment = qs.prefetch_related('status_history').get(pk=pk)
    except Payment.DoesNotExist:
        return Response({'error': 'Payment not found'}, status=status.HTTP_404_NOT_FOUND)
    serializer = PaymentDetailSerializer(payment, context={'request': request})
    return Response(serializer.data)
