"""Private, deterministic data for the editorial-image browser acceptance flow.

This helper is intentionally importable from a Django shell after migrations.  It
does not load dotenv files or alter Django settings: callers must explicitly
prepare the private SQLite database, local mail backend, and in-memory Huey.
"""

from __future__ import annotations

from decimal import Decimal
from io import BytesIO
import os
from pathlib import Path
from typing import Final

from django.conf import settings
from django.core.files.base import ContentFile
from django.db import connection, transaction
from django.utils import timezone
from django_attachments.models import Attachment, Library
from huey import MemoryHuey
from PIL import Image

from base_feature_app.models import Campaign, Shelter, UpdatePost, User


_NAMESPACE: Final = "editorial-r8"
_SHELTER_NAME: Final = "Editorial R8 Shelter"
_CAMPAIGN_TITLE_ES: Final = "Editorial R8 campaña completada"
_CAMPAIGN_TITLE_EN: Final = "Editorial R8 completed campaign"
_UPDATE_TITLE_ES: Final = "Actualización editorial R8 ilustrada"
_UPDATE_TITLE_EN: Final = "Illustrated editorial R8 update"


def _environment_value(name: str) -> str:
    value = os.environ.get(name, "").strip()
    if not value:
        raise RuntimeError(f"{name} must be set for the editorial E2E seed")
    return value


def _path_is_within(path: Path, parent: Path) -> bool:
    try:
        path.resolve().relative_to(parent.resolve())
    except ValueError:
        return False
    return True


def _require_private_runtime() -> None:
    """Reject every database or side-effecting runtime except the explicit test one."""
    if os.environ.get("E2E_EDITORIAL_SEED") != "1":
        raise RuntimeError("Set E2E_EDITORIAL_SEED=1 before creating editorial E2E data")
    if os.environ.get("DJANGO_ENV") != "development":
        raise RuntimeError("Editorial E2E data may only be created with DJANGO_ENV=development")
    if connection.vendor != "sqlite":
        raise RuntimeError("Editorial E2E data may only be created in SQLite")
    if settings.EMAIL_BACKEND != "django.core.mail.backends.locmem.EmailBackend":
        raise RuntimeError("Editorial E2E data requires Django's local-memory email backend")
    if not isinstance(settings.HUEY, MemoryHuey):
        raise RuntimeError("Editorial E2E data requires an in-memory Huey instance")

    # CI workspaces are ephemeral.  A developer must provide an explicit private
    # parent directory for both the SQLite file and media files instead.
    if os.environ.get("CI", "").lower() == "true":
        return

    allowed_dir = Path(_environment_value("E2E_EDITORIAL_DB_DIR"))
    database_name = str(connection.settings_dict["NAME"])
    if database_name == ":memory:" or not _path_is_within(Path(database_name), allowed_dir):
        raise RuntimeError("Editorial E2E SQLite database is outside E2E_EDITORIAL_DB_DIR")
    if not _path_is_within(Path(settings.MEDIA_ROOT), allowed_dir):
        raise RuntimeError("Editorial E2E media directory is outside E2E_EDITORIAL_DB_DIR")


def _png_file() -> ContentFile:
    image = Image.new("RGB", (2, 2), color=(28, 117, 137))
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return ContentFile(buffer.getvalue(), name=f"{_NAMESPACE}-update.png")


def _ensure_update_image(post: UpdatePost) -> tuple[Library, str | None]:
    """Return a real primary image library and a newly-written path, if any."""
    if post.image_id:
        try:
            primary = post.image.primary_attachment
        except Library.DoesNotExist:
            primary = None
        if primary and primary.file and primary.file.storage.exists(primary.file.name):
            return post.image, None
        library = post.image
    else:
        library = Library.objects.create(title=f"{_NAMESPACE} update illustration")
        post.image = library
        post.save(update_fields=["image", "updated_at"])

    attachment = Attachment(library=library, rank=0, file=_png_file())
    attachment.save()
    library.primary_attachment = attachment
    library.save(update_fields=["primary_attachment", "updated"])
    return library, attachment.file.name


