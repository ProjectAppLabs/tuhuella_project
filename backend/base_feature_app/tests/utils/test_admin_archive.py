"""Exercise admin archiving through real, permission-checked HTTP requests."""

import json
from datetime import UTC, date, datetime
from types import SimpleNamespace
from urllib.parse import parse_qs, urlparse

import pytest
from django.contrib.admin.models import CHANGE, LogEntry
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db import DatabaseError, connection
from django.test import Client
from django.urls import reverse

from base_feature_app.admin import ShelterAdmin
from base_feature_app.models import (
    AdoptionApplicationEvent,
    Animal,
    ClinicalHistoryEntry,
    PasswordCode,
    PostAdoptionFollowUp,
    Shelter,
)
from base_feature_app.tests.factories import (
    AdoptionApplicationEventFactory,
    AdoptionApplicationFactory,
    AnimalFactory,
    BlogPostFactory,
    CampaignFactory,
    ClinicalHistoryEntryFactory,
    DonationFactory,
    FavoriteFactory,
    PasswordCodeFactory,
    PaymentFactory,
    PostAdoptionFollowUpFactory,
    ShelterApplicationFactory,
    ShelterFactory,
    SponsorshipFactory,
    SubscriptionFactory,
    UpdatePostFactory,
    UserFactory,
    VolunteerApplicationFactory,
)

pytestmark = pytest.mark.django_db

ARCHIVE_FACTORIES = [
    UserFactory,
    ShelterFactory,
    ShelterApplicationFactory,
    AnimalFactory,
    FavoriteFactory,
    AdoptionApplicationFactory,
    AdoptionApplicationEventFactory,
    CampaignFactory,
    DonationFactory,
    SponsorshipFactory,
    PaymentFactory,
    SubscriptionFactory,
    UpdatePostFactory,
    BlogPostFactory,
    VolunteerApplicationFactory,
    PostAdoptionFollowUpFactory,
]


def browser_for(user):
    """Create an authenticated browser with Django's real CSRF checks."""
    browser = Client(enforce_csrf_checks=True)
    browser.force_login(user)
    browser.get(reverse('myadmin:index'))
    return browser


def single_url(obj):
    """Return the registered object's individual archive endpoint."""
    return reverse(
        f'myadmin:{obj._meta.app_label}_{obj._meta.model_name}_delete',
        args=[obj.pk],
    )


def bulk_url(obj):
    """Return the registered object's changelist action endpoint."""
    return reverse(f'myadmin:{obj._meta.app_label}_{obj._meta.model_name}_changelist')


def archive_form(browser, obj, mode):
    """Build an explicit confirmation POST for the selected archive mode."""
    forms = {
        'single': (single_url(obj), {'post': 'yes'}),
        'bulk': (
            bulk_url(obj),
            {'action': 'delete_selected', '_selected_action': [obj.pk], 'post': 'yes'},
        ),
    }
    url, payload = forms[mode]
    payload['csrfmiddlewaretoken'] = browser.cookies['csrftoken'].value
    return url, payload


@pytest.fixture(autouse=True)
def local_test_environment(settings):
    """Keep email local and avoid expensive password hashes unrelated to archiving."""
    settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
    settings.PASSWORD_HASHERS = ['django.contrib.auth.hashers.MD5PasswordHasher']


@pytest.fixture
def admin_browser(admin_user):
    """Provide a staff browser that must submit a valid CSRF token."""
    return browser_for(admin_user)


@pytest.fixture(params=['single', 'bulk'])
def archive_mode(request):
    """Exercise each archive safety rule through both admin entry points."""
    return request.param


@pytest.fixture(params=ARCHIVE_FACTORIES, ids=lambda factory: factory.__name__)
def archive_record(request):
    """Create a real record for each of the sixteen approved archive policies."""
    return request.param()


