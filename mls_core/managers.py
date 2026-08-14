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

        Requires django-crum's CurrentRequestUserMiddleware to be installed.

        Returns:
            Filtered queryset based on current user's clearances. Fails
            secure (returns none()) if there's no authenticated current
            user or no resolvable subject for them.
        """
        user = get_current_user()
        if not user or not user.is_authenticated:
            return self.none()

        # Try to get the subject associated with this user
        subject = self._get_subject_for_user(user)
        return self.accessible_by(subject)

    def _get_subject_clearances(self, subject):
        """Get the Security object from a subject."""
        # Try configured field names
        for field_name in MLS_SUBJECT_CLEARANCE_FIELDS:
            if hasattr(subject, field_name):
                return getattr(subject, field_name)
        return None

    def _get_mls_control_field(self):
        """Find the field marked with mls_control=True."""
        # cls._meta.fields (forward-only): mls_control only ever appears on a
        # forward FK/O2O field (see metaclasses.py for why get_fields()'s
        # reverse-field scan is avoided here too).
        for field in self.model._meta.fields:
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

        # The standard mls_core subject: SecurityProfile (User.security_profile)
        if hasattr(user, 'security_profile'):
            return user.security_profile

        # Check if user itself is a subject
        if hasattr(user, 'clearances') or hasattr(user, 'accesses'):
            return user

        return None


class MLSManager(models.Manager):
    """
    Manager that automatically enforces MLS access control.

    Secure by default: get_queryset() - and therefore .all()/.get()/
    .filter()/... - is filtered down to whatever the CURRENT REQUEST USER
    (via django-crum) can access. With no resolvable current user (no
    request in flight, no crum middleware wired up, management command,
    shell, etc.) this fails secure and returns nothing.

    For explicit subject filtering, use accessible_by(). For a full bypass,
    use the sibling DANGER manager (auto-injected next to this one on every
    MLS-protected model - see MLSModelBase/MLSObject) - never this manager.
    """

    def get_queryset(self):
        """Filtered by default: only what the current request user can access."""
        return MLSQuerySet(self.model, using=self._db).for_current_user()

    def accessible_by(self, subject):
        """
        Explicit subject filtering - bypasses the current-user default so
        it can be used to check access for a subject other than (or
        without) the current request user, e.g. from a management command.
        """
        return MLSQuerySet(self.model, using=self._db).accessible_by(subject)

    def for_current_user(self):
        """Equivalent to the default queryset; kept for explicit call sites."""
        return MLSQuerySet(self.model, using=self._db).for_current_user()


class UnfilteredMLSManager(models.Manager):
    """
    Manager that BYPASSES MLS ENFORCEMENT ENTIRELY - returns every row
    regardless of classification or current user.

    Always exposed as the loudly-named `DANGER` manager, auto-injected by
    MLSModelBase next to `objects` on every MLS-protected model:

        SecureModel.objects.all()   # safe - filtered to the current user
        SecureModel.DANGER.all()    # DANGEROUS - unfiltered, every row

    Use only for system/admin operations that have established
    authorization some other way - never to serve data to an end user.
    """

    def get_queryset(self):
        return super().get_queryset()
