"""
Metaclasses for automatic MLS behavior injection.
"""

from django.db.models.base import ModelBase as DjangoModelBase
from .managers import MLSManager


class MLSModelBase(DjangoModelBase):
    """
    Metaclass that automatically configures MLS protection.

    This metaclass examines the model's Meta options and fields to
    automatically inject MLS behavior when appropriate.
    """

    def __new__(mcs, name, bases, namespace, **kwargs):
        # Create the class first
        cls = super().__new__(mcs, name, bases, namespace, **kwargs)

        # Skip for abstract models and the base models themselves
        if cls._meta.abstract or name in ('MLSSubject', 'MLSObject'):
            return cls

        # Check if MLS protection is enabled via Meta
        mls_protected = getattr(cls._meta, 'mls_protected', False)

        # Check if any fields have mls_control=True
        has_mls_field = any(
            hasattr(field, 'mls_control') and field.mls_control
            for field in cls._meta.get_fields()
            if hasattr(field, 'mls_control')
        )

        # If MLS is enabled, ensure the default manager is MLSManager
        if mls_protected or has_mls_field:
            # Only replace if the default manager hasn't been explicitly set
            if not hasattr(cls, 'objects') or cls.objects.__class__.__name__ == 'Manager':
                cls.objects = MLSManager()
                cls.objects.model = cls

        return cls
