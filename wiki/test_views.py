"""
Wiki app tests.

Covers what actually matters for an MLS-protected wiki: that reads are
filtered by clearance through the real views (not just the ORM), that
attachment downloads are gated the same way, that submitted HTML is
sanitized before it's ever stored, and that history/restore behave.
"""

import pytest
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client

from mls_core.models import SecurityClearance, SecurityLabel, SecurityProfile
from wiki.models import Space, WikiAttachment, WikiPage, WikiRevision

User = get_user_model()


@pytest.fixture
def label_unclass(db):
    return SecurityLabel.objects.create(short_code='U', name='Unclassified', label_type='LVL', rank=1)


@pytest.fixture
def label_secret(db):
    return SecurityLabel.objects.create(short_code='S', name='Secret', label_type='LVL', rank=3)


@pytest.fixture
def clearance_unclass(db, label_unclass):
    c = SecurityClearance.objects.create(name='Unclass')
    c.securities.add(label_unclass)
    return c


@pytest.fixture
def clearance_secret(db, label_unclass, label_secret):
    c = SecurityClearance.objects.create(name='Secret')
    c.securities.add(label_unclass, label_secret)
    return c


def _user_with_clearance(username, clearance):
    user = User.objects.create_user(username=username, password='x')
    SecurityProfile.objects.create(user=user, clearances=clearance, is_active=True)
    return user


@pytest.fixture
def low_user(db, clearance_unclass):
    return _user_with_clearance('low_user', clearance_unclass)


@pytest.fixture
def high_user(db, clearance_secret):
    return _user_with_clearance('high_user', clearance_secret)


@pytest.fixture
def space(db, high_user):
    return Space.objects.create(key='ENG', name='Engineering', created_by=high_user)


@pytest.mark.django_db
class TestPageVisibility:
    def test_creating_a_page_requires_a_classification(self, high_user, space):
        client = Client()
        client.force_login(high_user)
        r = client.post(f'/wiki/{space.key}/new/', {
            'title': 'No classification', 'slug': '', 'content_html': '<p>hi</p>',
        })
        assert r.status_code == 200
        assert not WikiPage.DANGER.filter(title='No classification').exists()

    def test_cannot_classify_a_page_above_own_clearance(self, low_user, space, label_secret):
        """
        low_user only holds the Unclassified label. Even if a label id above
        their own clearance is submitted directly (bypassing whatever the
        rendered picker offered), the server must silently drop it rather
        than honor it - it must never be possible to create content you
        yourself can't see.
        """
        client = Client()
        client.force_login(low_user)
        r = client.post(f'/wiki/{space.key}/new/', {
            'title': 'Smuggled Secret', 'slug': '', 'content_html': '<p>x</p>',
            'label_ids': [str(label_secret.id)],
        })
        assert r.status_code == 200
        assert not WikiPage.DANGER.filter(title='Smuggled Secret').exists()

    def test_user_with_no_clearance_sees_no_selectable_labels(self, space):
        no_profile_user = User.objects.create_user(username='no_profile_user', password='x')
        client = Client()
        client.force_login(no_profile_user)
        r = client.get(f'/wiki/{space.key}/new/')
        assert r.status_code == 200
        assert 'no security clearance assigned' in r.content.decode()

    def test_low_clearance_user_cannot_see_high_page(self, high_user, low_user, space, label_secret):
        client = Client()
        client.force_login(high_user)
        r = client.post(f'/wiki/{space.key}/new/', {
            'title': 'Secret Report', 'slug': '', 'content_html': '<p>classified</p>',
            'label_ids': [str(label_secret.id)],
        })
        assert r.status_code == 302
        page = WikiPage.DANGER.get(title='Secret Report')

        low_client = Client()
        low_client.force_login(low_user)
        assert low_client.get(page.get_absolute_url()).status_code == 404

        # And it must not leak into the space's page tree either.
        tree_resp = low_client.get(f'/wiki/{space.key}/')
        assert 'Secret Report' not in tree_resp.content.decode()

    def test_high_clearance_user_can_see_high_page(self, high_user, space, label_secret):
        client = Client()
        client.force_login(high_user)
        client.post(f'/wiki/{space.key}/new/', {
            'title': 'Secret Report', 'slug': '', 'content_html': '<p>classified</p>',
            'label_ids': [str(label_secret.id)],
        })
        page = WikiPage.DANGER.get(title='Secret Report')
        assert client.get(page.get_absolute_url()).status_code == 200

    def test_anonymous_user_is_redirected_not_shown_content(self, space):
        r = Client().get(f'/wiki/{space.key}/')
        assert r.status_code == 302


