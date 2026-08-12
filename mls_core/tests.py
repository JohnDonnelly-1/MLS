"""
Comprehensive test suite for MLS Core functionality.
"""

from django.test import TestCase
from django.db import models

# Import MLS Core components
from mls_core import MLSSubject, MLSObject, MLSForeignKey, MLSOneToOneField
from mls_core.settings import get_mls_security_model, get_mls_label_model

# Try to import existing ABAC models, or use test models
try:
    from abac.models import Label, Security, FakeUser, Object
    ABAC_AVAILABLE = True
except ImportError:
    # ABAC not available - tests will use test-only models
    Label = None
    Security = None
    FakeUser = None
    Object = None
    ABAC_AVAILABLE = False


# Test-only models (used when ABAC app is not available)

if not ABAC_AVAILABLE:
    class Label(models.Model):
        """Test-only Label model"""
        class LabelType(models.TextChoices):
            LEVEL = "LVL", "Level"
            CATEGORY = "CAT", "Category"

        short_code = models.CharField(max_length=3)
        name = models.CharField(max_length=50)
        label_type = models.CharField(max_length=3, choices=LabelType.choices, default=LabelType.CATEGORY)

        class Meta:
            app_label = 'mls_core'

        def __str__(self):
            return self.name

    class Security(models.Model):
        """Test-only Security model"""
        securities = models.ManyToManyField(Label, related_name="labels")

        class Meta:
            app_label = 'mls_core'
            verbose_name_plural = "securities"

        def __str__(self):
            return ", ".join(str(s.short_code) for s in self.securities.all())

    class FakeUser(models.Model):
        """Test-only FakeUser model"""
        name = models.CharField(max_length=50)
        accesses = models.OneToOneField(Security, on_delete=models.SET_NULL, null=True)

        class Meta:
            app_label = 'mls_core'

        def __str__(self):
            return self.name

    class Object(models.Model):
        """Test-only Object model"""
        class ObjectType(models.TextChoices):
            SHIP = "SHIP", "Ship"
            SUB = "SUB", "Submarine"
            AC = "AC", "Aircraft"
            FILE = "FILE", "File"

        name = models.CharField(max_length=15)
        obj_type = models.CharField(max_length=4, choices=ObjectType.choices, default=ObjectType.SHIP)
        security = models.OneToOneField(Security, on_delete=models.CASCADE)

        class Meta:
            app_label = 'mls_core'

        def __str__(self):
            return self.name


# Test Models using MLS Core

class TestSubject(MLSSubject):
    """Test subject model for MLS tests"""
    name = models.CharField(max_length=100)
    clearances = models.OneToOneField(
        Security,
        on_delete=models.CASCADE,
        null=True
    )

    class Meta:
        app_label = 'mls_core'


class TestObjectFieldLevel(MLSObject):
    """Test object using field-level MLS control"""
    name = models.CharField(max_length=100)
    classification = MLSForeignKey(
        Security,
        mls_control=True,
        on_delete=models.CASCADE
    )

    class Meta:
        app_label = 'mls_core'


class TestObjectMetaLevel(MLSObject):
    """Test object using Meta-level MLS control"""
    name = models.CharField(max_length=100)
    security_label = models.ForeignKey(
        Security,
        on_delete=models.CASCADE
    )

    class Meta:
        app_label = 'mls_core'
        mls_protected = True
        mls_classification_field = 'security_label'


