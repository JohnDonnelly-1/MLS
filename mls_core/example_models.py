"""
Example security models for MLS Core.

These models provide a reference implementation that new projects can use.
You can copy these to your own app and customize as needed.
"""

from django.db import models


class SecurityLabel(models.Model):
    """
    Example security label model.

    Labels can be levels (hierarchical) or categories (compartments).

    Examples:
        - Levels: UNCLASSIFIED, CONFIDENTIAL, SECRET, TOP SECRET
        - Categories: CRYPTO, INTEL, NATO, NUCLEAR
    """

    class LabelType(models.TextChoices):
        LEVEL = "LVL", "Level"
        CATEGORY = "CAT", "Category"

    short_code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Short code for the label (e.g., 'TS', 'S', 'CRYPTO')"
    )
    name = models.CharField(
        max_length=100,
        help_text="Full name of the label"
    )
    label_type = models.CharField(
        max_length=3,
        choices=LabelType.choices,
        default=LabelType.CATEGORY,
        help_text="Whether this is a hierarchical level or a category compartment"
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this label means"
    )

    class Meta:
        ordering = ['label_type', 'name']
        verbose_name = "Security Label"
        verbose_name_plural = "Security Labels"

    def __str__(self):
        return f"{self.short_code} - {self.name}"


class SecurityClearance(models.Model):
    """
    Example security clearance/classification model.

    This represents a set of security labels. It can be used for:
    - Subject clearances (what a user/system can access)
    - Object classifications (what an object requires)

    The field name 'securities' matches the default MLS_SECURITY_LABELS_FIELD.
    """

    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional name for this security clearance/classification"
    )

    # This field name must match MLS_SECURITY_LABELS_FIELD setting
    securities = models.ManyToManyField(
        SecurityLabel,
        related_name="clearances",
        help_text="The set of security labels in this clearance/classification"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Security Clearance"
        verbose_name_plural = "Security Clearances"

    def __str__(self):
        if self.name:
            return self.name
        # Show labels if no name
        labels = list(self.securities.values_list('short_code', flat=True))
        return f"Security [{', '.join(labels)}]" if labels else "Security (no labels)"

    def get_levels(self):
        """Get all level labels."""
        return self.securities.filter(label_type=SecurityLabel.LabelType.LEVEL)

    def get_categories(self):
        """Get all category labels."""
        return self.securities.filter(label_type=SecurityLabel.LabelType.CATEGORY)


# Example usage in settings.py:
#
# MLS_SECURITY_MODEL = 'your_app.SecurityClearance'
# MLS_LABEL_MODEL = 'your_app.SecurityLabel'
# MLS_SECURITY_LABELS_FIELD = 'securities'  # This is the default
