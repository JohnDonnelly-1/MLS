"""
Custom field types that support MLS control parameters.
"""

from django.db import models


class MLSFieldMixin:
    """
    Mixin for fields that can be marked as MLS control fields.

    Usage:
        classification = MLSForeignKey(Security, mls_control=True, on_delete=models.CASCADE)
    """

    def __init__(self, *args, mls_control=False, **kwargs):
        """
        Args:
            mls_control: If True, this field is used for MLS access control
        """
        self.mls_control = mls_control
        super().__init__(*args, **kwargs)

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        if self.mls_control:
            kwargs['mls_control'] = self.mls_control
        return name, path, args, kwargs


class MLSForeignKey(MLSFieldMixin, models.ForeignKey):
    """
    ForeignKey that can be marked as an MLS control field.

    Example:
        class Document(models.Model):
            classification = MLSForeignKey(Security, mls_control=True, on_delete=models.CASCADE)
            content = models.TextField()
    """
    pass


class MLSOneToOneField(MLSFieldMixin, models.OneToOneField):
    """
    OneToOneField that can be marked as an MLS control field.

    Example:
        class SecureFile(models.Model):
            security = MLSOneToOneField(Security, mls_control=True, on_delete=models.CASCADE)
            filename = models.CharField(max_length=255)
    """
    pass