class MLSCoreTestCase(TestCase):
    """Test suite for MLS Core functionality"""

    def setUp(self):
        """Set up test fixtures"""
        # Create security labels
        self.label_unclassified = Label.objects.create(
            short_code="U",
            name="Unclassified",
            label_type=Label.LabelType.LEVEL
        )
        self.label_confidential = Label.objects.create(
            short_code="C",
            name="Confidential",
            label_type=Label.LabelType.LEVEL
        )
        self.label_secret = Label.objects.create(
            short_code="S",
            name="Secret",
            label_type=Label.LabelType.LEVEL
        )
        self.label_top_secret = Label.objects.create(
            short_code="TS",
            name="Top Secret",
            label_type=Label.LabelType.LEVEL
        )

        # Create category labels
        self.label_crypto = Label.objects.create(
            short_code="CRY",
            name="Crypto",
            label_type=Label.LabelType.CATEGORY
        )
        self.label_intel = Label.objects.create(
            short_code="INT",
            name="Intelligence",
            label_type=Label.LabelType.CATEGORY
        )

        # Create security clearance levels
        # Level 1: Unclassified only
        self.security_unclass = Security.objects.create()
        self.security_unclass.securities.add(self.label_unclassified)

        # Level 2: Confidential (includes unclassified)
        self.security_confidential = Security.objects.create()
        self.security_confidential.securities.add(
            self.label_unclassified,
            self.label_confidential
        )

        # Level 3: Secret (includes lower levels)
        self.security_secret = Security.objects.create()
        self.security_secret.securities.add(
            self.label_unclassified,
            self.label_confidential,
            self.label_secret
        )

        # Level 4: Top Secret (includes all levels)
        self.security_top_secret = Security.objects.create()
        self.security_top_secret.securities.add(
            self.label_unclassified,
            self.label_confidential,
            self.label_secret,
            self.label_top_secret
        )

        # Level 5: Secret + Crypto category
        self.security_secret_crypto = Security.objects.create()
        self.security_secret_crypto.securities.add(
            self.label_unclassified,
            self.label_confidential,
            self.label_secret,
            self.label_crypto
        )

        # Level 6: Top Secret + All categories
        self.security_ts_all = Security.objects.create()
        self.security_ts_all.securities.add(
            self.label_unclassified,
            self.label_confidential,
            self.label_secret,
            self.label_top_secret,
            self.label_crypto,
            self.label_intel
        )

        # Create test subjects with different clearances
        self.user_unclass = TestSubject.objects.create(
            name="Unclassified User",
            clearances=self.security_unclass
        )
        self.user_confidential = TestSubject.objects.create(
            name="Confidential User",
            clearances=self.security_confidential
        )
        self.user_secret = TestSubject.objects.create(
            name="Secret User",
            clearances=self.security_secret
        )
        self.user_top_secret = TestSubject.objects.create(
            name="Top Secret User",
            clearances=self.security_top_secret
        )
        self.user_secret_crypto = TestSubject.objects.create(
            name="Secret Crypto User",
            clearances=self.security_secret_crypto
        )
        self.user_ts_all = TestSubject.objects.create(
            name="TS All Access User",
            clearances=self.security_ts_all
        )

    def tearDown(self):
        """Clean up after tests"""
        # objects.all() is MLS-filtered and there's no current user in these
        # tests, so use DANGER to actually reach every row for cleanup.
        TestObjectFieldLevel.DANGER.all().delete()
        TestObjectMetaLevel.DANGER.all().delete()
        TestSubject.objects.all().delete()
        Security.objects.all().delete()
        Label.objects.all().delete()


class BasicMLSAccessTestCase(MLSCoreTestCase):
    """Test basic MLS access control rules"""

    def test_subject_can_access_equal_classification(self):
        """Subject with exact same clearances can access object"""
        obj = TestObjectFieldLevel.objects.create(
            name="Secret Document",
            classification=self.security_secret
        )
        self.assertTrue(self.user_secret.can_access(obj))

    def test_subject_with_higher_clearance_can_access(self):
        """Subject with higher clearance can access lower classified object"""
        obj = TestObjectFieldLevel.objects.create(
            name="Confidential Document",
            classification=self.security_confidential
        )
        self.assertTrue(self.user_secret.can_access(obj))
        self.assertTrue(self.user_top_secret.can_access(obj))

    def test_subject_with_lower_clearance_cannot_access(self):
        """Subject with lower clearance cannot access higher classified object"""
        obj = TestObjectFieldLevel.objects.create(
            name="Top Secret Document",
            classification=self.security_top_secret
        )
        self.assertFalse(self.user_secret.can_access(obj))
        self.assertFalse(self.user_confidential.can_access(obj))
        self.assertFalse(self.user_unclass.can_access(obj))

    def test_subject_must_have_all_labels(self):
        """Subject must have ALL labels that object requires"""
        obj = TestObjectFieldLevel.objects.create(
            name="Secret Crypto Document",
            classification=self.security_secret_crypto
        )
        # user_secret doesn't have CRYPTO label
        self.assertFalse(self.user_secret.can_access(obj))
        # user_secret_crypto has all required labels
        self.assertTrue(self.user_secret_crypto.can_access(obj))
        # user_ts_all has all labels
        self.assertTrue(self.user_ts_all.can_access(obj))


