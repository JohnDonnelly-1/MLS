"""
Custom managers and querysets for MLS enforcement.
"""

from django.db import models
from django.db.models import Q
from crum import get_current_user
from .settings import MLS_SECURITY_LABELS_FIELD, MLS_SUBJECT_CLEARANCE_FIELDS, MLS_OBJECT_CLASSIFICATION_FIELDS


class MLSQuerySet(models.QuerySet):
    """
    QuerySet that automatically filters objects based on MLS rules.

    The fundamental rule: A subject can access an object ONLY if the subject
    possesses ALL of the security labels that the object requires.
    """

    def accessible_by(self, subject):
        """
        Filter queryset to only objects accessible by the given subject.

        Args:
            subject: A model instance with a 'clearances' or 'accesses' field
                    pointing to a Security object

        Returns:
            Filtered queryset
        """
        if subject is None:
            # No subject = no access (fail-secure)
            return self.none()

        # Get the subject's clearances
        subject_clearances = self._get_subject_clearances(subject)
        if not subject_clearances:
            return self.none()

        # Get subject's label IDs
        labels_field = getattr(subject_clearances, MLS_SECURITY_LABELS_FIELD, None)
        if labels_field is None:
            return self.none()
        subject_label_ids = set(labels_field.values_list('id', flat=True))

        # Find the MLS control field on this model
        mls_field = self._get_mls_control_field()
        if not mls_field:
            # If no MLS field is defined, check Meta options
            if not getattr(self.model._meta, 'mls_protected', False):
                # Not MLS protected - return all
                return self
            else:
                # MLS protected but no field defined - fail secure
                return self.none()

        # Get all objects and filter by checking if subject has all required labels
        accessible_ids = []
        for obj in self.all():
            obj_security = getattr(obj, mls_field.name, None)
            if obj_security is None:
                # No classification = no access (fail-secure)
                continue

            # Get object's required label IDs
            labels_field = getattr(obj_security, MLS_SECURITY_LABELS_FIELD, None)
            if labels_field is None:
                continue
            obj_label_ids = set(labels_field.values_list('id', flat=True))

            # Subject must have ALL of the object's labels
            if obj_label_ids.issubset(subject_label_ids):
                accessible_ids.append(obj.pk)

        return self.filter(pk__in=accessible_ids)

    def for_current_user(self):
        """
        Filter queryset based on the current user from request context.

        Requires MLSMiddleware to be installed.

        Returns:
            Filtered queryset based on current user's clearances
        """
        user = get_current_user()
        if user is None or not user.is_authenticated:
            return self.none()

        # Try to get the subject associated with this user
        subject = self._get_subject_for_user(user)
        return self.accessible_by(subject)

    def unfiltered(self):
        """
        Get unfiltered queryset - use with caution!

        This bypasses MLS enforcement and should only be used for
        system/admin operations.

        Returns:
            Unfiltered queryset
        """
        return self.all()

    def _get_subject_clearances(self, subject):
        """Get the Security object from a subject."""
        # Try configured field names
        for field_name in MLS_SUBJECT_CLEARANCE_FIELDS:
            if hasattr(subject, field_name):
                return getattr(subject, field_name)
        return None

    def _get_mls_control_field(self):
        """Find the field marked with mls_control=True."""
        for field in self.model._meta.get_fields():
            if hasattr(field, 'mls_control') and field.mls_control:
                return field

        # Check if Meta specifies a classification field
        if hasattr(self.model._meta, 'mls_classification_field'):
            field_name = self.model._meta.mls_classification_field
            try:
                return self.model._meta.get_field(field_name)
            except Exception:
                pass

        return None

    def _get_subject_for_user(self, user):
        """
        Get the MLS subject for a Django user.

        Override this in subclasses if you have a different user->subject mapping.
        """
        # Try to find FakeUser or similar subject model
        if hasattr(user, 'fakeuser'):
            return user.fakeuser

        # Check if user itself is a subject
        if hasattr(user, 'clearances') or hasattr(user, 'accesses'):
            return user

        return None


class MLSManager(models.Manager):
    """
    Manager that automatically enforces MLS access control.

    This replaces the default 'objects' manager to make MLS enforcement
    the default behavior (secure-by-default).
    """

    def get_queryset(self):
        """Return MLSQuerySet instead of regular QuerySet."""
        return MLSQuerySet(self.model, using=self._db)

    def accessible_by(self, subject):
        """Proxy to queryset method."""
        return self.get_queryset().accessible_by(subject)

    def for_current_user(self):
        """Proxy to queryset method."""
        return self.get_queryset().for_current_user()

    def unfiltered(self):
        """
        Get unfiltered queryset - bypasses MLS enforcement.

        WARNING: Use only for system/admin operations!
        """
        return self.get_queryset().unfiltered()


class UnfilteredMLSManager(models.Manager):
    """
    Manager that provides unfiltered access.

    Use this as a secondary manager when you need explicit unfiltered access:

        class SecureModel(MLSObject):
            objects = MLSManager()  # Default filtered
            all_objects = UnfilteredMLSManager()  # Explicit unfiltered
    """

    def get_queryset(self):
        return super().get_queryset()