def seed_editorial_e2e() -> dict[str, str]:
    """Create the real completed-campaign update consumed by editorial E2E tests."""
    _require_private_runtime()
    email = _environment_value("E2E_EDITORIAL_ADMIN_EMAIL")
    password = _environment_value("E2E_EDITORIAL_ADMIN_PASSWORD")
    new_file_name: str | None = None

    try:
        with transaction.atomic():
            admin, _ = User.objects.get_or_create(
                email=email,
                defaults={
                    "first_name": "Editorial",
                    "last_name": "R8",
                    "role": User.Role.ADMIN,
                    "is_staff": True,
                    "is_active": True,
                },
            )
            admin.first_name = "Editorial"
            admin.last_name = "R8"
            admin.role = User.Role.ADMIN
            admin.is_staff = True
            admin.is_active = True
            admin.archived_at = None
            admin.set_password(password)
            admin.save(
                update_fields=[
                    "first_name", "last_name", "role", "is_staff", "is_active",
                    "archived_at", "password",
                ]
            )

            shelter, _ = Shelter.objects.get_or_create(
                owner=admin,
                name=_SHELTER_NAME,
                defaults={
                    "legal_name": "Editorial R8 Foundation",
                    "description_es": "Refugio privado para la aceptación editorial.",
                    "description_en": "Private shelter for editorial acceptance.",
                    "city": "Bogotá",
                    "address": "Calle editorial 8",
                    "phone": "3000000008",
                    "email": "editorial-r8@example.invalid",
                    "verification_status": Shelter.VerificationStatus.VERIFIED,
                },
            )
            shelter.archived_at = None
            shelter.verification_status = Shelter.VerificationStatus.VERIFIED
            shelter.save(update_fields=["archived_at", "verification_status", "updated_at"])

            campaign, _ = Campaign.objects.get_or_create(
                shelter=shelter,
                title_es=_CAMPAIGN_TITLE_ES,
                defaults={
                    "title_en": _CAMPAIGN_TITLE_EN,
                    "description_es": "Campaña completada para validar una actualización ilustrada.",
                    "description_en": "Completed campaign for an illustrated update check.",
                    "goal_amount": "1000.00",
                    "raised_amount": "1000.00",
                    "status": Campaign.Status.COMPLETED,
                    "approval_status": Campaign.ApprovalStatus.APPROVED,
                    "submitted_at": timezone.now(),
                    "reviewed_by": admin,
                    "reviewed_at": timezone.now(),
                },
            )
            now = timezone.now()
            campaign.title_en = _CAMPAIGN_TITLE_EN
            campaign.description_es = "Campaña completada para validar una actualización ilustrada."
            campaign.description_en = "Completed campaign for an illustrated update check."
            campaign.goal_amount = Decimal("1000.00")
            campaign.raised_amount = Decimal("1000.00")
            campaign.status = Campaign.Status.COMPLETED
            campaign.approval_status = Campaign.ApprovalStatus.APPROVED
            campaign.submitted_at = now
            campaign.reviewed_by = admin
            campaign.reviewed_at = now
            campaign.archived_at = None
            campaign.save()

            post, _ = UpdatePost.objects.get_or_create(
                campaign=campaign,
                title_es=_UPDATE_TITLE_ES,
                defaults={
                    "shelter": shelter,
                    "title_en": _UPDATE_TITLE_EN,
                    "content_es": "Una actualización pública con una ilustración real.",
                    "content_en": "A public update with a real illustration.",
                },
            )
            post.shelter = shelter
            post.title_en = _UPDATE_TITLE_EN
            post.content_es = "Una actualización pública con una ilustración real."
            post.content_en = "A public update with a real illustration."
            post.archived_at = None
            post.save()

            image_library, new_file_name = _ensure_update_image(post)
            primary = image_library.primary_attachment
            if primary is None:
                raise RuntimeError("Editorial E2E update image did not get a primary attachment")

            return {
                "E2E_EDITORIAL_ADMIN_EMAIL": admin.email,
                "E2E_EDITORIAL_ADMIN_PASSWORD": password,
                "E2E_EDITORIAL_CAMPAIGN_ID": str(campaign.pk),
                "E2E_EDITORIAL_UPDATE_ID": str(post.pk),
                "E2E_EDITORIAL_IMAGE_URL": primary.file.url,
            }
    except Exception:
        if new_file_name:
            Attachment._meta.get_field("file").storage.delete(new_file_name)
        raise