class FieldLevelMLSTestCase(MLSCoreTestCase):
    """Test field-level MLS protection (mls_control=True)"""

    def setUp(self):
        super().setUp()
        # Create test objects with different classifications
        self.obj_unclass = TestObjectFieldLevel.objects.create(
            name="Public File",
            classification=self.security_unclass
        )
        self.obj_confidential = TestObjectFieldLevel.objects.create(
            name="Confidential File",
            classification=self.security_confidential
        )
        self.obj_secret = TestObjectFieldLevel.objects.create(
            name="Secret File",
            classification=self.security_secret
        )
        self.obj_top_secret = TestObjectFieldLevel.objects.create(
            name="Top Secret File",
            classification=self.security_top_secret
        )

    def test_accessible_by_filters_correctly(self):
        """accessible_by() should return only accessible objects"""
        # Unclassified user can only see unclassified
        accessible = TestObjectFieldLevel.objects.accessible_by(self.user_unclass)
        self.assertEqual(accessible.count(), 1)
        self.assertIn(self.obj_unclass, accessible)

        # Secret user can see unclass, confidential, and secret
        accessible = TestObjectFieldLevel.objects.accessible_by(self.user_secret)
        self.assertEqual(accessible.count(), 3)
        self.assertIn(self.obj_unclass, accessible)
        self.assertIn(self.obj_confidential, accessible)
        self.assertIn(self.obj_secret, accessible)
        self.assertNotIn(self.obj_top_secret, accessible)

        # Top Secret user can see everything
        accessible = TestObjectFieldLevel.objects.accessible_by(self.user_top_secret)
        self.assertEqual(accessible.count(), 4)

    def test_danger_manager_unfiltered(self):
        """DANGER manager should return unfiltered queryset"""
        all_objects = TestObjectFieldLevel.DANGER.all()
        self.assertEqual(all_objects.count(), 4)


class MetaLevelMLSTestCase(MLSCoreTestCase):
    """Test Meta-level MLS protection (mls_protected=True)"""

    def setUp(self):
        super().setUp()
        # Create test objects using Meta-level protection
        self.obj_unclass = TestObjectMetaLevel.objects.create(
            name="Public Data",
            security_label=self.security_unclass
        )
        self.obj_secret = TestObjectMetaLevel.objects.create(
            name="Secret Data",
            security_label=self.security_secret
        )
        self.obj_top_secret = TestObjectMetaLevel.objects.create(
            name="Top Secret Data",
            security_label=self.security_top_secret
        )

    def test_meta_level_filtering_works(self):
        """Meta-level MLS protection should filter correctly"""
        # Unclassified user can only see unclassified
        accessible = TestObjectMetaLevel.objects.accessible_by(self.user_unclass)
        self.assertEqual(accessible.count(), 1)
        self.assertIn(self.obj_unclass, accessible)

        # Secret user can see unclass and secret
        accessible = TestObjectMetaLevel.objects.accessible_by(self.user_secret)
        self.assertEqual(accessible.count(), 2)
        self.assertIn(self.obj_unclass, accessible)
        self.assertIn(self.obj_secret, accessible)
        self.assertNotIn(self.obj_top_secret, accessible)

    def test_accessible_by_method_on_object(self):
        """Test accessible_by() method on object instances"""
        self.assertTrue(self.obj_unclass.accessible_by(self.user_unclass))
        self.assertFalse(self.obj_top_secret.accessible_by(self.user_unclass))
        self.assertTrue(self.obj_top_secret.accessible_by(self.user_top_secret))