@pytest.mark.django_db
class TestContentSanitization:
    def test_script_tags_are_stripped_on_save(self, high_user, space, label_secret):
        client = Client()
        client.force_login(high_user)
        client.post(f'/wiki/{space.key}/new/', {
            'title': 'XSS Test', 'slug': '', 'content_html': '<p>hi</p><script>alert(1)</script>',
            'label_ids': [str(label_secret.id)],
        })
        page = WikiPage.DANGER.get(title='XSS Test')
        assert '<script' not in page.content_html
        assert '<p>hi</p>' in page.content_html

    def test_disallowed_attributes_are_stripped(self, high_user, space, label_secret):
        client = Client()
        client.force_login(high_user)
        client.post(f'/wiki/{space.key}/new/', {
            'title': 'Onclick Test', 'slug': '',
            'content_html': '<p onclick="evil()">text</p>',
            'label_ids': [str(label_secret.id)],
        })
        page = WikiPage.DANGER.get(title='Onclick Test')
        assert 'onclick' not in page.content_html


@pytest.mark.django_db
class TestAttachments:
    def test_attachment_download_is_gated_by_its_own_classification(
        self, high_user, low_user, space, label_secret
    ):
        client = Client()
        client.force_login(high_user)
        client.post(f'/wiki/{space.key}/new/', {
            'title': 'Doc With Attachment', 'slug': '', 'content_html': '<p>x</p>',
            'label_ids': [str(label_secret.id)],
        })
        page = WikiPage.DANGER.get(title='Doc With Attachment')

        upload = SimpleUploadedFile('secret.txt', b'codes: 12345', content_type='text/plain')
        client.post(f'/wiki/{space.key}/{page.slug}/attach/', {
            'file': upload, 'label_ids': [str(label_secret.id)],
        })
        attachment = WikiAttachment.DANGER.get(filename='secret.txt')

        low_client = Client()
        low_client.force_login(low_user)
        assert low_client.get(f'/wiki/attachments/{attachment.pk}/download/').status_code == 404

        r = client.get(f'/wiki/attachments/{attachment.pk}/download/')
        assert r.status_code == 200
        assert b''.join(r.streaming_content) == b'codes: 12345'


@pytest.mark.django_db
class TestRevisionHistory:
    def test_edit_creates_a_new_revision_without_losing_the_old_one(
        self, high_user, space, label_secret
    ):
        client = Client()
        client.force_login(high_user)
        client.post(f'/wiki/{space.key}/new/', {
            'title': 'Versioned Page', 'slug': '', 'content_html': '<p>v1</p>',
            'label_ids': [str(label_secret.id)],
        })
        page = WikiPage.DANGER.get(title='Versioned Page')
        assert page.current_version == 1

        client.post(f'/wiki/{space.key}/{page.slug}/edit/', {
            'title': 'Versioned Page', 'content_html': '<p>v2</p>',
            'label_ids': [str(label_secret.id)],
        })
        page.refresh_from_db()
        assert page.current_version == 2
        assert page.content_html == '<p>v2</p>'
        assert WikiRevision.objects.filter(page=page).count() == 2

    def test_restore_creates_a_new_version_rather_than_overwriting(
        self, high_user, space, label_secret
    ):
        client = Client()
        client.force_login(high_user)
        client.post(f'/wiki/{space.key}/new/', {
            'title': 'Restorable Page', 'slug': '', 'content_html': '<p>original</p>',
            'label_ids': [str(label_secret.id)],
        })
        page = WikiPage.DANGER.get(title='Restorable Page')
        client.post(f'/wiki/{space.key}/{page.slug}/edit/', {
            'title': 'Restorable Page', 'content_html': '<p>changed</p>',
            'label_ids': [str(label_secret.id)],
        })

        client.post(f'/wiki/{space.key}/{page.slug}/restore/1/')
        page.refresh_from_db()
        assert page.content_html == '<p>original</p>'
        assert page.current_version == 3
        assert WikiRevision.objects.filter(page=page).count() == 3