@pytest.fixture
def clinical_tree(shelter, animal, adoption_application, admin_user):
    """Create the adoption and clinical descendants that hard deletion would lose."""
    follow_up = PostAdoptionFollowUpFactory(
        animal=animal,
        adoption_application=adoption_application,
        adopter=adoption_application.user,
        scheduled_date=date(2026, 10, 10),
    )
    entry = ClinicalHistoryEntryFactory(
        animal=animal, follow_up=follow_up, author=admin_user,
        occurred_at=datetime(2026, 10, 10, tzinfo=UTC),
    )
    return SimpleNamespace(
        shelter=shelter, animal=animal, application=adoption_application,
        follow_up=follow_up, entry=entry,
    )


class TestArchiveSinglePolicies:
    """Verify individual archives for every supported model."""

    def test_archives_record(self, admin_browser, archive_record):
        """Fail if an individual admin archive removes a supported record."""
        url, payload = archive_form(admin_browser, archive_record, 'single')

        response = admin_browser.post(url, payload)

        assert response.status_code == 302
        archive_record.refresh_from_db()
        assert archive_record.archived_at is not None


class TestArchiveBulkPolicies:
    """Verify bulk archives for every supported model."""

    def test_archives_record(self, admin_browser, archive_record):
        """Fail if a bulk admin archive removes a supported record."""
        url, payload = archive_form(admin_browser, archive_record, 'bulk')

        response = admin_browser.post(url, payload)

        assert response.status_code == 302
        archive_record.refresh_from_db()
        assert archive_record.archived_at is not None


class TestArchiveSafety:
    """Verify that archives preserve data and reject unauthorized writes."""

    def test_preserves_clinical_tree(self, admin_browser, clinical_tree, archive_mode):
        """Fail if archiving a shelter destroys its adoption or clinical history."""
        url, payload = archive_form(admin_browser, clinical_tree.shelter, archive_mode)

        response = admin_browser.post(url, payload)

        assert response.status_code == 302
        clinical_tree.shelter.refresh_from_db()
        assert clinical_tree.shelter.archived_at is not None
        assert Animal.objects.get(pk=clinical_tree.animal.pk).shelter_id == clinical_tree.shelter.pk
        clinical_tree.application.refresh_from_db()
        assert clinical_tree.application.animal_id == clinical_tree.animal.pk
        follow_up = PostAdoptionFollowUp.objects.get(pk=clinical_tree.follow_up.pk)
        assert follow_up.adoption_application_id == clinical_tree.application.pk
        entry = ClinicalHistoryEntry.objects.get(pk=clinical_tree.entry.pk)
        assert entry.follow_up_id == clinical_tree.follow_up.pk

    def test_preserves_protected_event(self, admin_browser, clinical_tree, archive_mode):
        """Fail if a protected authorship relation blocks an archive."""
        author = UserFactory()
        event = AdoptionApplicationEventFactory(application=clinical_tree.application, created_by=author)
        url, payload = archive_form(admin_browser, author, archive_mode)

        response = admin_browser.post(url, payload)

        assert response.status_code == 302
        author.refresh_from_db()
        assert author.is_active is False
        assert AdoptionApplicationEvent.objects.get(pk=event.pk).created_by_id == author.pk

    def test_denies_missing_target_permission(self, shelter, archive_mode):
        """Fail if staff without archive permission can alter records."""
        staff = UserFactory(is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename='view_shelter'))
        browser = browser_for(staff)
        url, payload = archive_form(browser, shelter, archive_mode)

        response = browser.post(url, payload)

        assert response.status_code == {'single': 403, 'bulk': 200}[archive_mode]
        shelter.refresh_from_db()
        assert shelter.archived_at is None
        assert LogEntry.objects.count() == 0

    def test_denies_missing_csrf(self, admin_browser, shelter, archive_mode):
        """Fail if a POST without its CSRF token can archive a record."""
        url, payload = archive_form(admin_browser, shelter, archive_mode)
        payload.pop('csrfmiddlewaretoken')

        response = admin_browser.post(url, payload)

        assert response.status_code == 403
        shelter.refresh_from_db()
        assert shelter.archived_at is None
        assert LogEntry.objects.count() == 0

    def test_rejects_unconfirmed_post(self, admin_browser, shelter, archive_mode):
        """Fail if a negative confirmation still archives a record."""
        url, payload = archive_form(admin_browser, shelter, archive_mode)
        payload['post'] = 'no'

        response = admin_browser.post(url, payload)

        assert response.status_code == 403
        shelter.refresh_from_db()
        assert shelter.archived_at is None
        assert LogEntry.objects.count() == 0

    def test_records_archive_as_change(self, admin_browser, shelter, archive_mode):
        """Fail if the audit trail reports physical deletion after archiving."""
        url, payload = archive_form(admin_browser, shelter, archive_mode)

        admin_browser.post(url, payload)

        log = LogEntry.objects.get(
            content_type=ContentType.objects.get_for_model(Shelter), object_id=str(shelter.pk),
        )
        assert log.action_flag == CHANGE
        assert log.change_message == 'Archived.'

    def test_needs_only_target_permission(self, clinical_tree, archive_mode):
        """Fail if archive wrongly requires permission to delete retained children."""
        staff = UserFactory(is_staff=True)
        staff.user_permissions.set(Permission.objects.filter(codename__in=['view_shelter', 'delete_shelter']))
        browser = browser_for(staff)
        url, payload = archive_form(browser, clinical_tree.shelter, archive_mode)

        response = browser.post(url, payload)

        assert response.status_code == 302
        clinical_tree.shelter.refresh_from_db()
        assert clinical_tree.shelter.archived_at is not None
        assert ClinicalHistoryEntry.objects.filter(pk=clinical_tree.entry.pk).count() == 1


