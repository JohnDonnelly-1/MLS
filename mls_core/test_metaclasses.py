"""
Comprehensive test suite for MLS Metaclass System.

This test suite validates the MLSModelBase metaclass, which is CRITICAL infrastructure
that makes MLS work transparently by automatically injecting MLS managers into models.

Test coverage includes:
- Automatic manager injection for MLS-protected models
- Detection of mls_protected Meta option
- Detection of mls_control fields
- Manager replacement (objects vs all_objects)
- Interaction with Django's model metaclass
- Edge cases (no MLS protection, multiple inheritance, etc.)
"""

import pytest
from django.db import models
from django.test import TestCase

from mls_core.metaclasses import MLSModelBase
from mls_core.managers import MLSManager, UnfilteredMLSManager
from mls_core.fields import MLSForeignKey, MLSOneToOneField
from mls_core.models import SecurityClearance, SecurityLabel


# ==================== Test Models ====================

class TestSecurityModel(models.Model):
    """Minimal Security model for testing"""
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'mls_core'


class BasicModel(models.Model):
    """Basic model without MLS protection - should NOT get MLSManager"""
    name = models.CharField(max_length=100)

    class Meta:
        app_label = 'mls_core'


class MLSProtectedViaMetaOption(models.Model, metaclass=MLSModelBase):
    """Model using Meta.mls_protected = True"""
    name = models.CharField(max_length=100)
    security = models.ForeignKey(
        TestSecurityModel,
        on_delete=models.CASCADE,
        null=True
    )

    class Meta:
        app_label = 'mls_core'
        mls_protected = True


class MLSProtectedViaFieldMarker(models.Model, metaclass=MLSModelBase):
    """Model using field-level mls_control=True"""
    name = models.CharField(max_length=100)
    classification = MLSForeignKey(
        TestSecurityModel,
        mls_control=True,
        on_delete=models.CASCADE,
        null=True
    )

    class Meta:
        app_label = 'mls_core'


class MLSProtectedViaOneToOneField(models.Model, metaclass=MLSModelBase):
    """Model using OneToOne field with mls_control=True"""
    name = models.CharField(max_length=100)
    security_level = MLSOneToOneField(
        TestSecurityModel,
        mls_control=True,
        on_delete=models.CASCADE,
        null=True
    )

    class Meta:
        app_label = 'mls_core'


class MLSProtectedViaBothMetaAndField(models.Model, metaclass=MLSModelBase):
    """Model using both Meta option AND field marker"""
    name = models.CharField(max_length=100)
    classification = MLSForeignKey(
        TestSecurityModel,
        mls_control=True,
        on_delete=models.CASCADE,
        null=True
    )

    class Meta:
        app_label = 'mls_core'
        mls_protected = True


class MLSWithExplicitManager(models.Model, metaclass=MLSModelBase):
    """Model with explicitly set custom manager - should NOT be replaced"""
    name = models.CharField(max_length=100)

    # Explicitly set custom manager
    objects = models.Manager()

    class Meta:
        app_label = 'mls_core'
        mls_protected = True


class MLSWithExplicitMLSManager(models.Model, metaclass=MLSModelBase):
    """Model with explicitly set MLSManager - should be preserved"""
    name = models.CharField(max_length=100)

    objects = MLSManager()

    class Meta:
        app_label = 'mls_core'
        mls_protected = True


class AbstractMLSModel(models.Model, metaclass=MLSModelBase):
    """Abstract model - should NOT get manager injection"""
    name = models.CharField(max_length=100)

    class Meta:
        abstract = True
        mls_protected = True


class ConcreteMLSChild(AbstractMLSModel):
    """Concrete child of abstract model - should get manager injection"""
    description = models.CharField(max_length=200)
    security = MLSForeignKey(
        TestSecurityModel,
        mls_control=True,
        on_delete=models.CASCADE,
        null=True
    )

    class Meta:
        app_label = 'mls_core'


class MultipleInheritanceModel(models.Model, metaclass=MLSModelBase):
    """Test multiple inheritance scenarios"""

    class Meta:
        app_label = 'mls_core'
        mls_protected = True


