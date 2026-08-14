"""
MLS Core Models - Complete security framework

This includes:
- Security Labels (levels and categories)
- Security Clearances (sets of labels)
- Security Profiles (extends Django User)
- MLS Groups (AND logic - user must have ALL labels)
- DAC Groups (OR logic - user needs ANY group)
- Permissions for security management
"""

from django.db import models
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from .managers import MLSManager, UnfilteredMLSManager
from .metaclasses import MLSModelBase
from .settings import MLS_SECURITY_LABELS_FIELD, MLS_SUBJECT_CLEARANCE_FIELDS, MLS_OBJECT_CLASSIFICATION_FIELDS


# ==================== Security Labels ====================

class SecurityLabel(models.Model):
    """
    Security labels are the building blocks of MLS.

    Three types:
    - LEVEL: Hierarchical (UNCLASSIFIED < CONFIDENTIAL < SECRET < TOP SECRET)
    - CATEGORY: Compartments (CRYPTO, INTEL, NATO, etc.)
    - RELEASABILITY: Countries content may be released to (REL TO USA, GBR, ...)

    Releasability is modeled as its own label_type rather than folded into
    CATEGORY (which is how the classification helper used to bucket
    dissemination-style controls by short_code pattern-matching) so that
    "which labels are countries" is an explicit, queryable fact instead of
    a fragile naming convention.
    """

    class LabelType(models.TextChoices):
        LEVEL = "LVL", "Level"
        CATEGORY = "CAT", "Category"
        RELEASABILITY = "REL", "Releasability"

    short_code = models.CharField(
        max_length=10,
        unique=True,
        help_text="Short code (e.g., 'TS', 'S', 'CRYPTO')"
    )
    name = models.CharField(
        max_length=100,
        help_text="Full name of the label"
    )
    label_type = models.CharField(
        max_length=3,
        choices=LabelType.choices,
        default=LabelType.CATEGORY,
        help_text="Level (hierarchical), Category (compartment), or Releasability (country)"
    )
    rank = models.IntegerField(
        default=0,
        help_text="For levels: higher rank = more sensitive. Categories ignore this."
    )
    description = models.TextField(
        blank=True,
        help_text="Description of what this label means"
    )
    color = models.CharField(
        max_length=7,
        default="#808080",
        help_text="Color code for display (hex format)"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['label_type', '-rank', 'name']
        verbose_name = "Security Label"
        verbose_name_plural = "Security Labels"
        permissions = [
            ("manage_labels", "Can manage security labels"),
        ]

    def __str__(self):
        return f"{self.short_code} - {self.name}"

    @property
    def text_color(self):
        """
        '#000000' or '#FFFFFF', whichever gives better contrast against this
        label's badge background color - so badge text stays readable
        regardless of how dark or light `color` is set to.

        Uses the WCAG 2.0 relative luminance definition
        (https://www.w3.org/TR/WCAG20/#relativeluminancedef): each sRGB
        channel is gamma-expanded to linear light, then luminance is the
        weighted sum L = 0.2126*R + 0.7152*G + 0.0722*B. WCAG's contrast
        ratio between two luminances is (lighter+0.05)/(darker+0.05); the
        luminance at which contrast-against-white equals contrast-against-
        black works out to L = 0.05*(sqrt(21) - 1) ~= 0.179 - below that,
        white text has the higher (better) contrast ratio, at or above it
        black does.
        """
        return '#FFFFFF' if _relative_luminance(self.color) < 0.179 else '#000000'


def _relative_luminance(hex_color):
    """WCAG relative luminance (0.0-1.0) of a '#rrggbb' color string."""
    hex_color = (hex_color or '').lstrip('#')
    if len(hex_color) != 6:
        return 1.0  # malformed color - fail toward black text, the safer default on an unknown/light background

    def linearize(channel):
        c = int(hex_color[channel:channel + 2], 16) / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = linearize(0), linearize(2), linearize(4)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


# ==================== Security Clearances ====================

class SecurityClearance(models.Model):
    """
    A set of security labels.

    Used for:
    - Subject clearances (what a user can access)
    - Object classifications (what an object requires)

    MLS Rule: Subject must have ALL of object's labels.
    """

    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional name for this clearance/classification"
    )

    # This field name must match MLS_SECURITY_LABELS_FIELD
    securities = models.ManyToManyField(
        SecurityLabel,
        related_name="clearances",
        blank=True,
        help_text="The set of security labels"
    )

    description = models.TextField(
        blank=True,
        help_text="Description of this clearance level"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Security Clearance"
        verbose_name_plural = "Security Clearances"

    def __str__(self):
        if self.name:
            return self.name
        labels = list(self.securities.values_list('short_code', flat=True))
        return f"[{', '.join(labels)}]" if labels else "(empty)"

    def get_levels(self):
        """Get all level labels (hierarchical)"""
        return self.securities.filter(label_type=SecurityLabel.LabelType.LEVEL)

    def get_categories(self):
        """Get all category labels (compartments)"""
        return self.securities.filter(label_type=SecurityLabel.LabelType.CATEGORY)

    def get_releasability(self):
        """Get all releasability labels (countries)"""
        return self.securities.filter(label_type=SecurityLabel.LabelType.RELEASABILITY)

    def has_label(self, label):
        """Check if this clearance includes a specific label"""
        return self.securities.filter(pk=label.pk).exists()

    def includes_clearance(self, other_clearance):
        """
        Check if this clearance includes all labels from another clearance.
        Used for MLS access control.
        """
        other_label_ids = set(other_clearance.securities.values_list('id', flat=True))
        this_label_ids = set(self.securities.values_list('id', flat=True))
        return other_label_ids.issubset(this_label_ids)


# ==================== MLS Groups (AND logic) ====================

class MLSGroup(models.Model):
    """
    MLS Groups assign security clearances in bulk.

    Logic: User gets ALL labels from ALL their MLS groups (AND logic)

    Example:
    - "Secret Cleared Personnel" group gives [UNCLASS, CONFIDENTIAL, SECRET]
    - "Crypto Compartment" group gives [CRYPTO category]
    - User in both gets: [UNCLASS, CONFIDENTIAL, SECRET, CRYPTO]
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    # The clearance template for this group
    clearance_template = models.ForeignKey(
        SecurityClearance,
        on_delete=models.PROTECT,
        related_name='mls_groups',
        help_text="Security clearance granted to group members"
    )

    # Can contain other MLS groups (nested)
    parent_groups = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='child_groups',
        blank=True,
        help_text="Parent groups (members inherit parent clearances)"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "MLS Group"
        verbose_name_plural = "MLS Groups"
        permissions = [
            ("manage_mls_groups", "Can manage MLS groups"),
        ]

    def __str__(self):
        return self.name

    def get_all_labels(self):
        """
        Get all labels from this group and all parent groups (recursive).
        Returns QuerySet of SecurityLabel objects.
        """
        # Start with this group's labels
        all_labels = set(self.clearance_template.securities.all())

        # Add labels from parent groups (recursive)
        for parent in self.parent_groups.all():
            all_labels.update(parent.get_all_labels())

        return SecurityLabel.objects.filter(pk__in=[label.pk for label in all_labels])


# ==================== DAC Groups (OR logic) ====================

class DACGroup(models.Model):
    """
    Discretionary Access Control Groups.

    Logic: User can access if they have ANY matching DAC group (OR logic)

    Different from MLS:
    - MLS: User must have ALL required labels (restrictive)
    - DAC: User needs ANY matching group (permissive)

    Example:
    - Document restricted to DAC groups: ["Engineering", "Management"]
    - User in "Engineering" group → Access granted (OR logic)
    - User needs either one, not both
    """

    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    # Can contain other DAC groups (nested)
    parent_groups = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='child_dac_groups',
        blank=True,
        help_text="Parent groups (members inherit parent memberships)"
    )

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "DAC Group"
        verbose_name_plural = "DAC Groups"
        permissions = [
            ("manage_dac_groups", "Can manage DAC groups"),
        ]

    def __str__(self):
        return self.name

    def get_all_groups(self):
        """
        Get this group and all parent groups (recursive).
        Returns QuerySet of DACGroup objects.
        """
        all_groups = {self}

        # Add parent groups (recursive)
        for parent in self.parent_groups.all():
            all_groups.update(parent.get_all_groups())

        return DACGroup.objects.filter(pk__in=[g.pk for g in all_groups])


# ==================== Security Profile (extends Django User) ====================

class SecurityProfile(models.Model):
    """
    Security profile for a Django User.

    This extends the built-in User model with MLS/DAC security features.
    One-to-one relationship with User.

    Combines:
    - Direct security clearance
    - MLS Groups (AND logic)
    - DAC Groups (OR logic)
    """

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='security_profile'
    )

    # Direct security clearance (optional - can use groups instead)
    clearances = models.ForeignKey(
        SecurityClearance,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='profiles',
        help_text="Direct security clearance (combined with group clearances)"
    )

    # MLS Groups (AND logic - user gets ALL labels from ALL groups)
    mls_groups = models.ManyToManyField(
        MLSGroup,
        related_name='members',
        blank=True,
        help_text="MLS groups (user gets ALL labels from ALL groups)"
    )

    # DAC Groups (OR logic - user can access if ANY group matches)
    dac_groups = models.ManyToManyField(
        DACGroup,
        related_name='members',
        blank=True,
        help_text="DAC groups (OR logic for discretionary access)"
    )

    # Additional metadata
    clearance_expires = models.DateField(
        null=True,
        blank=True,
        help_text="Date when clearance expires (optional)"
    )

    notes = models.TextField(
        blank=True,
        help_text="Internal notes about this security profile"
    )

    is_active = models.BooleanField(
        default=True,
        help_text="Inactive profiles cannot access anything"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Security Profile"
        verbose_name_plural = "Security Profiles"
        permissions = [
            ("security_manager", "Security Manager - Can edit profiles and assign labels"),
            ("senior_security_manager", "Senior Security Manager - Can CRUD all security objects"),
        ]

    def __str__(self):
        return f"Security Profile: {self.user.username}"

    def get_all_labels(self):
        """
        Get all security labels this user has access to.

        Combines:
        1. Direct clearances
        2. All labels from all MLS groups
        3. All labels from parent groups (recursive)

        Returns: QuerySet of SecurityLabel objects
        """
        all_labels = set()

        # Add direct clearances
        if self.clearances:
            all_labels.update(self.clearances.securities.all())

        # Add labels from all MLS groups
        for group in self.mls_groups.filter(is_active=True):
            all_labels.update(group.get_all_labels())

        return SecurityLabel.objects.filter(pk__in=[label.pk for label in all_labels])

    def get_effective_clearance(self):
        """
        Get a SecurityClearance object representing all labels user has access to.
        Useful for MLS access checks.
        """
        # Create a temporary clearance with all user's labels
        # Note: This doesn't save to database
        clearance = SecurityClearance(name=f"Effective: {self.user.username}")
        return clearance

    def get_all_dac_groups(self):
        """
        Get all DAC groups user belongs to (including parent groups).
        Returns: QuerySet of DACGroup objects
        """
        all_groups = set()

        for group in self.dac_groups.filter(is_active=True):
            all_groups.update(group.get_all_groups())

        return DACGroup.objects.filter(pk__in=[g.pk for g in all_groups])

    def can_access(self, obj):
        """
        Check if this user can access an MLS protected object.

        MLS Rule: User must have ALL of object's required labels.
        """
        if not self.is_active:
            return False

        # Get object's classification
        obj_security = obj._get_classification() if hasattr(obj, '_get_classification') else None
        if not obj_security:
            return False

        # Get user's labels
        user_labels = set(self.get_all_labels())
        obj_labels = set(obj_security.securities.all())

        # User must have ALL of object's labels
        return obj_labels.issubset(user_labels)

    def has_dac_access(self, required_groups):
        """
        Check DAC access.

        Args:
            required_groups: QuerySet or list of DACGroup objects

        Returns:
            True if user has ANY of the required groups (OR logic)
        """
        if not self.is_active:
            return False

        user_groups = set(self.get_all_dac_groups())
        required = set(required_groups)

        # User needs ANY of the required groups (OR logic)
        return bool(user_groups.intersection(required))


# ==================== Abstract Base Classes ====================

class MLSSubject(models.Model):
    """
    Abstract base model for MLS subjects (entities that access objects).

    For most uses, you should use SecurityProfile instead.
    This is kept for backwards compatibility and special cases.
    """

    class Meta:
        abstract = True

    def can_access(self, obj):
        """Check if this subject can access the given object."""
        subject_security = self._get_clearances()
        if not subject_security:
            return False

        obj_security = obj._get_classification() if hasattr(obj, '_get_classification') else None
        if not obj_security:
            return False

        subject_labels_field = getattr(subject_security, MLS_SECURITY_LABELS_FIELD, None)
        obj_labels_field = getattr(obj_security, MLS_SECURITY_LABELS_FIELD, None)

        if subject_labels_field is None or obj_labels_field is None:
            return False

        subject_labels = set(subject_labels_field.values_list('id', flat=True))
        obj_labels = set(obj_labels_field.values_list('id', flat=True))

        return obj_labels.issubset(subject_labels)

    def _get_clearances(self):
        """Get the Security object containing this subject's clearances."""
        for field_name in MLS_SUBJECT_CLEARANCE_FIELDS:
            if hasattr(self, field_name):
                return getattr(self, field_name)
        return None


class MLSObject(models.Model, metaclass=MLSModelBase):
    """
    Abstract base model for MLS objects (entities that need protection).

    Inherit from this to make your model MLS-protected.

    Example:
        class Document(MLSObject):
            title = models.CharField(max_length=200)
            classification = models.ForeignKey(SecurityClearance, mls_control=True, ...)
    """

    objects = MLSManager()  # Secure by default - filtered to the current user's clearance
    DANGER = UnfilteredMLSManager()  # Bypasses MLS entirely - system/admin use only

    class Meta:
        abstract = True

    def _get_classification(self):
        """Get the Security object containing this object's classification."""
        # self._meta.fields (forward-only): mls_control only ever appears on
        # a forward FK/O2O field (see metaclasses.py for why get_fields()'s
        # reverse-field scan is avoided here too).
        for field in self._meta.fields:
            if hasattr(field, 'mls_control') and field.mls_control:
                return getattr(self, field.name, None)

        if hasattr(self._meta, 'mls_classification_field'):
            field_name = self._meta.mls_classification_field
            if hasattr(self, field_name):
                return getattr(self, field_name)

        for field_name in MLS_OBJECT_CLASSIFICATION_FIELDS:
            if hasattr(self, field_name):
                return getattr(self, field_name)

        return None

    def accessible_by(self, subject):
        """Check if this object is accessible by the given subject."""
        if not hasattr(subject, 'can_access'):
            return False
        return subject.can_access(self)