class TestArchiveSpecialPolicies:
    """Verify model-specific state transitions while retaining related records."""

    def test_inactivates_user(self, admin_browser, archive_mode):
        """Fail if an archived user remains active."""
        user = UserFactory()
        url, payload = archive_form(admin_browser, user, archive_mode)

        admin_browser.post(url, payload)

        user.refresh_from_db()
        assert user.is_active is False

    def test_sets_animal_archived_status(self, admin_browser, animal, archive_mode):
        """Fail if archiving leaves an animal with its previous status."""
        url, payload = archive_form(admin_browser, animal, archive_mode)

        admin_browser.post(url, payload)

        animal.refresh_from_db()
        assert animal.status == Animal.Status.ARCHIVED

    def test_unpublishes_blog(self, admin_browser, blog_post, archive_mode):
        """Fail if archiving leaves a blog post published."""
        url, payload = archive_form(admin_browser, blog_post, archive_mode)

        admin_browser.post(url, payload)

        blog_post.refresh_from_db()
        assert blog_post.is_published is False

    def test_preserves_follow_up_reference(self, admin_browser, clinical_tree, archive_mode):
        """Fail if archiving a follow-up removes linked clinical entries."""
        url, payload = archive_form(admin_browser, clinical_tree.follow_up, archive_mode)

        admin_browser.post(url, payload)

        clinical_tree.follow_up.refresh_from_db()
        assert clinical_tree.follow_up.archived_at is not None
        assert ClinicalHistoryEntry.objects.get(pk=clinical_tree.entry.pk).follow_up_id == clinical_tree.follow_up.pk


@pytest.fixture(params=['state', 'audit'])
def failing_database(request):
    """Inject a storage failure at the state or audit SQL boundary."""
    prefix = {
        'state': 'UPDATE "base_feature_app_shelter"',
        'audit': 'INSERT INTO "django_admin_log"',
    }[request.param]

    def fail_write(execute, sql, params, many, context):
        if sql.startswith(prefix):
            raise DatabaseError('Archive write unavailable')
        return execute(sql, params, many, context)

    return fail_write