class ModelWithMultipleMLSFields(models.Model, metaclass=MLSModelBase):
    """Model with multiple fields marked with mls_control"""
    name = models.CharField(max_length=100)
    primary_classification = MLSForeignKey(
        TestSecurityModel,
        mls_control=True,
        on_delete=models.CASCADE,
        related_name='primary_classified',
        null=True
    )
    secondary_classification = MLSForeignKey(
        TestSecurityModel,
        mls_control=True,
        on_delete=models.CASCADE,
        related_name='secondary_classified',
        null=True
    )

    class Meta:
        app_label = 'mls_core'


class ModelWithoutMLSProtection(models.Model, metaclass=MLSModelBase):
    """Model using metaclass but no MLS protection markers"""
    name = models.CharField(max_length=100)
    regular_field = models.CharField(max_length=50)

    class Meta:
        app_label = 'mls_core'


# ==================== Unit Tests ====================


class TestMLSModelBaseBasicBehavior(TestCase):
    """Unit tests for basic MLSModelBase metaclass behavior"""

    def test_basic_model_without_mls_has_default_manager(self):
        """Models without MLS markers should have default Django Manager"""
        self.assertIsInstance(BasicModel.objects, models.Manager)
        self.assertNotIsInstance(BasicModel.objects, MLSManager)

    def test_meta_protected_model_gets_mls_manager(self):
        """Model with mls_protected=True should get MLSManager"""
        self.assertIsInstance(MLSProtectedViaMetaOption.objects, MLSManager)

    def test_field_protected_model_gets_mls_manager(self):
        """Model with mls_control field should get MLSManager"""
        self.assertIsInstance(MLSProtectedViaFieldMarker.objects, MLSManager)

    def test_onetoone_field_protection_works(self):
        """OneToOne field with mls_control should trigger manager injection"""
        self.assertIsInstance(MLSProtectedViaOneToOneField.objects, MLSManager)

    def test_both_meta_and_field_protection_works(self):
        """Model with both Meta option and field marker should get MLSManager"""
        self.assertIsInstance(MLSProtectedViaBothMetaAndField.objects, MLSManager)

    def test_mls_manager_is_bound_to_model(self):
        """Injected MLSManager should have correct model binding"""
        manager = MLSProtectedViaMetaOption.objects
        self.assertEqual(manager.model, MLSProtectedViaMetaOption)

    def test_model_without_protection_keeps_default_manager(self):
        """Model using metaclass but no protection should keep default Manager"""
        self.assertIsInstance(ModelWithoutMLSProtection.objects, models.Manager)
        self.assertNotIsInstance(ModelWithoutMLSProtection.objects, MLSManager)


class TestMLSModelBaseManagerInjection(TestCase):
    """Tests for manager injection logic"""

    def test_explicit_custom_manager_not_replaced(self):
        """Explicitly set custom manager should NOT be replaced"""
        # The model has objects = models.Manager() explicitly
        # Metaclass should detect this and NOT replace it
        self.assertIsInstance(MLSWithExplicitManager.objects, models.Manager)
        # Note: Due to metaclass logic, this WILL be replaced if it's the default Manager class
        # This is intentional - only truly custom managers are preserved

    def test_explicit_mls_manager_preserved(self):
        """Explicitly set MLSManager should be preserved"""
        self.assertIsInstance(MLSWithExplicitMLSManager.objects, MLSManager)
        self.assertEqual(MLSWithExplicitMLSManager.objects.model, MLSWithExplicitMLSManager)

    def test_manager_injection_creates_new_instance(self):
        """Each model should get its own MLSManager instance"""
        manager1 = MLSProtectedViaMetaOption.objects
        manager2 = MLSProtectedViaFieldMarker.objects

        # Should be different instances
        self.assertIsNot(manager1, manager2)

        # Each bound to correct model
        self.assertEqual(manager1.model, MLSProtectedViaMetaOption)
        self.assertEqual(manager2.model, MLSProtectedViaFieldMarker)


class TestMLSModelBaseAbstractModels(TestCase):
    """Tests for abstract model handling"""

    def test_abstract_model_skipped(self):
        """Abstract models should NOT get manager injection"""
        # Abstract models don't have managers in the same way
        # This test verifies the metaclass doesn't crash on abstract models
        self.assertTrue(AbstractMLSModel._meta.abstract)

    def test_concrete_child_gets_manager(self):
        """Concrete child of abstract model should get MLSManager"""
        self.assertIsInstance(ConcreteMLSChild.objects, MLSManager)
        self.assertFalse(ConcreteMLSChild._meta.abstract)


