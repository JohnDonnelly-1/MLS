"""
Metaclasses for automatic MLS behavior injection.
"""

from django.db.models.base import ModelBase as DjangoModelBase
import django.db.models.options as _django_options
from .managers import MLSManager, UnfilteredMLSManager

# Options.contribute_to_class() raises TypeError for any Meta attribute it
# doesn't recognize, checking each name against the module-level
# DEFAULT_NAMES tuple. mls_protected/mls_classification_field must be
# registered there before any model's `class Meta` using them is
# processed - i.e. at import time of this module, since every
# MLS-protected model imports MLSModelBase from here first.
for _mls_meta_option in ('mls_protected', 'mls_classification_field'):
    if _mls_meta_option not in _django_options.DEFAULT_NAMES:
        _django_options.DEFAULT_NAMES = _django_options.DEFAULT_NAMES + (_mls_meta_option,)


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

        # Check if any fields have mls_control=True. cls._meta.fields (forward
        # fields only, no M2M) rather than get_fields() - mls_control is only
        # ever set on a forward FK/O2O field, and get_fields()'s reverse-field
        # scan forces Options._relation_tree to run, which walks every model
        # in the app registry and raises AppRegistryNotReady if called while
        # models are still being imported - exactly what's happening right
        # here, at class-definition time for any model using this metaclass.
        has_mls_field = any(
            hasattr(field, 'mls_control') and field.mls_control
            for field in cls._meta.fields
            if hasattr(field, 'mls_control')
        )

        # If MLS is enabled, ensure the default manager is MLSManager
        if mls_protected or has_mls_field:
            # Only replace if the default manager hasn't been explicitly set
            if not hasattr(cls, 'objects') or cls.objects.__class__.__name__ == 'Manager':
                cls.objects = MLSManager()
                cls.objects.model = cls

            # Always give MLS-protected models the loudly-named DANGER
            # escape hatch, whether or not they inherit from MLSObject.
            if not hasattr(cls, 'DANGER'):
                cls.DANGER = UnfilteredMLSManager()
                cls.DANGER.model = cls

        return cls