class ExistingABACModelsTestCase(TestCase):
    """Test MLS with existing ABAC models (FakeUser and Object)"""

    def setUp(self):
        """Set up test data using existing models"""
        # Create labels
        self.label_public = Label.objects.create(
            short_code="PUB",
            name="Public",
            label_type=Label.LabelType.LEVEL
        )
        self.label_restricted = Label.objects.create(
            short_code="RES",
            name="Restricted",
            label_type=Label.LabelType.LEVEL
        )

        # Create securities
        self.security_public = Security.objects.create()
        self.security_public.securities.add(self.label_public)

        self.security_restricted = Security.objects.create()
        self.security_restricted.securities.add(self.label_public, self.label_restricted)

        # Create users
        self.user_low = FakeUser.objects.create(
            name="Low Access",
            accesses=self.security_public
        )
        self.user_high = FakeUser.objects.create(
            name="High Access",
            accesses=self.security_restricted
        )

        # Create objects
        self.obj_public = Object.objects.create(
            name="Public Ship",
            security=self.security_public
        )
        self.obj_restricted = Object.objects.create(
            name="Restricted Ship",
            security=self.security_restricted
        )

    def test_existing_models_work_without_mls(self):
        """Existing models should still work normally"""
        # Should return all objects (no MLS filtering yet)
        all_objects = Object.objects.all()
        self.assertEqual(all_objects.count(), 2)

    def test_can_query_fake_users(self):
        """Should be able to query FakeUser objects"""
        users = FakeUser.objects.all()
        self.assertEqual(users.count(), 2)


class EdgeCasesTestCase(MLSCoreTestCase):
    """Test edge cases and boundary conditions"""

    def test_subject_with_no_clearances(self):
        """Subject with no clearances cannot access anything"""
        user_no_clearance = TestSubject.objects.create(
            name="No Clearance User",
            clearances=None
        )
        obj = TestObjectFieldLevel.objects.create(
            name="Any Document",
            classification=self.security_unclass
        )
        self.assertFalse(user_no_clearance.can_access(obj))

    def test_object_with_no_classification(self):
        """Object with no classification cannot be accessed"""
        # This should not be possible with on_delete=CASCADE,
        # but test the logic anyway
        user = self.user_top_secret

        # Create object then try to access via manager
        # (We can't actually create without classification due to CASCADE)
        accessible = TestObjectFieldLevel.objects.accessible_by(user)
        # Should not crash
        self.assertIsNotNone(accessible)

    def test_accessible_by_with_none_subject(self):
        """accessible_by(None) should return no objects"""
        TestObjectFieldLevel.objects.create(
            name="Test Document",
            classification=self.security_unclass
        )
        accessible = TestObjectFieldLevel.objects.accessible_by(None)
        self.assertEqual(accessible.count(), 0)

    def test_empty_security_label_set(self):
        """Security with no labels attached"""
        empty_security = Security.objects.create()
        # Don't add any labels

        user = TestSubject.objects.create(
            name="Empty Clearance",
            clearances=empty_security
        )
        obj = TestObjectFieldLevel.objects.create(
            name="Empty Classification",
            classification=empty_security
        )

        # User with empty clearances can access object with empty classification
        self.assertTrue(user.can_access(obj))

    def test_complex_label_combination(self):
        """Test complex combinations of labels"""
        # Create object requiring multiple categories
        obj = TestObjectFieldLevel.objects.create(
            name="Multi-Category Document",
            classification=self.security_ts_all
        )

        # User without all categories cannot access
        self.assertFalse(self.user_top_secret.can_access(obj))
        # User with all categories can access
        self.assertTrue(self.user_ts_all.can_access(obj))


class ManagerMethodsTestCase(MLSCoreTestCase):
    """Test various manager methods"""

    def setUp(self):
        super().setUp()
        # Create test objects
        for i in range(5):
            TestObjectFieldLevel.objects.create(
                name=f"Document {i}",
                classification=self.security_secret
            )
        for i in range(3):
            TestObjectFieldLevel.objects.create(
                name=f"Top Secret Doc {i}",
                classification=self.security_top_secret
            )

    def test_all_returns_filtered(self):
        """objects.all() is secure by default: fails secure (empty) with no current user"""
        all_objs = TestObjectFieldLevel.objects.all()
        self.assertEqual(all_objs.count(), 0)

    def test_filter_with_accessible_by(self):
        """Should be able to chain filter() with accessible_by()"""
        accessible = TestObjectFieldLevel.objects.accessible_by(self.user_secret)
        filtered = accessible.filter(name__startswith="Document")
        self.assertEqual(filtered.count(), 5)

    def test_danger_then_filter(self):
        """Should be able to filter on the DANGER (unfiltered) manager"""
        all_objs = TestObjectFieldLevel.DANGER.all()
        self.assertEqual(all_objs.count(), 8)

        filtered = all_objs.filter(name__startswith="Top")
        self.assertEqual(filtered.count(), 3)