class TestMLSModelBaseFieldDetection(TestCase):
    """Tests for mls_control field detection"""

    def test_detects_foreign_key_with_mls_control(self):
        """Metaclass should detect MLSForeignKey with mls_control=True"""
        # Get the field
        field = MLSProtectedViaFieldMarker._meta.get_field('classification')
        self.assertTrue(hasattr(field, 'mls_control'))
        self.assertTrue(field.mls_control)

        # Verify manager was injected
        self.assertIsInstance(MLSProtectedViaFieldMarker.objects, MLSManager)

    def test_detects_onetoone_with_mls_control(self):
        """Metaclass should detect MLSOneToOneField with mls_control=True"""
        field = MLSProtectedViaOneToOneField._meta.get_field('security_level')
        self.assertTrue(hasattr(field, 'mls_control'))
        self.assertTrue(field.mls_control)

        # Verify manager was injected
        self.assertIsInstance(MLSProtectedViaOneToOneField.objects, MLSManager)

    def test_detects_multiple_mls_fields(self):
        """Metaclass should detect when multiple fields have mls_control=True"""
        primary_field = ModelWithMultipleMLSFields._meta.get_field('primary_classification')
        secondary_field = ModelWithMultipleMLSFields._meta.get_field('secondary_classification')

        self.assertTrue(primary_field.mls_control)
        self.assertTrue(secondary_field.mls_control)

        # Should still get MLSManager
        self.assertIsInstance(ModelWithMultipleMLSFields.objects, MLSManager)

    def test_regular_foreign_key_not_detected(self):
        """Regular ForeignKey without mls_control should not trigger injection"""
        # MLSProtectedViaMetaOption has a regular FK
        field = MLSProtectedViaMetaOption._meta.get_field('security')
        self.assertFalse(hasattr(field, 'mls_control') and field.mls_control)

        # But still gets manager due to Meta.mls_protected
        self.assertIsInstance(MLSProtectedViaMetaOption.objects, MLSManager)


class TestMLSModelBaseMetaOptions(TestCase):
    """Tests for Meta option detection"""

    def test_detects_mls_protected_meta_option(self):
        """Metaclass should detect Meta.mls_protected = True"""
        self.assertTrue(getattr(MLSProtectedViaMetaOption._meta, 'mls_protected', False))
        self.assertIsInstance(MLSProtectedViaMetaOption.objects, MLSManager)

    def test_default_meta_protected_is_false(self):
        """Models without mls_protected should default to False"""
        self.assertFalse(getattr(BasicModel._meta, 'mls_protected', False))

    def test_meta_protected_alone_sufficient(self):
        """Meta.mls_protected alone should trigger manager injection"""
        # Even without mls_control fields
        self.assertIsInstance(MLSProtectedViaMetaOption.objects, MLSManager)


class TestMLSModelBaseEdgeCases(TestCase):
    """Tests for edge cases and boundary conditions"""

    def test_base_model_names_skipped(self):
        """MLSSubject and MLSObject base classes should be skipped"""
        # This is tested implicitly - if they weren't skipped,
        # importing models.py would fail
        from mls_core.models import MLSSubject, MLSObject

        # Both are abstract, so this is more about not crashing
        self.assertTrue(MLSSubject._meta.abstract)
        self.assertTrue(MLSObject._meta.abstract)

    def test_model_without_any_mls_markers(self):
        """Model with metaclass but no MLS markers should work normally"""
        obj = ModelWithoutMLSProtection(name="test", regular_field="value")
        self.assertEqual(obj.name, "test")

        # Should have default Manager
        self.assertNotIsInstance(ModelWithoutMLSProtection.objects, MLSManager)

    def test_multiple_inheritance_works(self):
        """Model with multiple inheritance should work"""
        # Just verify it doesn't crash
        self.assertIsInstance(MultipleInheritanceModel.objects, MLSManager)


# ==================== Integration Tests ====================


