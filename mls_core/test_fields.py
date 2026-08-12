"""
Comprehensive pytest test suite for MLS custom field types.

This module tests the MLSForeignKey and MLSOneToOneField implementations,
which are critical for the MLS system to properly identify and enforce
security controls.

Test Coverage:
- Unit tests: Field initialization, parameters, and metadata
- Integration tests: Field behavior in Django ORM context
- Edge cases: None values, cascades, validation
"""

import pytest
from django.db import models, transaction
from django.core.exceptions import ValidationError
from django.test import TestCase

from mls_core.fields import MLSFieldMixin, MLSForeignKey, MLSOneToOneField


# ==================== Test Models ====================

class DummyModel(models.Model):
    """Dummy model for testing field relationships."""
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'mls_core'


class ModelWithMLSForeignKey(models.Model):
    """Test model using MLSForeignKey with mls_control=True."""
    name = models.CharField(max_length=100)
    security = MLSForeignKey(
        DummyModel,
        mls_control=True,
        on_delete=models.CASCADE
    )

    class Meta:
        app_label = 'mls_core'


class ModelWithoutMLSControl(models.Model):
    """Test model using MLSForeignKey without mls_control."""
    name = models.CharField(max_length=100)
    security = MLSForeignKey(
        DummyModel,
        mls_control=False,
        on_delete=models.CASCADE
    )

    class Meta:
        app_label = 'mls_core'


class ModelWithDefaultMLSControl(models.Model):
    """Test model using MLSForeignKey with default mls_control."""
    name = models.CharField(max_length=100)
    security = MLSForeignKey(
        DummyModel,
        on_delete=models.CASCADE
    )

    class Meta:
        app_label = 'mls_core'


class ModelWithMLSOneToOne(models.Model):
    """Test model using MLSOneToOneField with mls_control=True."""
    name = models.CharField(max_length=100)
    security = MLSOneToOneField(
        DummyModel,
        mls_control=True,
        on_delete=models.CASCADE
    )

    class Meta:
        app_label = 'mls_core'