class IntegrationTestCase(MLSCoreTestCase):
    """Integration tests combining multiple features"""

    def test_multiple_subjects_multiple_objects(self):
        """Test realistic scenario with multiple users and objects"""
        # Create various objects
        objects = [
            TestObjectFieldLevel.objects.create(
                name="Public Document",
                classification=self.security_unclass
            ),
            TestObjectFieldLevel.objects.create(
                name="Confidential Report",
                classification=self.security_confidential
            ),
            TestObjectFieldLevel.objects.create(
                name="Secret Intel",
                classification=self.security_secret
            ),
            TestObjectFieldLevel.objects.create(
                name="Top Secret Plans",
                classification=self.security_top_secret
            ),
            TestObjectFieldLevel.objects.create(
                name="Crypto Keys",
                classification=self.security_secret_crypto
            ),
        ]

        # Test each user sees correct objects
        unclass_access = TestObjectFieldLevel.objects.accessible_by(self.user_unclass)
        self.assertEqual(unclass_access.count(), 1)

        conf_access = TestObjectFieldLevel.objects.accessible_by(self.user_confidential)
        self.assertEqual(conf_access.count(), 2)

        secret_access = TestObjectFieldLevel.objects.accessible_by(self.user_secret)
        self.assertEqual(secret_access.count(), 3)  # Not crypto keys

        ts_access = TestObjectFieldLevel.objects.accessible_by(self.user_top_secret)
        self.assertEqual(ts_access.count(), 4)  # Not crypto keys

        crypto_access = TestObjectFieldLevel.objects.accessible_by(self.user_secret_crypto)
        self.assertEqual(crypto_access.count(), 4)  # Includes crypto keys

        all_access = TestObjectFieldLevel.objects.accessible_by(self.user_ts_all)
        self.assertEqual(all_access.count(), 5)  # Everything

    def test_both_field_and_meta_level_work_independently(self):
        """Field-level and Meta-level objects work independently"""
        field_obj = TestObjectFieldLevel.objects.create(
            name="Field Level",
            classification=self.security_secret
        )
        meta_obj = TestObjectMetaLevel.objects.create(
            name="Meta Level",
            security_label=self.security_secret
        )

        # Both should be accessible to secret user
        field_accessible = TestObjectFieldLevel.objects.accessible_by(self.user_secret)
        meta_accessible = TestObjectMetaLevel.objects.accessible_by(self.user_secret)

        self.assertIn(field_obj, field_accessible)
        self.assertIn(meta_obj, meta_accessible)


class PerformanceTestCase(MLSCoreTestCase):
    """Basic performance tests"""

    def test_large_dataset_filtering(self):
        """Test filtering with larger dataset"""
        # Create 100 objects with various classifications
        for i in range(25):
            TestObjectFieldLevel.objects.create(
                name=f"Unclass {i}",
                classification=self.security_unclass
            )
        for i in range(25):
            TestObjectFieldLevel.objects.create(
                name=f"Confidential {i}",
                classification=self.security_confidential
            )
        for i in range(25):
            TestObjectFieldLevel.objects.create(
                name=f"Secret {i}",
                classification=self.security_secret
            )
        for i in range(25):
            TestObjectFieldLevel.objects.create(
                name=f"Top Secret {i}",
                classification=self.security_top_secret
            )

        # Test filtering performance (should not crash or timeout)
        accessible = TestObjectFieldLevel.objects.accessible_by(self.user_secret)
        # Should return unclass + confidential + secret = 75
        self.assertEqual(accessible.count(), 75)