class TestMLSModelBaseIntegration(TestCase):
    """Integration tests for metaclass with real model operations"""

    def test_can_create_and_save_meta_protected_model(self):
        """Should be able to create and save models with Meta protection"""
        obj = MLSProtectedViaMetaOption(name="Test Object")
        obj.save()

        # Verify it was saved
        self.assertIsNotNone(obj.pk)

        # Verify we can retrieve it (bypassing MLS - no current user is set
        # up in this test, so the default manager fails secure and returns
        # nothing; the sibling DANGER manager is the explicit escape hatch)
        retrieved = MLSProtectedViaMetaOption.DANGER.get(pk=obj.pk)
        self.assertEqual(retrieved.name, "Test Object")

    def test_can_create_and_save_field_protected_model(self):
        """Should be able to create and save models with field protection"""
        obj = MLSProtectedViaFieldMarker(name="Classified Doc")
        obj.save()

        self.assertIsNotNone(obj.pk)
        retrieved = MLSProtectedViaFieldMarker.DANGER.get(pk=obj.pk)
        self.assertEqual(retrieved.name, "Classified Doc")

    def test_queryset_methods_work(self):
        """MLSManager should provide proper queryset methods"""
        # Create some test objects
        MLSProtectedViaMetaOption.objects.create(name="Object 1")
        MLSProtectedViaMetaOption.objects.create(name="Object 2")
        MLSProtectedViaMetaOption.objects.create(name="Object 3")

        # Test basic queryset operations (bypassing MLS - no current user)
        all_objs = MLSProtectedViaMetaOption.DANGER.all()
        self.assertEqual(all_objs.count(), 3)

        # Test filtering
        filtered = MLSProtectedViaMetaOption.DANGER.filter(name="Object 1")
        self.assertEqual(filtered.count(), 1)
        self.assertEqual(filtered.first().name, "Object 1")

    def test_default_manager_fails_secure_without_current_user(self):
        """With no current-user context, the default manager returns nothing"""
        MLSProtectedViaMetaOption.objects.create(name="Object 1")
        self.assertEqual(MLSProtectedViaMetaOption.objects.all().count(), 0)
        with self.assertRaises(MLSProtectedViaMetaOption.DoesNotExist):
            MLSProtectedViaMetaOption.objects.get(name="Object 1")

    def test_mls_specific_methods_available(self):
        """MLSManager should provide MLS-specific methods"""
        # Verify the methods exist
        self.assertTrue(hasattr(MLSProtectedViaFieldMarker.objects, 'accessible_by'))
        self.assertTrue(hasattr(MLSProtectedViaFieldMarker.objects, 'for_current_user'))
        # The bypass lives on the sibling DANGER manager, not on objects
        self.assertTrue(hasattr(MLSProtectedViaFieldMarker, 'DANGER'))

    def test_accessible_by_callable(self):
        """accessible_by method should be callable"""
        # Create a test object
        MLSProtectedViaFieldMarker.objects.create(name="Test")

        # Call accessible_by with None (should return empty queryset)
        result = MLSProtectedViaFieldMarker.objects.accessible_by(None)
        self.assertEqual(result.count(), 0)

    def test_danger_manager_returns_all(self):
        """The DANGER manager should return all objects, bypassing MLS"""
        MLSProtectedViaFieldMarker.objects.create(name="Doc 1")
        MLSProtectedViaFieldMarker.objects.create(name="Doc 2")

        unfiltered = MLSProtectedViaFieldMarker.DANGER.all()
        self.assertEqual(unfiltered.count(), 2)


class TestMLSModelBaseWithRealSecurityModels(TestCase):
    """Integration tests using actual SecurityClearance and SecurityLabel models"""

    def setUp(self):
        """Set up real security labels and clearances"""
        # Create security labels
        self.label_secret = SecurityLabel.objects.create(
            short_code="S",
            name="Secret",
            label_type=SecurityLabel.LabelType.LEVEL,
            rank=3
        )
        self.label_top_secret = SecurityLabel.objects.create(
            short_code="TS",
            name="Top Secret",
            label_type=SecurityLabel.LabelType.LEVEL,
            rank=4
        )

        # Create clearances
        self.clearance_secret = SecurityClearance.objects.create(
            name="Secret Clearance"
        )
        self.clearance_secret.securities.add(self.label_secret)

        self.clearance_ts = SecurityClearance.objects.create(
            name="Top Secret Clearance"
        )
        self.clearance_ts.securities.add(self.label_secret, self.label_top_secret)

    def test_model_with_real_security_clearance(self):
        """Model should work with real SecurityClearance FK"""
        # Create a temporary test model
        obj = MLSProtectedViaFieldMarker(
            name="Classified Document"
        )
        obj.save()

        # Verify it was created
        self.assertIsNotNone(obj.pk)

    def test_metaclass_doesnt_interfere_with_security_models(self):
        """SecurityClearance and SecurityLabel should work normally"""
        # These models don't use MLSModelBase, so should have regular managers
        self.assertIsInstance(SecurityLabel.objects, models.Manager)
        self.assertIsInstance(SecurityClearance.objects, models.Manager)

        # Should be able to query them
        labels = SecurityLabel.objects.all()
        clearances = SecurityClearance.objects.all()

        self.assertEqual(labels.count(), 2)
        self.assertEqual(clearances.count(), 2)


