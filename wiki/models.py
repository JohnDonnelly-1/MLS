"""
Wiki app models.

Pages and attachments inherit MLSObject, so the same clearance-based access
control enforced everywhere else in this project applies here automatically:
WikiPage.objects / WikiAttachment.objects only ever return what the current
request user is cleared for, and DANGER is the explicit, loudly-named bypass
- exactly the mls_core.example_wiki.py pattern this app is built from.

Spaces are NOT classified - they're just a naming/grouping container (like
Confluence's "space" concept). All real access control lives on the page,
its revisions (gated through the live page), and each attachment
individually - the same place mls_core's own example already put it.
"""

from django.conf import settings
from django.db import models
from django.urls import reverse

from mls_core.fields import MLSForeignKey
from mls_core.models import MLSObject, SecurityClearance


class Space(models.Model):
    """A named area containing a tree of wiki pages, e.g. "Engineering"."""

    key = models.SlugField(
        max_length=20, unique=True,
        help_text="Short code used in URLs, e.g. ENG"
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=8, blank=True,
        help_text="Optional emoji shown next to the space name"
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='wiki_spaces_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('wiki:space_detail', args=[self.key])

    def root_pages(self):
        """Top-level pages accessible to the current user (see managers.py)."""
        return self.pages.filter(parent__isnull=True)


class WikiPage(MLSObject):
    """A single wiki page. `parent` nests pages into a tree within a space."""

    space = models.ForeignKey(Space, on_delete=models.CASCADE, related_name='pages')
    parent = models.ForeignKey(
        'self', on_delete=models.SET_NULL, null=True, blank=True,
        related_name='children',
        help_text="Parent page - leave blank for a top-level page"
    )

    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200)
    content_html = models.TextField(
        blank=True, help_text="Sanitized HTML from the rich text editor"
    )

    classification = MLSForeignKey(
        SecurityClearance, mls_control=True, on_delete=models.PROTECT,
        related_name='wiki_pages',
        help_text="Security classification for this page"
    )

    current_version = models.PositiveIntegerField(default=1)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='wiki_pages_created'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='wiki_pages_updated'
    )
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['title']
        mls_classification_field = 'classification'
        constraints = [
            models.UniqueConstraint(fields=['space', 'slug'], name='unique_page_slug_per_space'),
        ]

    def __str__(self):
        return f"{self.title} [{self.classification}]"

    def get_absolute_url(self):
        return reverse('wiki:page_detail', args=[self.space.key, self.slug])

    def get_classification_marking(self):
        """Formatted marking string, e.g. 'SECRET//CRYPTO'."""
        labels = self.classification.securities.all().order_by('-rank', 'short_code')
        return "//".join(label.short_code for label in labels)

    def get_classification_level(self):
        """Highest-rank LEVEL label - used to pick the banner color."""
        return self.classification.securities.filter(label_type='LVL').order_by('-rank').first()


class WikiRevision(models.Model):
    """
    A saved snapshot of a WikiPage at a point in time.

    Deliberately plain (not MLS-protected) - history access is gated by
    whether the requesting user can access the *current* live page (see
    views.py), so the access-control surface stays in one place rather than
    every historical snapshot needing its own independently-checked label.
    """

    page = models.ForeignKey(WikiPage, on_delete=models.CASCADE, related_name='revisions')
    version = models.PositiveIntegerField()

    title = models.CharField(max_length=200)
    content_html = models.TextField(blank=True)
    classification = models.ForeignKey(
        SecurityClearance, on_delete=models.PROTECT, related_name='wiki_revisions'
    )

    change_note = models.CharField(max_length=255, blank=True)
    edited_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='wiki_revisions'
    )
    edited_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-version']
        constraints = [
            models.UniqueConstraint(fields=['page', 'version'], name='unique_revision_version_per_page'),
        ]

    def __str__(self):
        return f"{self.page.title} v{self.version}"

    def get_classification_marking(self):
        labels = self.classification.securities.all().order_by('-rank', 'short_code')
        return "//".join(label.short_code for label in labels)


class WikiAttachment(MLSObject):
    """A file attached to a wiki page, independently classified."""

    page = models.ForeignKey(WikiPage, on_delete=models.CASCADE, related_name='attachments')

    file = models.FileField(upload_to='wiki_attachments/%Y/%m/')
    filename = models.CharField(max_length=255)
    content_type = models.CharField(max_length=100, blank=True)
    size = models.PositiveIntegerField(default=0, help_text="File size in bytes")

    classification = MLSForeignKey(
        SecurityClearance, mls_control=True, on_delete=models.PROTECT,
        related_name='wiki_attachments',
        help_text="Security classification for this file - independent of the page's"
    )

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT,
        related_name='wiki_attachments_uploaded'
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['filename']
        mls_classification_field = 'classification'

    def __str__(self):
        return f"{self.filename} [{self.classification}]"

    def get_classification_marking(self):
        labels = self.classification.securities.all().order_by('-rank', 'short_code')
        return "//".join(label.short_code for label in labels)

    def human_size(self):
        size = float(self.size)
        for unit in ('B', 'KB', 'MB', 'GB'):
            if size < 1024:
                return f"{size:.0f} {unit}" if unit == 'B' else f"{size:.1f} {unit}"
            size /= 1024
        return f"{size:.1f} TB"
