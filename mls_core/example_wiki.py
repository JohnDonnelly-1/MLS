"""
Example Wiki Model - Demonstrates MLS Classification Integration

This is an example of how to integrate the classification helper
with your own models. You can copy this pattern to your own apps.
"""

from django.db import models
from django.contrib.auth.models import User
from .models import MLSObject, SecurityClearance


class WikiPage(MLSObject):
    """
    Example Wiki Page with MLS classification.

    Demonstrates how to:
    1. Inherit from MLSObject for MLS protection
    2. Use SecurityClearance for classification
    3. Integrate with classification helper
    """

    # Basic fields
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True)
    content = models.TextField()

    # MLS Classification - this field gets mls_control automatically
    classification = models.ForeignKey(
        SecurityClearance,
        on_delete=models.PROTECT,
        related_name='classified_wiki_pages',
        help_text="Security classification for this wiki page"
    )

    # Optional: Parent page for inheritance
    parent_page = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='child_pages',
        help_text="Parent page - can inherit classification"
    )

    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='wiki_pages_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='wiki_pages_updated')

    # Version tracking
    version = models.IntegerField(default=1)

    class Meta:
        ordering = ['title']
        # This tells MLSObject which field contains the classification
        mls_classification_field = 'classification'
        permissions = [
            ("can_classify_wiki", "Can classify wiki pages"),
        ]

    def __str__(self):
        return f"{self.title} [{self.classification.name}]"

    def get_classification_marking(self):
        """
        Returns a formatted classification marking string.
        Example: "SECRET//SCI//NOFORN"
        """
        labels = self.classification.securities.all().order_by('-rank', 'short_code')
        return "//".join([label.short_code for label in labels])

    def can_inherit_from_parent(self):
        """Check if this page can inherit classification from parent."""
        return self.parent_page is not None

    def get_suggested_classification(self):
        """
        Get suggested classification based on context.
        For demo purposes, suggests parent classification if available.
        """
        if self.parent_page:
            return self.parent_page.classification
        return None


# Example of a document attachment with inherited classification
class WikiAttachment(MLSObject):
    """
    File attachment for wiki pages.
    Demonstrates classification inheritance.
    """

    wiki_page = models.ForeignKey(
        WikiPage,
        on_delete=models.CASCADE,
        related_name='attachments'
    )

    filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='wiki_attachments/')

    # Can inherit from parent or have own classification
    classification = models.ForeignKey(
        SecurityClearance,
        on_delete=models.PROTECT,
        related_name='classified_attachments',
        help_text="Security classification - can inherit from wiki page"
    )

    uploaded_by = models.ForeignKey(User, on_delete=models.PROTECT)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        mls_classification_field = 'classification'

    def __str__(self):
        return f"{self.filename} [{self.classification.name}]"

    def save(self, *args, **kwargs):
        """
        Auto-inherit classification from parent page if not specified.
        This is a common pattern for attachments.
        """
        if not self.classification_id and self.wiki_page:
            self.classification = self.wiki_page.classification
        super().save(*args, **kwargs)