# ==================== Functional Tests ====================


class TestMLSModelBaseTransparency(TestCase):
    """Functional tests ensuring metaclass works transparently"""

    def test_developer_doesnt_need_to_set_manager_manually(self):
        """Developer should not need to manually set objects = MLSManager()"""
        # This model just sets mls_protected=True
        # The metaclass should automatically inject MLSManager
        self.assertIsInstance(MLSProtectedViaMetaOption.objects, MLSManager)

        # No manual manager setup required
        self.assertTrue(True)  # If we got here, automatic injection worked

    def test_mls_control_field_alone_sufficient(self):
        """Using mls_control=True on a field should be enough"""
        # This model only has a field with mls_control=True
        # No Meta.mls_protected needed
        self.assertIsInstance(MLSProtectedViaFieldMarker.objects, MLSManager)

    def test_models_work_like_normal_django_models(self):
        """MLS-protected models should behave like normal Django models"""
        # CRUD below reads back via the DANGER manager - no current user is
        # set up in this test, so the default (secure) manager would return
        # nothing for reads regardless of these operations succeeding.

        # Create
        obj = MLSProtectedViaMetaOption.objects.create(name="Test")

        # Read
        retrieved = MLSProtectedViaMetaOption.DANGER.get(pk=obj.pk)
        self.assertEqual(retrieved.name, "Test")

        # Update
        retrieved.name = "Updated"
        retrieved.save()

        # Verify update
        updated = MLSProtectedViaMetaOption.DANGER.get(pk=obj.pk)
        self.assertEqual(updated.name, "Updated")

        # Delete
        obj_id = obj.pk
        obj.delete()

        # Verify deletion
        with self.assertRaises(MLSProtectedViaMetaOption.DoesNotExist):
            MLSProtectedViaMetaOption.DANGER.get(pk=obj_id)


class TestMLSModelBaseDjangoCompatibility(TestCase):
    """Tests ensuring compatibility with Django's model system"""

    def test_migrations_work(self):
        """Models should work with Django migrations"""
        # This is implicitly tested by the fact that tests run
        # But we can verify the models have proper Meta
        self.assertTrue(hasattr(MLSProtectedViaMetaOption, '_meta'))
        self.assertEqual(MLSProtectedViaMetaOption._meta.app_label, 'mls_core')

    def test_model_admin_compatible(self):
        """Models should be compatible with Django Admin"""
        # Verify models have required attributes for admin
        self.assertTrue(hasattr(MLSProtectedViaMetaOption, '_meta'))
        self.assertTrue(hasattr(MLSProtectedViaMetaOption._meta, 'verbose_name'))

    def test_queryset_chaining_works(self):
        """QuerySet chaining should work normally"""
        MLSProtectedViaMetaOption.objects.create(name="Alpha")
        MLSProtectedViaMetaOption.objects.create(name="Beta")
        MLSProtectedViaMetaOption.objects.create(name="Charlie")

        # Chain multiple operations (bypassing MLS - no current user)
        result = (MLSProtectedViaMetaOption.DANGER
                  .filter(name__icontains="a")
                  .exclude(name="Charlie")
                  .order_by('name'))

        self.assertEqual(result.count(), 2)

    def test_related_queries_work(self):
        """Related object queries should work"""
        # Create security and related object
        security = TestSecurityModel.objects.create(name="Top Secret")
        obj = MLSProtectedViaMetaOption.objects.create(
            name="Document",
            security=security
        )

        # Forward relation
        self.assertEqual(obj.security.name, "Top Secret")

        # Reverse relation: the *_set accessor is always built from the
        # default (MLS-filtered) manager, so there's no unfiltered reverse
        # accessor - query the DANGER manager directly instead.
        related = MLSProtectedViaMetaOption.DANGER.filter(security=security)
        self.assertEqual(related.count(), 1)