@pytest.mark.django_db(transaction=True)
class TestArchiveTransactions:
    """Verify real database rollback when any archive write fails."""

    def test_rolls_back_failed_archive(self, admin_browser, shelter, archive_mode, failing_database):
        """Fail if a failed state or audit write leaves a partial archive."""
        url, payload = archive_form(admin_browser, shelter, archive_mode)

        with connection.execute_wrapper(failing_database), pytest.raises(DatabaseError, match='Archive write unavailable'):
            admin_browser.post(url, payload)

        shelter.refresh_from_db()
        assert shelter.archived_at is None
        assert LogEntry.objects.count() == 0


@pytest.fixture
def restricted_shelter_admin(monkeypatch, shelter):
    """Add a real object-level permission denial to the registered admin."""
    forbidden_pk = shelter.pk
    original_permission = ShelterAdmin.has_delete_permission

    def object_permission(self, request, obj=None):
        return original_permission(self, request, obj) and (obj is None or obj.pk != forbidden_pk)

    monkeypatch.setattr(ShelterAdmin, 'has_delete_permission', object_permission)


class TestArchiveSelection:
    """Verify that bulk selections respect every target's permissions."""

    def test_denies_forbidden_object(self, admin_browser, shelter, archive_mode, restricted_shelter_admin):
        """Fail if object-level denial is bypassed by a confirmed archive."""
        url, payload = archive_form(admin_browser, shelter, archive_mode)

        response = admin_browser.post(url, payload)

        assert response.status_code == 403
        shelter.refresh_from_db()
        assert shelter.archived_at is None
        assert LogEntry.objects.count() == 0

    def test_denies_mixed_selection(self, admin_browser, shelter, restricted_shelter_admin):
        """Fail if a selection containing a forbidden object is partly archived."""
        allowed = ShelterFactory()
        url, payload = archive_form(admin_browser, shelter, 'bulk')
        payload['_selected_action'].append(allowed.pk)

        response = admin_browser.post(url, payload)

        assert response.status_code == 403
        allowed.refresh_from_db()
        assert allowed.archived_at is None
        shelter.refresh_from_db()
        assert shelter.archived_at is None
        assert LogEntry.objects.count() == 0

    def test_preserves_unselected_object(self, admin_browser, shelter):
        """Fail if bulk archiving changes an unselected record."""
        unselected = ShelterFactory()
        url, payload = archive_form(admin_browser, shelter, 'bulk')

        admin_browser.post(url, payload)

        unselected.refresh_from_db()
        assert unselected.archived_at is None


