"""
Authentication views for user sign up, sign in, and password management.
"""
import logging

from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import AnonRateThrottle
from django.contrib.auth.hashers import check_password, make_password
from django.contrib.auth import get_user_model
from django.contrib.auth.models import update_last_login
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.conf import settings

import requests

from base_feature_app.models import PasswordCode
from base_feature_app.utils.auth_utils import (
    generate_auth_tokens, 
    send_password_reset_code,
    send_verification_code
)
def verify_recaptcha(token):
    """Placeholder reCAPTCHA verification. Returns True in DEBUG mode."""
    from django.conf import settings as _settings
    if _settings.DEBUG:
        return True
    secret = getattr(_settings, 'RECAPTCHA_SECRET_KEY', '')
    if not secret:
        return True
    if not token:
        return False
    try:
        resp = requests.post(
            'https://www.google.com/recaptcha/api/siteverify',
            data={'secret': secret, 'response': token},
            timeout=5,
        )
        return resp.json().get('success', False)
    except Exception:
        return False

User = get_user_model()

logger = logging.getLogger(__name__)

CURRENT_TERMS_VERSION = '2026-03-25'


class PasswordResetSendThrottle(AnonRateThrottle):
    scope = 'password_reset'


class PasswordResetVerifyThrottle(AnonRateThrottle):
    scope = 'password_reset_verify'


class SignInThrottle(AnonRateThrottle):
    scope = 'sign_in'