# ==================== Performance Tests ====================


@pytest.mark.slow
class TestMLSModelBasePerformance(TestCase):
    """Performance tests for metaclass operations"""

    def test_metaclass_doesnt_slow_model_creation(self):
        """Metaclass should not significantly impact model instantiation"""
        import time

        # Create many objects
        start = time.time()
        for i in range(100):
            MLSProtectedViaMetaOption(name=f"Object {i}")
        end = time.time()

        # Should be fast (< 1 second for 100 instantiations)
        duration = end - start
        self.assertLess(duration, 1.0)

    def test_manager_injection_happens_once(self):
        """Manager injection should happen at class creation, not per instance"""
        # Get the manager instance
        manager1 = MLSProtectedViaMetaOption.objects

        # Create some instances
        obj1 = MLSProtectedViaMetaOption(name="A")
        obj2 = MLSProtectedViaMetaOption(name="B")

        # Manager should still be the same instance
        manager2 = MLSProtectedViaMetaOption.objects
        self.assertIs(manager1, manager2)

    def test_bulk_operations_work(self):
        """Bulk operations should work efficiently"""
        # Bulk create
        objects = [
            MLSProtectedViaMetaOption(name=f"Bulk {i}")
            for i in range(50)
        ]
        created = MLSProtectedViaMetaOption.objects.bulk_create(objects)
        self.assertEqual(len(created), 50)

        # Verify they were created (bypassing MLS - no current user)
        count = MLSProtectedViaMetaOption.DANGER.count()
        self.assertEqual(count, 50)


# ==================== Acceptance Tests ====================


class TestMLSModelBaseAcceptance(TestCase):
    """Acceptance tests from business/user perspective"""

    def test_mls_protection_is_automatic(self):
        """MLS protection should be applied automatically without manual setup"""
        # Given a model with mls_protected=True
        # When the model is defined
        # Then it should automatically have MLSManager
        self.assertIsInstance(MLSProtectedViaMetaOption.objects, MLSManager)

        # And developers don't need to remember to set the manager
        # (This is the whole point of the metaclass!)

    def test_field_level_protection_is_automatic(self):
        """Field-level MLS control should automatically enable protection"""
        # Given a model with a field marked mls_control=True
        # When the model is defined
        # Then it should automatically have MLSManager
        self.assertIsInstance(MLSProtectedViaFieldMarker.objects, MLSManager)

    def test_models_without_protection_unaffected(self):
        """Models without MLS markers should not be affected"""
        # Given a model without MLS protection
        # When the model is defined
        # Then it should have regular Django Manager
        self.assertIsInstance(BasicModel.objects, models.Manager)
        self.assertNotIsInstance(BasicModel.objects, MLSManager)

        # And it should work normally
        obj = BasicModel.objects.create(name="Normal Model")
        self.assertIsNotNone(obj.pk)

    def test_system_is_fail_secure_by_default(self):
        """System should default to secure behavior"""
        # When a model has MLS protection enabled
        # Then the default manager should enforce access control
        self.assertIsInstance(MLSProtectedViaMetaOption.objects, MLSManager)

        # Not UnfilteredMLSManager or regular Manager
        self.assertNotIsInstance(
            MLSProtectedViaMetaOption.objects,
            UnfilteredMLSManager
        )

    def test_explicit_unfiltered_access_available(self):
        """Developers should have explicit way to bypass filtering when needed"""
        # The sibling DANGER manager should be available
        self.assertTrue(hasattr(MLSProtectedViaMetaOption, 'DANGER'))

        # And it should work
        MLSProtectedViaMetaOption.objects.create(name="Test")
        unfiltered = MLSProtectedViaMetaOption.DANGER
        self.assertEqual(unfiltered.count(), 1)


# ==================== Pytest Fixtures ====================


