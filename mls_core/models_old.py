"""
Abstract base models for MLS subjects and objects.
"""

from django.db import models
from .managers import MLSManager, UnfilteredMLSManager
from .metaclasses import MLSModelBase
from .settings import MLS_SECURITY_LABELS_FIELD, MLS_SUBJECT_CLEARANCE_FIELDS, MLS_OBJECT_CLASSIFICATION_FIELDS


class MLSSubject(models.Model):
    """
    Abstract base model for MLS subjects (entities that access objects).

    A subject can be:
    - A user
    - A computer system
    - A network
    - Any entity that needs to access protected objects

    The subject must have a field that references their security clearances.

    Example:
        class User(MLSSubject):
            username = models.CharField(max_length=50)
            clearances = models.OneToOneField(Security, on_delete=models.SET_NULL, null=True)
    """

    class Meta:
        abstract = True

    def can_access(self, obj):
        """
        Check if this subject can access the given object.

        Args:
            obj: An MLSObject instance

        Returns:
            bool: True if subject has all required clearances, False otherwise
        """
        # Get subject's clearances
        subject_security = self._get_clearances()
        if not subject_security:
            return False

        # Get object's classification
        obj_security = obj._get_classification()
        if not obj_security:
            return False

        # Get label IDs
        subject_labels_field = getattr(subject_security, MLS_SECURITY_LABELS_FIELD, None)
        obj_labels_field = getattr(obj_security, MLS_SECURITY_LABELS_FIELD, None)

        if subject_labels_field is None or obj_labels_field is None:
            return False

        subject_labels = set(subject_labels_field.values_list('id', flat=True))
        obj_labels = set(obj_labels_field.values_list('id', flat=True))

        # Subject must have ALL of object's labels
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

    An object can be:
    - A file
    - A database row, column, or cell
    - Any entity that needs MLS protection

    The object must have a field that references its security classification.

    Example:
        class Document(MLSObject):
            content = models.TextField()
            classification = MLSForeignKey(Security, mls_control=True, on_delete=models.CASCADE)

    Or with Meta options:
        class SecureFile(MLSObject):
            filename = models.CharField(max_length=255)
            security_label = models.ForeignKey(Security, on_delete=models.CASCADE)

            class Meta:
                mls_protected = True
                mls_classification_field = 'security_label'
    """

    # Default manager - automatically filtered by MLS
    objects = MLSManager()

    # Unfiltered manager - use explicitly for admin/system operations
    all_objects = UnfilteredMLSManager()

    class Meta:
        abstract = True

    def _get_classification(self):
        """Get the Security object containing this object's classification."""
        # Look for field with mls_control=True
        for field in self._meta.get_fields():
            if hasattr(field, 'mls_control') and field.mls_control:
                return getattr(self, field.name, None)

        # Check Meta for classification field
        if hasattr(self._meta, 'mls_classification_field'):
            field_name = self._meta.mls_classification_field
            if hasattr(self, field_name):
                return getattr(self, field_name)

        # Try configured field names
        for field_name in MLS_OBJECT_CLASSIFICATION_FIELDS:
            if hasattr(self, field_name):
                return getattr(self, field_name)

        return None

    def accessible_by(self, subject):
        """
        Check if this object is accessible by the given subject.

        Args:
            subject: An MLSSubject instance

        Returns:
            bool: True if subject can access this object
        """
        if not hasattr(subject, 'can_access'):
            return False
        return subject.can_access(self)
