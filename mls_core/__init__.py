"""
MLS Core - Reusable Multi-Level Security for Django

This package provides automatic MLS enforcement at the ORM level.
"""

__version__ = '1.0.0'

# Lazy imports to avoid loading models before Django apps are ready
def __getattr__(name):
    if name == 'MLSForeignKey':
        from .fields import MLSForeignKey
        return MLSForeignKey
    elif name == 'MLSOneToOneField':
        from .fields import MLSOneToOneField
        return MLSOneToOneField
    elif name == 'MLSManager':
        from .managers import MLSManager
        return MLSManager
    elif name == 'MLSQuerySet':
        from .managers import MLSQuerySet
        return MLSQuerySet
    elif name == 'UnfilteredMLSManager':
        from .managers import UnfilteredMLSManager
        return UnfilteredMLSManager
    elif name == 'MLSSubject':
        from .models import MLSSubject
        return MLSSubject
    elif name == 'MLSObject':
        from .models import MLSObject
        return MLSObject
    elif name == 'MLSMiddleware':
        from .middleware import MLSMiddleware
        return MLSMiddleware
    elif name == 'get_mls_security_model':
        from .settings import get_mls_security_model
        return get_mls_security_model
    elif name == 'get_mls_label_model':
        from .settings import get_mls_label_model
        return get_mls_label_model
    elif name == 'MLS_SECURITY_LABELS_FIELD':
        from .settings import MLS_SECURITY_LABELS_FIELD
        return MLS_SECURITY_LABELS_FIELD
    elif name == 'MLS_SUBJECT_CLEARANCE_FIELDS':
        from .settings import MLS_SUBJECT_CLEARANCE_FIELDS
        return MLS_SUBJECT_CLEARANCE_FIELDS
    elif name == 'MLS_OBJECT_CLASSIFICATION_FIELDS':
        from .settings import MLS_OBJECT_CLASSIFICATION_FIELDS
        return MLS_OBJECT_CLASSIFICATION_FIELDS
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")