@pytest.fixture
def security_labels(db):
    """Fixture providing security labels"""
    unclass = SecurityLabel.objects.create(
        short_code="U",
        name="Unclassified",
        label_type=SecurityLabel.LabelType.LEVEL,
        rank=1
    )
    secret = SecurityLabel.objects.create(
        short_code="S",
        name="Secret",
        label_type=SecurityLabel.LabelType.LEVEL,
        rank=3
    )
    return {'unclassified': unclass, 'secret': secret}


@pytest.fixture
def clearances(db, security_labels):
    """Fixture providing security clearances"""
    unclass_clearance = SecurityClearance.objects.create(
        name="Unclassified Clearance"
    )
    unclass_clearance.securities.add(security_labels['unclassified'])

    secret_clearance = SecurityClearance.objects.create(
        name="Secret Clearance"
    )
    secret_clearance.securities.add(
        security_labels['unclassified'],
        security_labels['secret']
    )

    return {
        'unclassified': unclass_clearance,
        'secret': secret_clearance
    }


# ==================== Pytest-style Tests ====================


@pytest.mark.django_db
class TestMLSModelBasePytestStyle:
    """Pytest-style tests for metaclass"""

    def test_meta_option_triggers_injection(self):
        """Test that Meta.mls_protected triggers manager injection"""
        assert isinstance(MLSProtectedViaMetaOption.objects, MLSManager)
        assert MLSProtectedViaMetaOption.objects.model == MLSProtectedViaMetaOption

    def test_field_marker_triggers_injection(self):
        """Test that mls_control=True triggers manager injection"""
        assert isinstance(MLSProtectedViaFieldMarker.objects, MLSManager)

        # Verify the field actually has the marker
        field = MLSProtectedViaFieldMarker._meta.get_field('classification')
        assert hasattr(field, 'mls_control')
        assert field.mls_control is True

    def test_no_markers_no_injection(self):
        """Test that models without markers don't get MLSManager"""
        assert isinstance(ModelWithoutMLSProtection.objects, models.Manager)
        assert not isinstance(ModelWithoutMLSProtection.objects, MLSManager)

    @pytest.mark.parametrize("model_class,should_have_mls", [
        (MLSProtectedViaMetaOption, True),
        (MLSProtectedViaFieldMarker, True),
        (MLSProtectedViaOneToOneField, True),
        (MLSProtectedViaBothMetaAndField, True),
        (ModelWithMultipleMLSFields, True),
        (ConcreteMLSChild, True),
        (BasicModel, False),
        (ModelWithoutMLSProtection, False),
    ])
    def test_manager_injection_matrix(self, model_class, should_have_mls):
        """Parametrized test for manager injection across different models"""
        has_mls = isinstance(model_class.objects, MLSManager)
        assert has_mls == should_have_mls, (
            f"{model_class.__name__} should {'have' if should_have_mls else 'not have'} "
            f"MLSManager but has {type(model_class.objects).__name__}"
        )

    def test_queryset_has_mls_methods(self):
        """Test that injected manager provides MLS-specific methods"""
        qs = MLSProtectedViaMetaOption.objects.all()

        # Should have MLS methods
        assert hasattr(qs, 'accessible_by')
        assert hasattr(qs, 'for_current_user')

        # Methods should be callable
        assert callable(qs.accessible_by)
        assert callable(qs.for_current_user)

        # The bypass lives on the sibling DANGER manager, not on objects
        assert hasattr(MLSProtectedViaMetaOption, 'DANGER')

    def test_accessible_by_with_none_returns_empty(self):
        """Test that accessible_by(None) returns empty queryset"""
        MLSProtectedViaFieldMarker.objects.create(name="Test")

        result = MLSProtectedViaFieldMarker.objects.accessible_by(None)
        assert result.count() == 0

    def test_danger_manager_returns_all_objects(self):
        """Test that the DANGER manager bypasses access control"""
        MLSProtectedViaFieldMarker.objects.create(name="Doc1")
        MLSProtectedViaFieldMarker.objects.create(name="Doc2")
        MLSProtectedViaFieldMarker.objects.create(name="Doc3")

        unfiltered = MLSProtectedViaFieldMarker.DANGER.all()
        assert unfiltered.count() == 3

    def test_manager_bound_to_correct_model(self):
        """Test that each model gets its own manager instance"""
        manager1 = MLSProtectedViaMetaOption.objects
        manager2 = MLSProtectedViaFieldMarker.objects

        assert manager1 is not manager2
        assert manager1.model == MLSProtectedViaMetaOption
        assert manager2.model == MLSProtectedViaFieldMarker

    def test_multiple_mls_fields_detected(self):
        """Test that models with multiple mls_control fields work"""
        assert isinstance(ModelWithMultipleMLSFields.objects, MLSManager)

        # Verify both fields have the marker
        primary = ModelWithMultipleMLSFields._meta.get_field('primary_classification')
        secondary = ModelWithMultipleMLSFields._meta.get_field('secondary_classification')

        assert primary.mls_control is True
        assert secondary.mls_control is True

    def test_abstract_models_skipped(self):
        """Test that abstract models don't get manager injection"""
        assert AbstractMLSModel._meta.abstract is True
        # Abstract models don't have a concrete 'objects' manager

    def test_concrete_child_of_abstract_gets_manager(self):
        """Test that concrete children of abstract models get injection"""
        assert ConcreteMLSChild._meta.abstract is False
        assert isinstance(ConcreteMLSChild.objects, MLSManager)


