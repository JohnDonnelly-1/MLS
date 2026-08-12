"""
Tests for MLSManager's secure-by-default query filtering.

Regression coverage for a vulnerability where the documented guarantee
("Secure by Default" / "Automatic Filtering (Default)" in README.md) did
not actually hold: Model.objects.all()/.get()/.filter() returned every row
regardless of classification, because nothing wired the default manager up
to accessible_by()/for_current_user(). Explicit accessible_by(subject)
calls worked correctly the whole time - only the *default*, undecorated
manager was silently unfiltered.

MLSManager.get_queryset() now filters to whatever the current request user
(via django-crum) can access, and fails secure (returns/raises nothing)
when there's no current user. The only bypass is the loudly-named DANGER
manager that MLSModelBase auto-injects next to `objects` on every
MLS-protected model.
"""

import pytest
from django.db import models
from crum import impersonate

from mls_core.models import MLSObject, SecurityClearance
from mls_core.fields import MLSForeignKey


class Document(MLSObject):
    """Minimal MLS-protected model for manager tests."""

    title = models.CharField(max_length=200)
    classification = MLSForeignKey(
        SecurityClearance,
        mls_control=True,
        on_delete=models.CASCADE,
    )

    class Meta:
        app_label = 'mls_core'


@pytest.mark.django_db
class TestDefaultManagerFailsSecure:
    """With no resolvable current user, objects.all()/.get() return nothing."""

    def test_all_returns_empty(self, clearance_secret):
        Document.objects.create(title="Secret Report", classification=clearance_secret)
        assert Document.objects.all().count() == 0

    def test_get_raises_does_not_exist(self, clearance_secret):
        Document.objects.create(title="Secret Report", classification=clearance_secret)
        with pytest.raises(Document.DoesNotExist):
            Document.objects.get(title="Secret Report")


@pytest.mark.django_db
class TestDefaultManagerFiltersByCurrentUser:
    """With crum.impersonate(user) active, objects.all()/.get() are filtered
    to exactly what that user's SecurityProfile clearance covers."""

    def test_low_clearance_user_sees_only_low_doc(
        self, user_unclassified, clearance_unclassified, clearance_secret, clearance_top_secret
    ):
        Document.objects.create(title="Cafeteria Menu", classification=clearance_unclassified)
        Document.objects.create(title="Secret Report", classification=clearance_secret)
        Document.objects.create(title="Nuclear Launch Codes", classification=clearance_top_secret)

        with impersonate(user_unclassified):
            titles = set(Document.objects.all().values_list('title', flat=True))
            assert titles == {"Cafeteria Menu"}

    def test_get_on_inaccessible_document_raises_does_not_exist(
        self, user_unclassified, clearance_unclassified, clearance_top_secret
    ):
        Document.objects.create(title="Cafeteria Menu", classification=clearance_unclassified)
        secret_doc = Document.objects.create(
            title="Nuclear Launch Codes", classification=clearance_top_secret
        )

        with impersonate(user_unclassified):
            with pytest.raises(Document.DoesNotExist):
                Document.objects.get(pk=secret_doc.pk)

    def test_higher_clearance_user_sees_more(
        self, user_secret, clearance_unclassified, clearance_secret, clearance_top_secret
    ):
        Document.objects.create(title="Cafeteria Menu", classification=clearance_unclassified)
        secret_doc = Document.objects.create(
            title="Secret Report", classification=clearance_secret
        )
        Document.objects.create(title="Nuclear Launch Codes", classification=clearance_top_secret)

        with impersonate(user_secret):
            titles = set(Document.objects.all().values_list('title', flat=True))
            assert titles == {"Cafeteria Menu", "Secret Report"}
            assert Document.objects.get(pk=secret_doc.pk).title == "Secret Report"

    def test_top_secret_user_sees_everything_with_matching_clearance(
        self, user_top_secret, clearance_unclassified, clearance_secret, clearance_top_secret
    ):
        for title, clearance in [
            ("Cafeteria Menu", clearance_unclassified),
            ("Secret Report", clearance_secret),
            ("Nuclear Launch Codes", clearance_top_secret),
        ]:
            Document.objects.create(title=title, classification=clearance)

        with impersonate(user_top_secret):
            titles = set(Document.objects.all().values_list('title', flat=True))
            assert titles == {"Cafeteria Menu", "Secret Report", "Nuclear Launch Codes"}


@pytest.mark.django_db
class TestDangerManagerBypass:
    """DANGER is the one explicit, loudly-named way to see everything."""

    def test_danger_returns_everything_with_no_current_user(self, clearance_top_secret):
        Document.objects.create(title="Nuclear Launch Codes", classification=clearance_top_secret)

        assert Document.objects.all().count() == 0
        assert Document.DANGER.all().count() == 1

    def test_danger_ignores_current_user_clearance(self, user_unclassified, clearance_top_secret):
        Document.objects.create(title="Nuclear Launch Codes", classification=clearance_top_secret)

        with impersonate(user_unclassified):
            assert Document.objects.all().count() == 0
            assert Document.DANGER.all().count() == 1


@pytest.mark.django_db
class TestExplicitSubjectFilteringUnaffected:
    """accessible_by(subject) keeps working explicitly, independent of any
    current-user context - e.g. for use from a management command."""

    def test_accessible_by_works_with_no_current_user(
        self, user_secret, clearance_secret, clearance_top_secret
    ):
        secret_doc = Document.objects.create(
            title="Secret Report", classification=clearance_secret
        )
        ts_doc = Document.objects.create(
            title="Nuclear Launch Codes", classification=clearance_top_secret
        )

        accessible = Document.objects.accessible_by(user_secret.security_profile)
        assert secret_doc in accessible
        assert ts_doc not in accessible
