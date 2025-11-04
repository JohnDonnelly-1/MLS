"""
MLS Core settings and configuration.
"""

from django.conf import settings
from django.core.exceptions import ImproperlyConfigured


def get_mls_security_model():
    """
    Get the security model to use for MLS.

    Similar to Django's AUTH_USER_MODEL, this allows projects to specify
    which model represents security clearances/classifications.

    The model must have a ManyToManyField named 'securities' that points
    to a label model (or implement a compatible interface).

    Configure in settings.py:
        MLS_SECURITY_MODEL = 'myapp.SecurityClearance'

    Returns:
        Model class
    """
    try:
        from django.apps import apps
        model_string = getattr(settings, 'MLS_SECURITY_MODEL', 'abac.Security')
        return apps.get_model(model_string)
    except (ValueError, LookupError) as e:
        # Check if we're in testing mode
        import sys
        if 'test' in sys.argv or 'pytest' in sys.modules:
            # In test mode without abac app - return None
            # Tests will use their own test models
            return None
        raise ImproperlyConfigured(
            f"MLS_SECURITY_MODEL refers to model '{model_string}' "
            f"that has not been installed or is invalid. "
            f"Make sure to configure MLS_SECURITY_MODEL in your settings.py "
            f"or ensure the 'abac' app is in INSTALLED_APPS."
        )


def get_mls_label_model():
    """
    Get the label model to use for MLS.

    Configure in settings.py:
        MLS_LABEL_MODEL = 'myapp.SecurityLabel'

    Returns:
        Model class
    """
    try:
        from django.apps import apps
        model_string = getattr(settings, 'MLS_LABEL_MODEL', 'abac.Label')
        return apps.get_model(model_string)
    except (ValueError, LookupError):
        # Check if we're in testing mode
        import sys
        if 'test' in sys.argv or 'pytest' in sys.modules:
            # In test mode without abac app - return None
            # Tests will use their own test models
            return None
        raise ImproperlyConfigured(
            f"MLS_LABEL_MODEL refers to model '{model_string}' "
            f"that has not been installed or is invalid. "
            f"Make sure to configure MLS_LABEL_MODEL in your settings.py "
            f"or ensure the 'abac' app is in INSTALLED_APPS."
        )


# Default field names to look for on security models
MLS_SECURITY_LABELS_FIELD = getattr(settings, 'MLS_SECURITY_LABELS_FIELD', 'securities')

# Default field names to look for on subject models
MLS_SUBJECT_CLEARANCE_FIELDS = getattr(
    settings,
    'MLS_SUBJECT_CLEARANCE_FIELDS',
    ['clearances', 'accesses', 'security']
)

# Default field names to look for on object models
MLS_OBJECT_CLASSIFICATION_FIELDS = getattr(
    settings,
    'MLS_OBJECT_CLASSIFICATION_FIELDS',
    ['classification', 'security', 'security_label']
)