class TestArchiveNavigation:
    """Verify confirmation, return links and unchanged unrelated delete flows."""

    def test_single_confirmation_preserves_records(self, admin_browser, shelter):
        """Fail if opening the archive confirmation changes the record."""
        response = admin_browser.get(single_url(shelter))

        assert response.status_code == 200
        assert b'Related records and files will be preserved.' in response.content
        shelter.refresh_from_db()
        assert shelter.archived_at is None

    def test_bulk_confirmation_preserves_records(self, admin_browser, shelter):
        """Fail if choosing the bulk action archives before confirmation."""
        url, payload = archive_form(admin_browser, shelter, 'bulk')
        payload.pop('post')

        response = admin_browser.post(url, payload)

        assert response.status_code == 200
        assert b'Related records and files will be preserved.' in response.content
        shelter.refresh_from_db()
        assert shelter.archived_at is None

    def test_change_form_labels_archive_action(self, admin_browser, shelter):
        """Fail if an archivable change form still advertises physical deletion."""
        url = reverse('myadmin:base_feature_app_shelter_change', args=[shelter.pk])

        response = admin_browser.get(url)

        assert response.status_code == 200
        assert b'>Archive</a>' in response.content
        assert b'>Delete</a>' not in response.content

    def test_preserves_changelist_filter(self, admin_browser, shelter):
        """Fail if returning from an archive loses the original list filter."""
        url, payload = archive_form(admin_browser, shelter, 'single')

        response = admin_browser.post(url + '?_changelist_filters=city%3DBogota', payload)

        assert response.status_code == 302
        assert parse_qs(urlparse(response.url).query) == {'city': ['Bogota']}

    def test_single_cancel_returns_to_change_form(self, admin_browser, shelter):
        """Fail if cancelling an individual archive loses the original change form."""
        change_url = reverse('myadmin:base_feature_app_shelter_change', args=[shelter.pk])
        expected_link = change_url + '?_changelist_filters=city%3DBogota'

        response = admin_browser.get(single_url(shelter) + '?_changelist_filters=city%3DBogota')

        assert f'href="{expected_link}" class="button">Cancel</a>'.encode() in response.content

    def test_bulk_cancel_returns_to_filtered_list(self, admin_browser, shelter):
        """Fail if cancelling a bulk archive loses the original filtered list."""
        shelter.city = 'Bogota'
        shelter.save()
        url, payload = archive_form(admin_browser, shelter, 'bulk')
        payload.pop('post')

        response = admin_browser.post(url + '?city=Bogota', payload)

        expected_link = url + '?city=Bogota'
        assert f'href="{expected_link}" class="button">Cancel</a>'.encode() in response.content

    def test_delete_only_returns_to_admin_index(self, shelter):
        """Fail if an archive links staff to a list they cannot view."""
        staff = UserFactory(is_staff=True)
        staff.user_permissions.add(Permission.objects.get(codename='delete_shelter'))
        browser = browser_for(staff)
        url, payload = archive_form(browser, shelter, 'single')

        confirmation = browser.get(url)
        response = browser.post(url, payload)

        assert b'href="/admin/" class="button">Cancel</a>' in confirmation.content
        assert b'href="/admin/base_feature_app/shelter/"' not in confirmation.content
        assert response.url == reverse('myadmin:index')

    def test_ignores_external_redirect(self, admin_browser, shelter):
        """Fail if an archive POST can redirect outside the admin."""
        url, payload = archive_form(admin_browser, shelter, 'single')
        payload['next'] = 'https://attacker.example/'

        response = admin_browser.post(url, payload)

        assert response.url == bulk_url(shelter)

    def test_rejects_unapproved_lookup_field(self, admin_browser, shelter):
        """Fail if an archive POST can bypass Django's lookup-field restrictions."""
        url, payload = archive_form(admin_browser, shelter, 'single')
        payload['_to_field'] = 'name'

        response = admin_browser.post(url, payload)

        assert response.status_code == 400
        shelter.refresh_from_db()
        assert shelter.archived_at is None

    def test_popup_removes_archived_choice(self, admin_browser, shelter):
        """Fail if a related-object popup retains an archived choice."""
        url, payload = archive_form(admin_browser, shelter, 'single')
        payload['_popup'] = '1'

        response = admin_browser.post(url, payload)

        assert response.status_code == 200
        assert json.loads(response.context['popup_response_data']) == {'action': 'delete', 'value': str(shelter.pk)}
        shelter.refresh_from_db()
        assert shelter.archived_at is not None

    def test_escapes_confirmation_name(self, admin_browser, shelter):
        """Fail if a record name injects HTML into an archive confirmation."""
        shelter.name = '<img src=x onerror="bad()">'
        shelter.save()

        response = admin_browser.get(single_url(shelter))

        assert b'&lt;img src=x onerror=&quot;bad()&quot;&gt;' in response.content
        assert b'<img src=x onerror=' not in response.content

    def test_keeps_unrelated_hard_delete(self, admin_browser):
        """Fail if an unrelated admin's physical-delete policy changes."""
        code = PasswordCodeFactory()
        code_pk = code.pk
        payload = {'post': 'yes', 'csrfmiddlewaretoken': admin_browser.cookies['csrftoken'].value}

        response = admin_browser.post(single_url(code), payload)

        assert response.status_code == 302
        assert PasswordCode.objects.filter(pk=code_pk).count() == 0