class ModelWithNullableMLSField(models.Model):
    """Test model with nullable MLS field."""
    name = models.CharField(max_length=100)
    security = MLSForeignKey(
        DummyModel,
        mls_control=True,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    class Meta:
        app_label = 'mls_core'


class ModelWithMultipleMLSFields(models.Model):
    """Test model with multiple MLS control fields."""
    name = models.CharField(max_length=100)
    primary_classification = MLSForeignKey(
        DummyModel,
        mls_control=True,
        on_delete=models.CASCADE,
        related_name='primary_objects'
    )
    secondary_classification = MLSForeignKey(
        DummyModel,
        mls_control=False,
        on_delete=models.CASCADE,
        related_name='secondary_objects'
    )

    class Meta:
        app_label = 'mls_core'


class ModelWithCascadeDelete(models.Model):
    """Test model with CASCADE delete behavior."""
    name = models.CharField(max_length=100)
    security = MLSForeignKey(
        DummyModel,
        mls_control=True,
        on_delete=models.CASCADE
    )

    class Meta:
        app_label = 'mls_core'


class ModelWithProtect(models.Model):
    """Test model with PROTECT delete behavior."""
    name = models.CharField(max_length=100)
    security = MLSForeignKey(
        DummyModel,
        mls_control=True,
        on_delete=models.PROTECT
    )

    class Meta:
        app_label = 'mls_core'


# ==================== Unit Tests ====================

class TestMLSFieldMixinUnit:
    """Unit tests for MLSFieldMixin base class."""

    def test_mixin_init_with_mls_control_true(self):
        """Test MLSFieldMixin initialization with mls_control=True."""
        field = MLSForeignKey(DummyModel, mls_control=True, on_delete=models.CASCADE)
        assert field.mls_control is True

    def test_mixin_init_with_mls_control_false(self):
        """Test MLSFieldMixin initialization with mls_control=False."""
        field = MLSForeignKey(DummyModel, mls_control=False, on_delete=models.CASCADE)
        assert field.mls_control is False

    def test_mixin_init_default_mls_control(self):
        """Test MLSFieldMixin initialization with default mls_control (False)."""
        field = MLSForeignKey(DummyModel, on_delete=models.CASCADE)
        assert field.mls_control is False

    def test_mixin_stores_mls_control_attribute(self):
        """Test that mls_control is stored as instance attribute."""
        field = MLSForeignKey(DummyModel, mls_control=True, on_delete=models.CASCADE)
        assert hasattr(field, 'mls_control')
        assert isinstance(field.mls_control, bool)


class TestMLSFieldMixinDeconstruct:
    """Unit tests for MLSFieldMixin.deconstruct() method."""

    def test_deconstruct_with_mls_control_true(self):
        """Test deconstruct includes mls_control when True."""
        field = MLSForeignKey(DummyModel, mls_control=True, on_delete=models.CASCADE)
        name, path, args, kwargs = field.deconstruct()

        assert 'mls_control' in kwargs
        assert kwargs['mls_control'] is True

    def test_deconstruct_with_mls_control_false(self):
        """Test deconstruct excludes mls_control when False."""
        field = MLSForeignKey(DummyModel, mls_control=False, on_delete=models.CASCADE)
        name, path, args, kwargs = field.deconstruct()

        # mls_control=False is the default, so it should not be in kwargs
        assert 'mls_control' not in kwargs

    def test_deconstruct_preserves_other_kwargs(self):
        """Test deconstruct preserves other field parameters."""
        field = MLSForeignKey(
            DummyModel,
            mls_control=True,
            on_delete=models.CASCADE,
            related_name='test_relation',
            null=True
        )
        name, path, args, kwargs = field.deconstruct()

        assert kwargs['on_delete'] == models.CASCADE
        assert kwargs['related_name'] == 'test_relation'
        assert kwargs['null'] is True
        assert kwargs['mls_control'] is True

    def test_deconstruct_returns_correct_path(self):
        """Test deconstruct returns correct field path."""
        field = MLSForeignKey(DummyModel, mls_control=True, on_delete=models.CASCADE)
        name, path, args, kwargs = field.deconstruct()

        assert 'MLSForeignKey' in path
        assert 'mls_core.fields' in path


class TestMLSForeignKeyUnit:
    """Unit tests for MLSForeignKey field class."""

    def test_mls_foreign_key_inherits_from_foreign_key(self):
        """Test MLSForeignKey inherits from Django's ForeignKey."""
        field = MLSForeignKey(DummyModel, mls_control=True, on_delete=models.CASCADE)
        assert isinstance(field, models.ForeignKey)

    def test_mls_foreign_key_inherits_from_mixin(self):
        """Test MLSForeignKey inherits from MLSFieldMixin."""
        field = MLSForeignKey(DummyModel, mls_control=True, on_delete=models.CASCADE)
        assert isinstance(field, MLSFieldMixin)

    def test_mls_foreign_key_has_mls_control_attribute(self):
        """Test MLSForeignKey has mls_control attribute."""
        field = MLSForeignKey(DummyModel, mls_control=True, on_delete=models.CASCADE)
        assert hasattr(field, 'mls_control')

    def test_mls_foreign_key_accepts_all_foreign_key_params(self):
        """Test MLSForeignKey accepts standard ForeignKey parameters."""
        field = MLSForeignKey(
            DummyModel,
            mls_control=True,
            on_delete=models.CASCADE,
            related_name='test_related',
            related_query_name='test_query',
            limit_choices_to={'active': True},
            null=True,
            blank=True
        )
        assert field.mls_control is True
        assert field.remote_field.related_name == 'test_related'
        assert field.null is True
        assert field.blank is True


class TestMLSOneToOneFieldUnit:
    """Unit tests for MLSOneToOneField field class."""

    def test_mls_one_to_one_inherits_from_one_to_one_field(self):
        """Test MLSOneToOneField inherits from Django's OneToOneField."""
        field = MLSOneToOneField(DummyModel, mls_control=True, on_delete=models.CASCADE)
        assert isinstance(field, models.OneToOneField)

    def test_mls_one_to_one_inherits_from_mixin(self):
        """Test MLSOneToOneField inherits from MLSFieldMixin."""
        field = MLSOneToOneField(DummyModel, mls_control=True, on_delete=models.CASCADE)
        assert isinstance(field, MLSFieldMixin)

    def test_mls_one_to_one_has_mls_control_attribute(self):
        """Test MLSOneToOneField has mls_control attribute."""
        field = MLSOneToOneField(DummyModel, mls_control=True, on_delete=models.CASCADE)
        assert hasattr(field, 'mls_control')

    def test_mls_one_to_one_accepts_all_one_to_one_params(self):
        """Test MLSOneToOneField accepts standard OneToOneField parameters."""
        field = MLSOneToOneField(
            DummyModel,
            mls_control=True,
            on_delete=models.SET_NULL,
            null=True,
            blank=True,
            related_name='one_to_one_related'
        )
        assert field.mls_control is True
        assert field.null is True
        assert field.blank is True


# ==================== Integration Tests ====================

@pytest.mark.django_db
class TestMLSForeignKeyIntegration:
    """Integration tests for MLSForeignKey in Django ORM context."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data for each test."""
        # Clean up any existing data
        DummyModel.objects.all().delete()
        ModelWithMLSForeignKey.objects.all().delete()
        ModelWithoutMLSControl.objects.all().delete()

        # Create test security objects
        self.security1 = DummyModel.objects.create(name="Security Level 1")
        self.security2 = DummyModel.objects.create(name="Security Level 2")

        yield

        # Cleanup
        DummyModel.objects.all().delete()
        ModelWithMLSForeignKey.objects.all().delete()
        ModelWithoutMLSControl.objects.all().delete()

    def test_model_creation_with_mls_foreign_key(self):
        """Test creating a model instance with MLSForeignKey."""
        obj = ModelWithMLSForeignKey.objects.create(
            name="Test Object",
            security=self.security1
        )
        assert obj.pk is not None
        assert obj.security == self.security1
        assert obj.name == "Test Object"

    def test_field_is_accessible_via_meta(self):
        """Test that MLS field can be accessed through model's _meta."""
        model = ModelWithMLSForeignKey
        security_field = model._meta.get_field('security')

        assert isinstance(security_field, MLSForeignKey)
        assert hasattr(security_field, 'mls_control')
        assert security_field.mls_control is True

    def test_mls_control_true_field_is_identifiable(self):
        """Test that fields with mls_control=True can be identified."""
        model = ModelWithMLSForeignKey
        mls_fields = [
            field for field in model._meta.get_fields()
            if hasattr(field, 'mls_control') and field.mls_control
        ]

        assert len(mls_fields) == 1
        assert mls_fields[0].name == 'security'

    def test_mls_control_false_field_is_not_identified(self):
        """Test that fields with mls_control=False are not identified as MLS fields."""
        model = ModelWithoutMLSControl
        mls_fields = [
            field for field in model._meta.get_fields()
            if hasattr(field, 'mls_control') and field.mls_control
        ]

        assert len(mls_fields) == 0

    def test_field_relationship_works(self):
        """Test that ForeignKey relationship functionality works."""
        obj = ModelWithMLSForeignKey.objects.create(
            name="Test Object",
            security=self.security1
        )

        # Test forward relationship
        assert obj.security.name == "Security Level 1"

        # Test reverse relationship
        related_objects = self.security1.modelwithmlsforeignkey_set.all()
        assert obj in related_objects

    def test_querying_by_related_field(self):
        """Test querying objects by their MLS foreign key."""
        obj1 = ModelWithMLSForeignKey.objects.create(
            name="Object 1",
            security=self.security1
        )
        obj2 = ModelWithMLSForeignKey.objects.create(
            name="Object 2",
            security=self.security2
        )

        results = ModelWithMLSForeignKey.objects.filter(security=self.security1)
        assert obj1 in results
        assert obj2 not in results

    def test_update_mls_foreign_key(self):
        """Test updating the MLS foreign key field."""
        obj = ModelWithMLSForeignKey.objects.create(
            name="Test Object",
            security=self.security1
        )

        obj.security = self.security2
        obj.save()

        obj.refresh_from_db()
        assert obj.security == self.security2


@pytest.mark.django_db
class TestMLSOneToOneFieldIntegration:
    """Integration tests for MLSOneToOneField in Django ORM context."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data for each test."""
        DummyModel.objects.all().delete()
        ModelWithMLSOneToOne.objects.all().delete()

        self.security = DummyModel.objects.create(name="Security Level")

        yield

        DummyModel.objects.all().delete()
        ModelWithMLSOneToOne.objects.all().delete()

    def test_model_creation_with_mls_one_to_one(self):
        """Test creating a model instance with MLSOneToOneField."""
        obj = ModelWithMLSOneToOne.objects.create(
            name="Test Object",
            security=self.security
        )
        assert obj.pk is not None
        assert obj.security == self.security

    def test_one_to_one_uniqueness_constraint(self):
        """Test that OneToOne relationship enforces uniqueness."""
        ModelWithMLSOneToOne.objects.create(
            name="Object 1",
            security=self.security
        )

        # Attempting to create another object with same security should fail.
        # The failing create() is wrapped in its own atomic() block so the
        # IntegrityError gets rolled back to a savepoint instead of poisoning
        # the surrounding test transaction - without this, the fixture's
        # post-yield cleanup queries would raise TransactionManagementError.
        with pytest.raises(Exception):  # Will raise IntegrityError
            with transaction.atomic():
                ModelWithMLSOneToOne.objects.create(
                    name="Object 2",
                    security=self.security
                )

    def test_reverse_one_to_one_relationship(self):
        """Test reverse OneToOne relationship."""
        obj = ModelWithMLSOneToOne.objects.create(
            name="Test Object",
            security=self.security
        )

        # Access reverse relationship
        assert self.security.modelwithmlsonetoone == obj


@pytest.mark.django_db
class TestMLSFieldEdgeCases:
    """Test edge cases and boundary conditions for MLS fields."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data."""
        DummyModel.objects.all().delete()
        ModelWithNullableMLSField.objects.all().delete()
        ModelWithCascadeDelete.objects.all().delete()

        self.security = DummyModel.objects.create(name="Security")

        yield

        DummyModel.objects.all().delete()
        ModelWithNullableMLSField.objects.all().delete()
        ModelWithCascadeDelete.objects.all().delete()

    def test_nullable_mls_field_with_none(self):
        """Test creating object with None for nullable MLS field."""
        obj = ModelWithNullableMLSField.objects.create(
            name="Object with no security",
            security=None
        )
        assert obj.pk is not None
        assert obj.security is None

    def test_nullable_mls_field_with_value(self):
        """Test nullable MLS field can also hold a value."""
        obj = ModelWithNullableMLSField.objects.create(
            name="Object with security",
            security=self.security
        )
        assert obj.security == self.security

    def test_cascade_delete_behavior(self):
        """Test CASCADE delete behavior on MLS field."""
        obj = ModelWithCascadeDelete.objects.create(
            name="Test Object",
            security=self.security
        )
        obj_id = obj.id

        # Delete the related security object
        self.security.delete()

        # The object should be deleted due to CASCADE
        assert not ModelWithCascadeDelete.objects.filter(id=obj_id).exists()

    def test_set_null_behavior(self):
        """Test SET_NULL behavior on nullable MLS field."""
        obj = ModelWithNullableMLSField.objects.create(
            name="Test Object",
            security=self.security
        )

        # Delete the related security object
        self.security.delete()

        # The object should still exist but with None security
        obj.refresh_from_db()
        assert obj.security is None

    def test_protect_behavior(self):
        """Test PROTECT behavior prevents deletion of referenced object."""
        from django.db.models import ProtectedError

        # Create model with PROTECT
        security = DummyModel.objects.create(name="Protected Security")
        ModelWithProtect.objects.create(
            name="Protected Object",
            security=security
        )

        # Attempting to delete should raise ProtectedError
        with pytest.raises(ProtectedError):
            security.delete()

        # Cleanup
        ModelWithProtect.objects.all().delete()
        security.delete()


@pytest.mark.django_db
class TestMLSFieldModelIntrospection:
    """Test model introspection and field discovery."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data."""
        DummyModel.objects.all().delete()

        self.security1 = DummyModel.objects.create(name="Security 1")
        self.security2 = DummyModel.objects.create(name="Security 2")

        yield

        DummyModel.objects.all().delete()

    def test_find_mls_control_fields_in_model(self):
        """Test finding all fields with mls_control=True in a model."""
        model = ModelWithMultipleMLSFields

        mls_fields = [
            field for field in model._meta.get_fields()
            if hasattr(field, 'mls_control') and field.mls_control
        ]

        assert len(mls_fields) == 1
        assert mls_fields[0].name == 'primary_classification'

    def test_find_all_mls_fields_regardless_of_control(self):
        """Test finding all MLSForeignKey/MLSOneToOneField fields."""
        model = ModelWithMultipleMLSFields

        mls_fields = [
            field for field in model._meta.get_fields()
            if isinstance(field, (MLSForeignKey, MLSOneToOneField))
        ]

        assert len(mls_fields) == 2
        field_names = [f.name for f in mls_fields]
        assert 'primary_classification' in field_names
        assert 'secondary_classification' in field_names

    def test_distinguish_mls_control_true_from_false(self):
        """Test distinguishing between mls_control=True and False fields."""
        model = ModelWithMultipleMLSFields

        mls_controlled = [
            field for field in model._meta.get_fields()
            if hasattr(field, 'mls_control') and field.mls_control is True
        ]
        mls_not_controlled = [
            field for field in model._meta.get_fields()
            if hasattr(field, 'mls_control') and field.mls_control is False
        ]

        assert len(mls_controlled) == 1
        assert mls_controlled[0].name == 'primary_classification'

        assert len(mls_not_controlled) == 1
        assert mls_not_controlled[0].name == 'secondary_classification'

    def test_model_without_mls_fields(self):
        """Test models that don't have any MLS fields."""
        model = DummyModel

        mls_fields = [
            field for field in model._meta.get_fields()
            if isinstance(field, (MLSForeignKey, MLSOneToOneField))
        ]

        assert len(mls_fields) == 0


@pytest.mark.django_db
class TestMLSFieldMigrations:
    """Test that MLS fields work correctly with Django migrations."""

    def test_field_deconstruct_for_migrations(self):
        """Test that field deconstruction works for migrations."""
        field = MLSForeignKey(
            DummyModel,
            mls_control=True,
            on_delete=models.CASCADE
        )

        name, path, args, kwargs = field.deconstruct()

        # Reconstruct the field from deconstruct output
        # This simulates what Django migrations do
        assert path is not None
        assert 'mls_control' in kwargs
        assert kwargs['mls_control'] is True

    def test_field_serialization_round_trip(self):
        """Test that field can be serialized and deserialized."""
        original_field = MLSForeignKey(
            DummyModel,
            mls_control=True,
            on_delete=models.CASCADE,
            related_name='test_related'
        )

        # Deconstruct (serialize)
        name, path, args, kwargs = original_field.deconstruct()

        # The kwargs should contain all necessary information
        assert kwargs['mls_control'] is True
        assert kwargs['on_delete'] == models.CASCADE
        assert kwargs['related_name'] == 'test_related'


@pytest.mark.django_db
class TestMLSFieldQuerySetOperations:
    """Test MLS fields work correctly with QuerySet operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data."""
        DummyModel.objects.all().delete()
        ModelWithMLSForeignKey.objects.all().delete()

        self.security1 = DummyModel.objects.create(name="Security 1")
        self.security2 = DummyModel.objects.create(name="Security 2")
        self.security3 = DummyModel.objects.create(name="Security 3")

        self.obj1 = ModelWithMLSForeignKey.objects.create(
            name="Object 1",
            security=self.security1
        )
        self.obj2 = ModelWithMLSForeignKey.objects.create(
            name="Object 2",
            security=self.security2
        )
        self.obj3 = ModelWithMLSForeignKey.objects.create(
            name="Object 3",
            security=self.security1
        )

        yield

        DummyModel.objects.all().delete()
        ModelWithMLSForeignKey.objects.all().delete()

    def test_filter_by_mls_field(self):
        """Test filtering QuerySet by MLS field."""
        results = ModelWithMLSForeignKey.objects.filter(security=self.security1)
        assert results.count() == 2
        assert self.obj1 in results
        assert self.obj3 in results

    def test_exclude_by_mls_field(self):
        """Test excluding from QuerySet by MLS field."""
        results = ModelWithMLSForeignKey.objects.exclude(security=self.security1)
        assert results.count() == 1
        assert self.obj2 in results

    def test_select_related_with_mls_field(self):
        """Test select_related with MLS field."""
        # This should not cause additional queries
        results = ModelWithMLSForeignKey.objects.select_related('security').all()

        assert results.count() == 3
        # Access related object without additional query
        for obj in results:
            assert obj.security is not None

    def test_prefetch_related_with_reverse_mls_relation(self):
        """Test prefetch_related with reverse MLS relationship."""
        securities = DummyModel.objects.prefetch_related(
            'modelwithmlsforeignkey_set'
        ).all()

        for sec in securities:
            # Access reverse relation without additional queries
            related_count = sec.modelwithmlsforeignkey_set.count()
            if sec == self.security1:
                assert related_count == 2
            elif sec == self.security2:
                assert related_count == 1
            else:
                assert related_count == 0

    def test_annotate_with_mls_field(self):
        """Test annotate with MLS field counts."""
        from django.db.models import Count

        securities = DummyModel.objects.annotate(
            obj_count=Count('modelwithmlsforeignkey')
        )

        for sec in securities:
            if sec == self.security1:
                assert sec.obj_count == 2
            elif sec == self.security2:
                assert sec.obj_count == 1

    def test_values_includes_mls_field(self):
        """Test values() includes MLS field."""
        results = ModelWithMLSForeignKey.objects.values('name', 'security')

        assert len(results) == 3
        for result in results:
            assert 'name' in result
            assert 'security' in result
            assert result['security'] in [self.security1.id, self.security2.id]

    def test_values_list_with_mls_field(self):
        """Test values_list with MLS field."""
        results = ModelWithMLSForeignKey.objects.values_list('security', flat=True)

        security_ids = list(results)
        assert self.security1.id in security_ids
        assert self.security2.id in security_ids
        assert security_ids.count(self.security1.id) == 2


@pytest.mark.django_db
class TestMLSFieldBulkOperations:
    """Test MLS fields work correctly with bulk operations."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data."""
        DummyModel.objects.all().delete()
        ModelWithMLSForeignKey.objects.all().delete()

        self.security1 = DummyModel.objects.create(name="Security 1")
        self.security2 = DummyModel.objects.create(name="Security 2")

        yield

        DummyModel.objects.all().delete()
        ModelWithMLSForeignKey.objects.all().delete()

    def test_bulk_create_with_mls_field(self):
        """Test bulk_create with MLS fields."""
        objects = [
            ModelWithMLSForeignKey(name=f"Object {i}", security=self.security1)
            for i in range(10)
        ]

        created = ModelWithMLSForeignKey.objects.bulk_create(objects)
        assert len(created) == 10

        # Verify all objects have the correct security
        for obj in created:
            obj.refresh_from_db()
            assert obj.security == self.security1

    def test_bulk_update_mls_field(self):
        """Test bulk_update with MLS fields."""
        # Create objects
        objects = [
            ModelWithMLSForeignKey.objects.create(
                name=f"Object {i}",
                security=self.security1
            )
            for i in range(5)
        ]

        # Update all to security2
        for obj in objects:
            obj.security = self.security2

        ModelWithMLSForeignKey.objects.bulk_update(objects, ['security'])

        # Verify updates
        for obj in objects:
            obj.refresh_from_db()
            assert obj.security == self.security2

    def test_update_queryset_with_mls_field(self):
        """Test QuerySet.update() with MLS field."""
        # Create objects with security1
        for i in range(5):
            ModelWithMLSForeignKey.objects.create(
                name=f"Object {i}",
                security=self.security1
            )

        # Update all to security2
        updated = ModelWithMLSForeignKey.objects.filter(
            security=self.security1
        ).update(security=self.security2)

        assert updated == 5

        # Verify no objects have security1
        assert ModelWithMLSForeignKey.objects.filter(
            security=self.security1
        ).count() == 0

        # Verify all have security2
        assert ModelWithMLSForeignKey.objects.filter(
            security=self.security2
        ).count() == 5


# ==================== Performance Tests ====================

@pytest.mark.django_db
class TestMLSFieldPerformance:
    """Performance tests for MLS fields."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test data."""
        DummyModel.objects.all().delete()
        ModelWithMLSForeignKey.objects.all().delete()

        # Create security levels
        self.securities = [
            DummyModel.objects.create(name=f"Security {i}")
            for i in range(10)
        ]

        yield

        DummyModel.objects.all().delete()
        ModelWithMLSForeignKey.objects.all().delete()

    def test_large_dataset_with_mls_fields(self):
        """Test MLS fields work efficiently with large datasets."""
        import time

        # Create 1000 objects with MLS fields
        objects = [
            ModelWithMLSForeignKey(
                name=f"Object {i}",
                security=self.securities[i % len(self.securities)]
            )
            for i in range(1000)
        ]

        start = time.time()
        ModelWithMLSForeignKey.objects.bulk_create(objects)
        create_time = time.time() - start

        # Should complete reasonably quickly (< 5 seconds)
        assert create_time < 5.0

        # Verify count
        assert ModelWithMLSForeignKey.objects.count() == 1000

    def test_filtering_large_dataset_by_mls_field(self):
        """Test filtering large dataset by MLS field is performant."""
        import time

        # Create 1000 objects
        objects = [
            ModelWithMLSForeignKey(
                name=f"Object {i}",
                security=self.securities[i % len(self.securities)]
            )
            for i in range(1000)
        ]
        ModelWithMLSForeignKey.objects.bulk_create(objects)

        # Time filtering operation
        start = time.time()
        results = ModelWithMLSForeignKey.objects.filter(
            security=self.securities[0]
        )
        count = results.count()
        filter_time = time.time() - start

        # Should complete quickly (< 1 second)
        assert filter_time < 1.0
        assert count == 100  # Every 10th object

    def test_select_related_performance_with_mls_field(self):
        """Test select_related improves performance with MLS fields."""
        import time

        # Create 100 objects
        objects = [
            ModelWithMLSForeignKey(
                name=f"Object {i}",
                security=self.securities[i % len(self.securities)]
            )
            for i in range(100)
        ]
        ModelWithMLSForeignKey.objects.bulk_create(objects)

        # Time without select_related
        start = time.time()
        objects_no_select = list(ModelWithMLSForeignKey.objects.all())
        for obj in objects_no_select:
            _ = obj.security.name  # Access related object
        time_no_select = time.time() - start

        # Time with select_related
        start = time.time()
        objects_with_select = list(
            ModelWithMLSForeignKey.objects.select_related('security').all()
        )
        for obj in objects_with_select:
            _ = obj.security.name  # Access related object
        time_with_select = time.time() - start

        # select_related should be significantly faster
        # (at least 2x faster, typically much more)
        assert time_with_select < time_no_select


# ==================== Django TestCase Compatibility ====================

class TestMLSFieldsDjangoTestCase(TestCase):
    """
    Django TestCase-based tests for compatibility with existing test suite.

    These tests use Django's TestCase instead of pytest to ensure
    compatibility with the existing test framework.
    """

    def setUp(self):
        """Set up test data."""
        self.security = DummyModel.objects.create(name="Test Security")

    def test_mls_foreign_key_with_django_testcase(self):
        """Test MLSForeignKey works with Django TestCase."""
        obj = ModelWithMLSForeignKey.objects.create(
            name="Test Object",
            security=self.security
        )

        self.assertIsNotNone(obj.pk)
        self.assertEqual(obj.security, self.security)

        # Test field has mls_control
        field = obj._meta.get_field('security')
        self.assertTrue(hasattr(field, 'mls_control'))
        self.assertTrue(field.mls_control)

    def test_mls_one_to_one_with_django_testcase(self):
        """Test MLSOneToOneField works with Django TestCase."""
        obj = ModelWithMLSOneToOne.objects.create(
            name="Test Object",
            security=self.security
        )

        self.assertIsNotNone(obj.pk)
        self.assertEqual(obj.security, self.security)

        # Test field has mls_control
        field = obj._meta.get_field('security')
        self.assertTrue(hasattr(field, 'mls_control'))
        self.assertTrue(field.mls_control)

    def test_field_introspection_with_django_testcase(self):
        """Test field introspection works with Django TestCase."""
        model = ModelWithMLSForeignKey

        # Find MLS-controlled fields
        mls_fields = [
            field for field in model._meta.get_fields()
            if hasattr(field, 'mls_control') and field.mls_control
        ]

        self.assertEqual(len(mls_fields), 1)
        self.assertEqual(mls_fields[0].name, 'security')
        self.assertIsInstance(mls_fields[0], MLSForeignKey)