@api_view(['POST'])
@permission_classes([AllowAny])
def sign_up(request):
    """
    User registration endpoint.
    
    Expected data:
    - email: str
    - password: str
    - first_name: str (optional)
    - last_name: str (optional)
    """
    captcha_token = request.data.get('captcha_token', '')
    if not verify_recaptcha(captcha_token):
        return Response(
            {'error': 'reCAPTCHA verification failed.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password')
    first_name = request.data.get('first_name', '').strip()
    last_name = request.data.get('last_name', '').strip()
    
    if not email or not password:
        return Response(
            {'error': 'Email and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if len(password) < 8:
        return Response(
            {'error': 'Password must be at least 8 characters'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if User.objects.filter(email=email).exists():
        return Response(
            {'error': 'User with this email already exists'},
            status=status.HTTP_400_BAD_REQUEST
        )

    terms_accepted = request.data.get('terms_accepted', False)
    if not terms_accepted:
        return Response(
            {'error': 'You must accept the terms and conditions'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create user
    from django.utils import timezone as tz
    user = User.objects.create(
        email=email,
        first_name=first_name,
        last_name=last_name,
        password=make_password(password),
        is_active=True,
        terms_accepted_at=tz.now(),
        terms_version=CURRENT_TERMS_VERSION,
    )
    
    # Generate tokens
    tokens = generate_auth_tokens(user)
    
    return Response(tokens, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([SignInThrottle])
def sign_in(request):
    """
    User sign in endpoint.

    Expected data:
    - email: str
    - password: str
    """
    captcha_token = request.data.get('captcha_token', '')
    if not verify_recaptcha(captcha_token):
        return Response(
            {'error': 'reCAPTCHA verification failed.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    email = request.data.get('email', '').strip().lower()
    password = request.data.get('password')

    if not email or not password:
        return Response(
            {'error': 'Email and password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not check_password(password, user.password):
        return Response(
            {'error': 'Invalid credentials'},
            status=status.HTTP_401_UNAUTHORIZED
        )
    
    if not user.is_active:
        return Response(
            {'error': 'Account is inactive'},
            status=status.HTTP_403_FORBIDDEN
        )

    if user.archived_at:
        return Response(
            {'error': 'Account is no longer available'},
            status=status.HTTP_403_FORBIDDEN
        )

    update_last_login(None, user)

    tokens = generate_auth_tokens(user)

    return Response(tokens, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([SignInThrottle])
def google_login(request):
    """
    Google OAuth login endpoint.
    
    Expected data:
    - email: str
    - given_name: str (optional)
    - family_name: str (optional)
    - picture: str (optional)
    """
    credential = request.data.get('credential') or request.data.get('id_token')

    if not credential:
        return Response({'error': 'Google credential is required'}, status=status.HTTP_400_BAD_REQUEST)

    email = request.data.get('email', '').strip().lower()
    given_name = request.data.get('given_name', '').strip()
    family_name = request.data.get('family_name', '').strip()
    picture_url = request.data.get('picture', '')

    payload = None
    aud_mismatch = False
    try:
        tokeninfo = requests.get(
            'https://oauth2.googleapis.com/tokeninfo',
            params={'id_token': credential},
            timeout=5,
        )
        if tokeninfo.status_code == 200:
            payload = tokeninfo.json()
        else:
            logger.warning('Google tokeninfo rejected credential: status=%s body=%s', tokeninfo.status_code, tokeninfo.text)
    except (requests.RequestException, ValueError) as exc:
        logger.warning('Google token validation failed: %s', exc)

    if payload is not None:
        aud = payload.get('aud', '')
        allowed_auds = [v.strip() for v in (settings.GOOGLE_OAUTH_CLIENT_ID or '').split(',') if v.strip()]
        if allowed_auds and aud not in allowed_auds:
            logger.warning('Google aud mismatch. aud=%s allowed=%s', aud, allowed_auds)
            aud_mismatch = True
            payload = None

    if payload is None and not settings.DEBUG:
        if aud_mismatch:
            return Response({'error': 'Invalid Google client'}, status=status.HTTP_401_UNAUTHORIZED)
        return Response({'error': 'Invalid Google credential'}, status=status.HTTP_401_UNAUTHORIZED)

    if payload is not None:
        token_email = (payload.get('email') or '').strip().lower()
        if token_email:
            email = token_email

        token_given = (payload.get('given_name') or '').strip()
        token_family = (payload.get('family_name') or '').strip()
        token_picture = payload.get('picture') or ''

        if token_given:
            given_name = token_given
        if token_family:
            family_name = token_family
        if token_picture:
            picture_url = token_picture
    
    if not email:
        return Response(
            {'error': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create user
    from django.utils import timezone as tz
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            'first_name': given_name,
            'last_name': family_name,
            'is_active': True,
            'terms_accepted_at': tz.now(),
            'terms_version': CURRENT_TERMS_VERSION,
        }
    )

    if created:
        user.set_unusable_password()
        user.save(update_fields=['password'])
    
    # Update names if user exists but doesn't have them
    if not created:
        if not user.first_name and given_name:
            user.first_name = given_name
        if not user.last_name and family_name:
            user.last_name = family_name
        if user.first_name or user.last_name:
            user.save()

    if user.archived_at or not user.is_active:
        return Response(
            {'error': 'Account is no longer available'},
            status=status.HTTP_403_FORBIDDEN,
        )

    update_last_login(None, user)

    tokens = generate_auth_tokens(user)
    tokens['created'] = created
    tokens['google_validated'] = payload is not None

    return Response(tokens, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetSendThrottle])
def send_passcode(request):
    """
    Send password reset code to user's email.

    Expected data:
    - email: str
    - locale: str (optional, 'es' or 'en'; defaults to 'es')
    """
    email = request.data.get('email', '').strip().lower()
    locale = (request.data.get('locale') or '').strip().lower() or 'es'

    if not email:
        return Response(
            {'error': 'Email is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        # Don't reveal if user exists
        return Response(
            {'message': 'If the email exists, a code has been sent'},
            status=status.HTTP_200_OK
        )

    # Generate and save code
    password_code = PasswordCode.generate_code(user)

    # Send email
    success = send_password_reset_code(user, password_code.code, locale=locale)

    if not success:
        return Response(
            {'error': 'Failed to send email'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return Response(
        {'message': 'Code sent successfully'},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([PasswordResetVerifyThrottle])
def verify_passcode_and_reset_password(request):
    """
    Verify passcode and reset password.

    Expected data:
    - email: str
    - code: str
    - new_password: str
    """
    email = request.data.get('email', '').strip().lower()
    code = request.data.get('code', '').strip()
    new_password = request.data.get('new_password')

    if not email or not code or not new_password:
        return Response(
            {'error': 'Email, code, and new password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        user = User.objects.get(email=email)
    except User.DoesNotExist:
        return Response(
            {'error': 'Invalid email or code'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Find valid code
    try:
        password_code = user.password_codes.filter(
            code=code,
            used=False
        ).first()

        if not password_code or not password_code.is_valid():
            return Response(
                {'error': 'Invalid or expired code'},
                status=status.HTTP_400_BAD_REQUEST
            )
    except Exception:
        return Response(
            {'error': 'Invalid or expired code'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Enforce password strength (min length, common-password, numeric-only, similarity).
    # Validated only after proving the user holds a valid code so we don't leak
    # whether a given email exists for unauthenticated callers.
    try:
        validate_password(new_password, user=user)
    except ValidationError as exc:
        return Response(
            {'error': 'Password does not meet requirements', 'details': list(exc.messages)},
            status=status.HTTP_400_BAD_REQUEST
        )

    user.password = make_password(new_password)
    user.save(update_fields=['password'])

    password_code.used = True
    password_code.save(update_fields=['used'])

    return Response(
        {'message': 'Password reset successfully'},
        status=status.HTTP_200_OK
    )


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_password(request):
    """
    Update user password (requires authentication).
    
    Expected data:
    - current_password: str
    - new_password: str
    """
    current_password = request.data.get('current_password')
    new_password = request.data.get('new_password')
    
    if not current_password or not new_password:
        return Response(
            {'error': 'Current password and new password are required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    user = request.user
    
    if not check_password(current_password, user.password):
        return Response(
            {'error': 'Current password is incorrect'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        validate_password(new_password, user=user)
    except ValidationError as exc:
        return Response(
            {'error': 'Password does not meet requirements', 'details': list(exc.messages)},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user.password = make_password(new_password)
    user.save()
    
    return Response(
        {'message': 'Password updated successfully'},
        status=status.HTTP_200_OK
    )


@api_view(['GET'])
@permission_classes([AllowAny])
def get_captcha_site_key(request):
    """Return the reCAPTCHA site key for frontend widgets."""
    return Response({'site_key': settings.RECAPTCHA_SITE_KEY})


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def validate_token(request):
    """
    Validate JWT token and return user info.
    """
    user = request.user
    return Response({
        'valid': True,
        'user': {
            'id': user.id,
            'email': user.email,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'phone': user.phone,
            'city': user.city,
            'role': user.role,
            'is_staff': user.is_staff,
            'date_joined': user.date_joined.isoformat(),
            'terms_version': user.terms_version or '',
            'current_terms_version': CURRENT_TERMS_VERSION,
        }
    }, status=status.HTTP_200_OK)