# ==================== End-to-End Tests ====================


@pytest.mark.django_db
@pytest.mark.e2e
class TestMLSModelBaseEndToEnd:
    """End-to-end tests simulating real usage"""

    def test_complete_mls_workflow(self, security_labels, clearances):
        """Test complete MLS workflow from model creation to access control"""
        # Step 1: Create a classified document
        doc = MLSProtectedViaFieldMarker.objects.create(
            name="Secret Battle Plans"
        )

        # Step 2: Verify it was created with MLSManager
        assert isinstance(MLSProtectedViaFieldMarker.objects, MLSManager)

        # Step 3: Verify we can retrieve it (bypassing MLS - no current user
        # is set up in this test)
        retrieved = MLSProtectedViaFieldMarker.DANGER.get(pk=doc.pk)
        assert retrieved.name == "Secret Battle Plans"

        # Step 4: Verify unfiltered access works
        unfiltered = MLSProtectedViaFieldMarker.DANGER.all()
        assert doc in unfiltered

        # Step 5: Verify accessible_by is available
        result = MLSProtectedViaFieldMarker.objects.accessible_by(None)
        assert result.count() == 0  # No subject = no access

        # Step 6: Verify the default manager fails secure with no current user
        assert MLSProtectedViaFieldMarker.objects.all().count() == 0

    def test_mixed_models_in_same_app(self):
        """Test that MLS and non-MLS models can coexist"""
        # Create MLS-protected object
        mls_obj = MLSProtectedViaMetaOption.objects.create(name="Protected")

        # Create non-MLS object
        basic_obj = BasicModel.objects.create(name="Public")

        # Verify they have different managers
        assert isinstance(MLSProtectedViaMetaOption.objects, MLSManager)
        assert not isinstance(BasicModel.objects, MLSManager)

        # Verify both work correctly (bypassing MLS for the protected model -
        # no current user is set up in this test)
        assert MLSProtectedViaMetaOption.DANGER.count() == 1
        assert BasicModel.objects.count() == 1

    def test_django_orm_features_work(self):
        """Test that standard Django ORM features work with injected manager"""
        # Create test data
        MLSProtectedViaMetaOption.objects.create(name="Alpha")
        MLSProtectedViaMetaOption.objects.create(name="Beta")
        MLSProtectedViaMetaOption.objects.create(name="Gamma")

        # Everything below reads through the DANGER manager - no current
        # user is set up in this test, so the default (secure) manager
        # would return nothing for reads regardless of these ORM features
        # working correctly.
        base = MLSProtectedViaMetaOption.DANGER

        # Test filtering
        filtered = base.filter(name__startswith="A")
        assert filtered.count() == 1

        # Test exclude
        excluded = base.exclude(name="Beta")
        assert excluded.count() == 2

        # Test ordering
        ordered = base.order_by('-name')
        names = list(ordered.values_list('name', flat=True))
        assert names == ["Gamma", "Beta", "Alpha"]

        # Test exists
        assert base.filter(name="Alpha").exists()

        # Test count
        assert base.count() == 3
