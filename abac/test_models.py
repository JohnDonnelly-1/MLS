"""
Comprehensive pytest test suite for ABAC (Attribute-Based Access Control) models.

This test suite covers all models in the ABAC application:
- Label: Security labels (levels and categories)
- Security: Security profiles containing multiple labels
- FakeUser: Subject with security clearances
- Object: Protected objects with security classifications

Test Categories:
- Unit Tests: Test individual model functionality
- Integration Tests: Test relationships between models
- Functional Tests: Test access control scenarios
- Performance Tests: Test with large datasets
"""

import pytest
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.urls import reverse

from abac.models import Label, Security, FakeUser, Object


# ==================== Unit Tests: Label Model ====================


@pytest.mark.unit
class TestLabelModel:
    """Unit tests for the Label model"""

    def test_create_level_label(self, db):
        """Test creating a level label"""
        label = Label.objects.create(
            short_code="TST",
            name="Test Level",
            label_type=Label.LabelType.LEVEL
        )
        assert label.short_code == "TST"
        assert label.name == "Test Level"
        assert label.label_type == Label.LabelType.LEVEL
        assert str(label) == "Test Level"

    def test_create_category_label(self, db):
        """Test creating a category label"""
        label = Label.objects.create(
            short_code="CAT",
            name="Test Category",
            label_type=Label.LabelType.CATEGORY
        )
        assert label.short_code == "CAT"
        assert label.name == "Test Category"
        assert label.label_type == Label.LabelType.CATEGORY

    def test_label_default_type_is_category(self, db):
        """Test that default label type is CATEGORY"""
        label = Label.objects.create(
            short_code="DEF",
            name="Default Type"
        )
        assert label.label_type == Label.LabelType.CATEGORY

    def test_label_str_representation(self, label_public):
        """Test Label string representation returns name"""
        assert str(label_public) == "Public"

    def test_label_choices_available(self):
        """Test that label type choices are available"""
        assert Label.LabelType.LEVEL == "LVL"
        assert Label.LabelType.CATEGORY == "CAT"
        assert len(Label.LabelType.choices) == 2

    def test_label_short_code_max_length(self, db):
        """Test that short_code respects max_length of 3"""
        label = Label.objects.create(
            short_code="ABC",
            name="Valid Short Code",
            label_type=Label.LabelType.LEVEL
        )
        assert len(label.short_code) <= 3

    def test_label_name_max_length(self, db):
        """Test that name can be up to 50 characters"""
        long_name = "A" * 50
        label = Label.objects.create(
            short_code="LNG",
            name=long_name,
            label_type=Label.LabelType.LEVEL
        )
        assert len(label.name) == 50
        assert label.name == long_name

    def test_multiple_labels_can_exist(self, all_level_labels):
        """Test that multiple labels can exist simultaneously"""
        assert Label.objects.count() == 6
        assert all(isinstance(label, Label) for label in all_level_labels.values())

    def test_label_query_by_type(self, all_level_labels, all_category_labels):
        """Test querying labels by type"""
        level_labels = Label.objects.filter(label_type=Label.LabelType.LEVEL)
        category_labels = Label.objects.filter(label_type=Label.LabelType.CATEGORY)

        assert level_labels.count() == 6
        assert category_labels.count() == 4


# ==================== Unit Tests: Security Model ====================


@pytest.mark.unit
class TestSecurityModel:
    """Unit tests for the Security model"""

    def test_create_empty_security(self, db):
        """Test creating a security profile with no labels"""
        security = Security.objects.create()
        assert security.id is not None
        assert security.securities.count() == 0

    def test_add_single_label_to_security(self, security_empty, label_public):
        """Test adding a single label to security profile"""
        security_empty.securities.add(label_public)
        assert security_empty.securities.count() == 1
        assert label_public in security_empty.securities.all()

    def test_add_multiple_labels_to_security(
        self,
        security_empty,
        label_public,
        label_internal,
        label_restricted
    ):
        """Test adding multiple labels to security profile"""
        security_empty.securities.add(label_public, label_internal, label_restricted)
        assert security_empty.securities.count() == 3

    def test_security_str_shows_category_labels(
        self,
        db,
        label_public,
        label_crypto,
        label_intel
    ):
        """Test that __str__ shows category labels only"""
        security = Security.objects.create()
        security.securities.add(label_public, label_crypto, label_intel)

        # Should only show category labels
        result = str(security)
        # Since label_public is LEVEL, only crypto and intel should appear
        assert "CRY" in result or "INT" in result

    def test_security_str_with_no_categories(self, security_public):
        """Test __str__ when security has no category labels"""
        result = str(security_public)
        # Should return empty string or no categories
        assert isinstance(result, str)

    def test_security_verbose_name_plural(self):
        """Test that verbose_name_plural is 'securities'"""
        assert Security._meta.verbose_name_plural == "securities"

    def test_security_many_to_many_relationship(self, security_secret, all_level_labels):
        """Test many-to-many relationship between Security and Label"""
        labels = security_secret.securities.all()
        assert labels.count() == 5
        assert all_level_labels['public'] in labels
        assert all_level_labels['secret'] in labels

    def test_security_remove_label(self, security_internal, label_internal):
        """Test removing a label from security profile"""
        initial_count = security_internal.securities.count()
        security_internal.securities.remove(label_internal)
        assert security_internal.securities.count() == initial_count - 1
        assert label_internal not in security_internal.securities.all()

    def test_security_clear_all_labels(self, security_secret):
        """Test clearing all labels from security profile"""
        assert security_secret.securities.count() > 0
        security_secret.securities.clear()
        assert security_secret.securities.count() == 0

    def test_label_has_reverse_relationship(self, label_public, security_public):
        """Test that labels can access securities through reverse relationship"""
        securities = label_public.labels.all()
        assert security_public in securities

    def test_multiple_securities_can_share_labels(
        self,
        db,
        label_public,
        label_internal
    ):
        """Test that multiple security profiles can share the same labels"""
        security1 = Security.objects.create()
        security1.securities.add(label_public, label_internal)

        security2 = Security.objects.create()
        security2.securities.add(label_public, label_internal)

        assert label_public in security1.securities.all()
        assert label_public in security2.securities.all()


# ==================== Unit Tests: FakeUser Model ====================


@pytest.mark.unit
class TestFakeUserModel:
    """Unit tests for the FakeUser model"""

    def test_create_user_with_clearance(self, db, security_public):
        """Test creating a user with security clearance"""
        user = FakeUser.objects.create(
            name="Test User",
            accesses=security_public
        )
        assert user.name == "Test User"
        assert user.accesses == security_public

    def test_create_user_without_clearance(self, db):
        """Test creating a user without security clearance"""
        user = FakeUser.objects.create(
            name="No Access User",
            accesses=None
        )
        assert user.name == "No Access User"
        assert user.accesses is None

    def test_user_str_representation(self, user_public):
        """Test FakeUser string representation returns name"""
        assert str(user_public) == "Public User"

    def test_user_get_absolute_url(self, user_public):
        """Test get_absolute_url returns correct URL"""
        url = user_public.get_absolute_url()
        expected_url = reverse("abac:user", kwargs={"pk": user_public.pk})
        assert url == expected_url

    def test_user_name_max_length(self, db, security_public):
        """Test that name can be up to 50 characters"""
        long_name = "A" * 50
        user = FakeUser.objects.create(
            name=long_name,
            accesses=security_public
        )
        assert len(user.name) == 50
        assert user.name == long_name

    def test_user_one_to_one_with_security(self, user_secret, security_secret):
        """Test one-to-one relationship between user and security"""
        assert user_secret.accesses == security_secret
        # Security should have reverse relation to user
        assert hasattr(security_secret, 'fakeuser')

    def test_user_security_set_null_on_delete(self, db, security_public):
        """Test that user's accesses is set to NULL when security is deleted"""
        user = FakeUser.objects.create(
            name="Test User",
            accesses=security_public
        )
        security_id = security_public.id
        security_public.delete()

        user.refresh_from_db()
        assert user.accesses is None

    def test_multiple_users_with_different_clearances(self, all_users):
        """Test that multiple users can exist with different clearances"""
        assert FakeUser.objects.count() == 8
        assert all(isinstance(user, FakeUser) for user in all_users.values())

    def test_user_can_access_clearance_labels(self, user_secret, all_level_labels):
        """Test that user can access labels through security relationship"""
        labels = user_secret.accesses.securities.all()
        assert all_level_labels['public'] in labels
        assert all_level_labels['secret'] in labels

    def test_user_query_by_clearance_level(
        self,
        db,
        user_public,
        user_secret,
        security_public,
        security_secret
    ):
        """Test querying users by their clearance level"""
        secret_users = FakeUser.objects.filter(accesses=security_secret)
        assert user_secret in secret_users
        assert user_public not in secret_users


# ==================== Unit Tests: Object Model ====================


@pytest.mark.unit
class TestObjectModel:
    """Unit tests for the Object model"""

    def test_create_ship_object(self, db, security_public):
        """Test creating a ship object"""
        obj = Object.objects.create(
            name="USS Test",
            obj_type=Object.ObjectType.SHIP,
            x_coords=50,
            y_coords=50,
            security=security_public
        )
        assert obj.name == "USS Test"
        assert obj.obj_type == Object.ObjectType.SHIP
        assert obj.x_coords == 50
        assert obj.y_coords == 50
        assert obj.security == security_public

    def test_create_submarine_object(self, db, security_secret):
        """Test creating a submarine object"""
        obj = Object.objects.create(
            name="USS SubTest",
            obj_type=Object.ObjectType.SUB,
            x_coords=25,
            y_coords=75,
            security=security_secret
        )
        assert obj.obj_type == Object.ObjectType.SUB

    def test_create_aircraft_object(self, db, security_top_secret):
        """Test creating an aircraft object"""
        obj = Object.objects.create(
            name="F-22 Raptor",
            obj_type=Object.ObjectType.AC,
            x_coords=80,
            y_coords=20,
            security=security_top_secret
        )
        assert obj.obj_type == Object.ObjectType.AC

    def test_create_file_object(self, db, security_confidential):
        """Test creating a file object"""
        obj = Object.objects.create(
            name="Document.pdf",
            obj_type=Object.ObjectType.FILE,
            x_coords=10,
            y_coords=90,
            security=security_confidential
        )
        assert obj.obj_type == Object.ObjectType.FILE

    def test_object_default_type_is_ship(self, db, security_public):
        """Test that default object type is SHIP"""
        obj = Object.objects.create(
            name="Default Type",
            security=security_public
        )
        assert obj.obj_type == Object.ObjectType.SHIP

    def test_object_default_coordinates(self, db, security_public):
        """Test that default coordinates are 50, 50"""
        obj = Object.objects.create(
            name="Default Coords",
            obj_type=Object.ObjectType.SHIP,
            security=security_public
        )
        assert obj.x_coords == 50
        assert obj.y_coords == 50

    def test_object_str_representation(self, object_public_ship):
        """Test Object string representation returns name"""
        assert str(object_public_ship) == "USS Public"

    def test_object_get_absolute_url(self, object_public_ship):
        """Test get_absolute_url returns correct URL"""
        url = object_public_ship.get_absolute_url()
        expected_url = reverse("abac:object", kwargs={"pk": object_public_ship.pk})
        assert url == expected_url

    def test_object_name_max_length(self, db, security_public):
        """Test that name can be up to 15 characters"""
        name = "A" * 15
        obj = Object.objects.create(
            name=name,
            security=security_public
        )
        assert len(obj.name) == 15

    def test_object_choices_available(self):
        """Test that object type choices are available"""
        assert Object.ObjectType.SHIP == "SHIP"
        assert Object.ObjectType.SUB == "SUB"
        assert Object.ObjectType.AC == "AC"
        assert Object.ObjectType.FILE == "FILE"
        assert len(Object.ObjectType.choices) == 4

    def test_object_coordinates_validation(self, db, security_public):
        """Test that coordinates accept valid values"""
        obj = Object.objects.create(
            name="Valid Coords",
            x_coords=0,
            y_coords=100,
            security=security_public
        )
        assert obj.x_coords == 0
        assert obj.y_coords == 100

    def test_object_cascade_delete_with_security(self, db, security_public):
        """Test that object is deleted when security is deleted (CASCADE)"""
        obj = Object.objects.create(
            name="Test Delete",
            security=security_public
        )
        obj_id = obj.id
        security_public.delete()

        assert not Object.objects.filter(id=obj_id).exists()

    def test_object_one_to_one_with_security(self, object_secret_submarine, security_secret):
        """Test one-to-one relationship between object and security"""
        assert object_secret_submarine.security == security_secret
        # Security should have reverse relation
        assert hasattr(security_secret, 'object')

    def test_multiple_objects_with_different_types(self, all_objects):
        """Test that multiple objects of different types can exist"""
        assert Object.objects.count() == 4
        types = [obj.obj_type for obj in all_objects.values()]
        assert Object.ObjectType.SHIP in types
        assert Object.ObjectType.SUB in types
        assert Object.ObjectType.AC in types
        assert Object.ObjectType.FILE in types

    def test_query_objects_by_type(
        self,
        object_public_ship,
        object_secret_submarine,
        object_ts_aircraft
    ):
        """Test querying objects by type"""
        ships = Object.objects.filter(obj_type=Object.ObjectType.SHIP)
        subs = Object.objects.filter(obj_type=Object.ObjectType.SUB)
        aircraft = Object.objects.filter(obj_type=Object.ObjectType.AC)

        assert object_public_ship in ships
        assert object_secret_submarine in subs
        assert object_ts_aircraft in aircraft

    def test_query_objects_by_security_level(
        self,
        object_public_ship,
        object_secret_submarine,
        security_public,
        security_secret
    ):
        """Test querying objects by security level"""
        public_objects = Object.objects.filter(security=security_public)
        secret_objects = Object.objects.filter(security=security_secret)

        assert object_public_ship in public_objects
        assert object_secret_submarine in secret_objects


# ==================== Integration Tests: Model Relationships ====================


@pytest.mark.integration
class TestModelRelationships:
    """Integration tests for relationships between models"""

    def test_full_chain_label_to_security_to_user(
        self,
        label_public,
        security_public,
        user_public
    ):
        """Test complete relationship chain from label to user"""
        # Label -> Security -> User
        assert label_public in security_public.securities.all()
        assert user_public.accesses == security_public

        # User can access labels through security
        user_labels = user_public.accesses.securities.all()
        assert label_public in user_labels

    def test_full_chain_label_to_security_to_object(
        self,
        label_secret,
        security_secret,
        object_secret_submarine
    ):
        """Test complete relationship chain from label to object"""
        assert label_secret in security_secret.securities.all()
        assert object_secret_submarine.security == security_secret

        # Object can access labels through security
        object_labels = object_secret_submarine.security.securities.all()
        assert label_secret in object_labels

    def test_user_and_object_share_same_security(
        self,
        db,
        security_confidential
    ):
        """Test that user and object can share the same security profile"""
        user = FakeUser.objects.create(
            name="Shared Security User",
            accesses=security_confidential
        )
        obj = Object.objects.create(
            name="Shared Security Object",
            security=security_confidential
        )

        assert user.accesses == obj.security
        assert user.accesses.securities.count() == obj.security.securities.count()

    def test_multiple_users_same_clearance(self, db, security_secret):
        """Test that multiple users can have the same clearance"""
        user1 = FakeUser.objects.create(name="User 1", accesses=security_secret)
        user2 = FakeUser.objects.create(name="User 2", accesses=security_secret)

        assert user1.accesses == user2.accesses
        users_with_secret = FakeUser.objects.filter(accesses=security_secret)
        assert users_with_secret.count() == 2

    def test_security_deletion_affects_user_but_not_labels(
        self,
        db,
        label_public,
        security_public
    ):
        """Test that deleting security affects user but not labels"""
        user = FakeUser.objects.create(name="Test", accesses=security_public)
        label_id = label_public.id

        security_public.delete()

        user.refresh_from_db()
        assert user.accesses is None
        assert Label.objects.filter(id=label_id).exists()

    def test_security_deletion_cascades_to_object(
        self,
        db,
        security_restricted
    ):
        """Test that deleting security cascades to delete object"""
        obj = Object.objects.create(
            name="Cascade Test",
            security=security_restricted
        )
        obj_id = obj.id

        security_restricted.delete()

        assert not Object.objects.filter(id=obj_id).exists()

    def test_label_used_by_multiple_securities(
        self,
        label_public,
        security_public,
        security_internal,
        security_restricted
    ):
        """Test that a label can be used by multiple security profiles"""
        securities_with_public = label_public.labels.all()
        assert security_public in securities_with_public
        assert security_internal in securities_with_public
        assert security_restricted in securities_with_public

    def test_complex_multi_level_relationship(
        self,
        all_level_labels,
        all_category_labels,
        security_ts_all_categories,
        user_ts_all,
        object_crypto_file
    ):
        """Test complex relationships with multiple labels"""
        # User has all labels through security
        user_labels = user_ts_all.accesses.securities.all()
        assert all_level_labels['top_secret'] in user_labels
        assert all_category_labels['crypto'] in user_labels

        # Object has specific labels
        object_labels = object_crypto_file.security.securities.all()
        assert all_category_labels['crypto'] in object_labels

    def test_querying_across_relationships(
        self,
        label_secret,
        user_secret,
        object_secret_submarine
    ):
        """Test complex queries across relationships"""
        # Find users with specific label
        users_with_label = FakeUser.objects.filter(
            accesses__securities=label_secret
        ).distinct()
        assert user_secret in users_with_label

        # Find objects with specific label
        objects_with_label = Object.objects.filter(
            security__securities=label_secret
        ).distinct()
        assert object_secret_submarine in objects_with_label


# ==================== Functional Tests: Access Control Scenarios ====================


@pytest.mark.functional
class TestAccessControlScenarios:
    """Functional tests for real-world access control scenarios"""

    def test_public_user_cannot_access_classified_objects(
        self,
        user_public,
        object_secret_submarine,
        object_ts_aircraft
    ):
        """Test that public user cannot access classified objects"""
        user_labels = set(user_public.accesses.securities.all())

        secret_labels = set(object_secret_submarine.security.securities.all())
        ts_labels = set(object_ts_aircraft.security.securities.all())

        # User should not have all labels required for access
        assert not secret_labels.issubset(user_labels)
        assert not ts_labels.issubset(user_labels)

    def test_secret_user_can_access_lower_classified_objects(
        self,
        user_secret,
        object_public_ship
    ):
        """Test that secret user can access public objects"""
        user_labels = set(user_secret.accesses.securities.all())
        object_labels = set(object_public_ship.security.securities.all())

        # User should have all labels required
        assert object_labels.issubset(user_labels)

    def test_top_secret_user_can_access_all_level_objects(
        self,
        user_top_secret,
        object_public_ship,
        object_secret_submarine,
        object_ts_aircraft
    ):
        """Test that top secret user can access all classification level objects"""
        user_labels = set(user_top_secret.accesses.securities.all())

        public_labels = set(object_public_ship.security.securities.all())
        secret_labels = set(object_secret_submarine.security.securities.all())
        ts_labels = set(object_ts_aircraft.security.securities.all())

        assert public_labels.issubset(user_labels)
        assert secret_labels.issubset(user_labels)
        assert ts_labels.issubset(user_labels)

    def test_secret_user_cannot_access_crypto_without_clearance(
        self,
        user_secret,
        object_crypto_file
    ):
        """Test that secret user without crypto clearance cannot access crypto objects"""
        user_labels = set(user_secret.accesses.securities.all())
        crypto_labels = set(object_crypto_file.security.securities.all())

        # User should not have crypto label
        assert not crypto_labels.issubset(user_labels)

    def test_secret_crypto_user_can_access_crypto_objects(
        self,
        user_secret_crypto,
        object_crypto_file
    ):
        """Test that secret + crypto user can access crypto objects"""
        user_labels = set(user_secret_crypto.accesses.securities.all())
        crypto_labels = set(object_crypto_file.security.securities.all())

        # User should have all required labels including crypto
        assert crypto_labels.issubset(user_labels)

    def test_user_without_clearance_cannot_access_anything(
        self,
        user_no_clearance,
        object_public_ship
    ):
        """Test that user without clearance cannot access any objects"""
        assert user_no_clearance.accesses is None

    def test_compartmentalized_access_control(
        self,
        db,
        label_secret,
        label_crypto,
        label_intel,
        security_factory,
        user_factory,
        object_factory
    ):
        """Test compartmentalized access control with categories"""
        # Create security with secret + crypto
        sec_crypto = security_factory([label_secret, label_crypto])
        # Create security with secret + intel
        sec_intel = security_factory([label_secret, label_intel])

        # Create users with different compartments
        user_crypto = user_factory("Crypto User", sec_crypto)
        user_intel = user_factory("Intel User", sec_intel)

        # Create objects in different compartments
        obj_crypto = object_factory("Crypto Data", sec_crypto)
        obj_intel = object_factory("Intel Data", sec_intel)

        # Crypto user can access crypto objects but not intel
        crypto_user_labels = set(user_crypto.accesses.securities.all())
        intel_user_labels = set(user_intel.accesses.securities.all())

        crypto_obj_labels = set(obj_crypto.security.securities.all())
        intel_obj_labels = set(obj_intel.security.securities.all())

        assert crypto_obj_labels.issubset(crypto_user_labels)
        assert not intel_obj_labels.issubset(crypto_user_labels)
        assert intel_obj_labels.issubset(intel_user_labels)
        assert not crypto_obj_labels.issubset(intel_user_labels)

    def test_hierarchical_access_control(
        self,
        all_users,
        all_objects
    ):
        """Test hierarchical access control with multiple levels"""
        # Create access matrix
        access_tests = [
            (all_users['public'], all_objects['public_ship'], True),
            (all_users['public'], all_objects['secret_sub'], False),
            (all_users['secret'], all_objects['public_ship'], True),
            (all_users['secret'], all_objects['secret_sub'], True),
            (all_users['secret'], all_objects['ts_aircraft'], False),
            (all_users['top_secret'], all_objects['public_ship'], True),
            (all_users['top_secret'], all_objects['secret_sub'], True),
            (all_users['top_secret'], all_objects['ts_aircraft'], True),
        ]

        for user, obj, should_access in access_tests:
            user_labels = set(user.accesses.securities.all())
            obj_labels = set(obj.security.securities.all())
            can_access = obj_labels.issubset(user_labels)

            assert can_access == should_access, (
                f"{user.name} should {'be able to' if should_access else 'not be able to'} "
                f"access {obj.name}"
            )

    def test_need_to_know_principle(
        self,
        db,
        label_confidential,
        label_nato,
        label_crypto,
        security_factory,
        user_factory,
        object_factory
    ):
        """Test need-to-know principle with compartments"""
        # Create user with high clearance but limited compartments
        sec_conf_nato = security_factory([label_confidential, label_nato])
        user_nato = user_factory("NATO User", sec_conf_nato)

        # Create object requiring crypto compartment
        sec_conf_crypto = security_factory([label_confidential, label_crypto])
        obj_crypto = object_factory("Crypto Document", sec_conf_crypto)

        # Even though both are at confidential level, NATO user cannot access crypto
        user_labels = set(user_nato.accesses.securities.all())
        obj_labels = set(obj_crypto.security.securities.all())

        assert not obj_labels.issubset(user_labels)

    def test_multiple_simultaneous_accesses(
        self,
        user_ts_all,
        all_objects
    ):
        """Test that user with full clearance can access all objects"""
        user_labels = set(user_ts_all.accesses.securities.all())

        for obj_name, obj in all_objects.items():
            obj_labels = set(obj.security.securities.all())
            assert obj_labels.issubset(user_labels), (
                f"User with full clearance should access {obj_name}"
            )


# ==================== Functional Tests: Object Coordinate and Type Scenarios ====================


@pytest.mark.functional
class TestObjectCoordinatesAndTypes:
    """Functional tests for object coordinates and types"""

    def test_objects_at_different_coordinates(
        self,
        db,
        security_public,
        object_factory
    ):
        """Test creating objects at different coordinates"""
        obj1 = object_factory("Ship 1", security_public, x_coords=10, y_coords=20)
        obj2 = object_factory("Ship 2", security_public, x_coords=90, y_coords=80)

        assert obj1.x_coords == 10
        assert obj1.y_coords == 20
        assert obj2.x_coords == 90
        assert obj2.y_coords == 80

    def test_query_objects_by_coordinate_range(
        self,
        db,
        security_public,
        object_factory
    ):
        """Test querying objects within coordinate range"""
        obj1 = object_factory("Near", security_public, x_coords=25, y_coords=25)
        obj2 = object_factory("Far", security_public, x_coords=75, y_coords=75)

        # Query objects in lower left quadrant
        near_objects = Object.objects.filter(x_coords__lt=50, y_coords__lt=50)
        assert obj1 in near_objects
        assert obj2 not in near_objects

    def test_different_object_types_different_security(
        self,
        security_public,
        security_secret,
        security_top_secret,
        object_factory
    ):
        """Test objects of different types with different security levels"""
        ship = object_factory("Public Ship", security_public, obj_type=Object.ObjectType.SHIP)
        sub = object_factory("Secret Sub", security_secret, obj_type=Object.ObjectType.SUB)
        aircraft = object_factory("TS Aircraft", security_top_secret, obj_type=Object.ObjectType.AC)

        assert ship.obj_type == Object.ObjectType.SHIP
        assert sub.obj_type == Object.ObjectType.SUB
        assert aircraft.obj_type == Object.ObjectType.AC

        # Each has different security
        assert ship.security != sub.security
        assert sub.security != aircraft.security


# ==================== Acceptance Tests: Business Requirements ====================


@pytest.mark.acceptance
class TestBusinessRequirements:
    """Acceptance tests validating business requirements"""

    def test_system_enforces_clearance_hierarchy(
        self,
        all_level_labels,
        all_users
    ):
        """
        Business Requirement: System must enforce hierarchical clearance levels
        where higher clearances include all lower level access
        """
        # Verify that higher clearances include lower labels
        ts_labels = set(all_users['top_secret'].accesses.securities.all())
        secret_labels = set(all_users['secret'].accesses.securities.all())
        conf_labels = set(all_users['confidential'].accesses.securities.all())

        # Top Secret should include all secret labels
        assert secret_labels.issubset(ts_labels)
        # Secret should include all confidential labels
        assert conf_labels.issubset(secret_labels)

    def test_system_supports_compartmentalization(
        self,
        user_secret,
        user_secret_crypto,
        label_crypto
    ):
        """
        Business Requirement: System must support compartmentalization
        where users need specific category clearances
        """
        secret_labels = set(user_secret.accesses.securities.all())
        crypto_labels = set(user_secret_crypto.accesses.securities.all())

        # Secret user should not have crypto
        assert label_crypto not in secret_labels
        # Secret crypto user should have crypto
        assert label_crypto in crypto_labels

    def test_system_tracks_object_locations(
        self,
        object_public_ship,
        object_secret_submarine,
        object_ts_aircraft
    ):
        """
        Business Requirement: System must track object coordinates
        """
        assert hasattr(object_public_ship, 'x_coords')
        assert hasattr(object_public_ship, 'y_coords')
        assert 0 <= object_public_ship.x_coords <= 100
        assert 0 <= object_public_ship.y_coords <= 100

    def test_system_categorizes_object_types(self, all_objects):
        """
        Business Requirement: System must categorize different object types
        (ships, submarines, aircraft, files)
        """
        types = set(obj.obj_type for obj in all_objects.values())
        required_types = {
            Object.ObjectType.SHIP,
            Object.ObjectType.SUB,
            Object.ObjectType.AC,
            Object.ObjectType.FILE
        }
        assert types == required_types

    def test_system_prevents_unauthorized_access(
        self,
        user_public,
        object_secret_submarine
    ):
        """
        Business Requirement: System must prevent users from accessing
        objects above their clearance level
        """
        user_labels = set(user_public.accesses.securities.all())
        object_labels = set(object_secret_submarine.security.securities.all())

        # Public user should not have required labels
        assert not object_labels.issubset(user_labels)

    def test_system_allows_authorized_access(
        self,
        user_ts_all,
        all_objects
    ):
        """
        Business Requirement: System must allow users to access objects
        at or below their clearance level with proper compartments
        """
        user_labels = set(user_ts_all.accesses.securities.all())

        for obj in all_objects.values():
            object_labels = set(obj.security.securities.all())
            assert object_labels.issubset(user_labels)

    def test_security_labels_have_two_types(self, all_level_labels, all_category_labels):
        """
        Business Requirement: System must support two types of security labels:
        levels (hierarchical) and categories (compartments)
        """
        # Verify level labels
        for label in all_level_labels.values():
            assert label.label_type == Label.LabelType.LEVEL

        # Verify category labels
        for label in all_category_labels.values():
            assert label.label_type == Label.LabelType.CATEGORY


# ==================== Performance Tests ====================


@pytest.mark.performance
@pytest.mark.slow
class TestPerformance:
    """Performance tests with larger datasets"""

    def test_create_many_labels(self, db, label_factory):
        """Test creating many labels efficiently"""
        labels = []
        for i in range(100):
            label = label_factory(
                short_code=f"L{i:02d}",
                name=f"Label {i}",
                label_type=Label.LabelType.CATEGORY
            )
            labels.append(label)

        assert len(labels) == 100
        assert Label.objects.count() >= 100

    def test_create_many_security_profiles(self, db, label_public, security_factory):
        """Test creating many security profiles"""
        securities = []
        for i in range(50):
            security = security_factory([label_public])
            securities.append(security)

        assert len(securities) == 50
        assert Security.objects.count() >= 50

    def test_create_many_users(self, db, security_public, user_factory):
        """Test creating many users efficiently"""
        users = []
        for i in range(100):
            user = user_factory(f"User {i}", security_public)
            users.append(user)

        assert len(users) == 100
        assert FakeUser.objects.count() >= 100

    def test_create_many_objects(self, db, security_public, object_factory):
        """Test creating many objects efficiently"""
        objects = []
        for i in range(100):
            obj = object_factory(
                f"Obj{i}",
                security_public,
                x_coords=i % 100,
                y_coords=(i * 2) % 100
            )
            objects.append(obj)

        assert len(objects) == 100
        assert Object.objects.count() >= 100

    def test_query_large_label_set(self, db, label_factory):
        """Test querying large set of labels"""
        # Create 50 level labels and 50 category labels
        for i in range(50):
            label_factory(f"LV{i}", f"Level {i}", Label.LabelType.LEVEL)
        for i in range(50):
            label_factory(f"CT{i}", f"Category {i}", Label.LabelType.CATEGORY)

        # Query all level labels
        level_labels = Label.objects.filter(label_type=Label.LabelType.LEVEL)
        assert level_labels.count() == 50

        # Query all category labels
        category_labels = Label.objects.filter(label_type=Label.LabelType.CATEGORY)
        assert category_labels.count() == 50

    def test_complex_security_with_many_labels(
        self,
        db,
        label_factory,
        security_factory
    ):
        """Test security profile with many labels"""
        # Create 20 labels
        labels = [label_factory(f"L{i}", f"Label {i}") for i in range(20)]

        # Add all to one security profile
        security = security_factory(labels)

        assert security.securities.count() == 20

    def test_query_users_by_complex_clearance(
        self,
        db,
        label_factory,
        security_factory,
        user_factory
    ):
        """Test querying users with complex clearances"""
        # Create labels
        label_a = label_factory("LA", "Label A")
        label_b = label_factory("LB", "Label B")
        label_c = label_factory("LC", "Label C")

        # Create security profiles
        sec_ab = security_factory([label_a, label_b])
        sec_bc = security_factory([label_b, label_c])
        sec_abc = security_factory([label_a, label_b, label_c])

        # Create users
        user_ab = user_factory("User AB", sec_ab)
        user_bc = user_factory("User BC", sec_bc)
        user_abc = user_factory("User ABC", sec_abc)

        # Query users with label_b
        users_with_b = FakeUser.objects.filter(
            accesses__securities=label_b
        ).distinct()

        assert users_with_b.count() == 3
        assert user_ab in users_with_b
        assert user_bc in users_with_b
        assert user_abc in users_with_b

    def test_access_control_with_large_dataset(
        self,
        db,
        all_level_labels,
        security_factory,
        user_factory,
        object_factory
    ):
        """Test access control with large number of objects"""
        # Create security at different levels
        sec_public = security_factory([all_level_labels['public']])
        sec_secret = security_factory([
            all_level_labels['public'],
            all_level_labels['internal'],
            all_level_labels['restricted'],
            all_level_labels['confidential'],
            all_level_labels['secret']
        ])

        # Create many objects at different levels
        public_objects = [
            object_factory(f"Public{i}", sec_public) for i in range(30)
        ]
        secret_objects = [
            object_factory(f"Secret{i}", sec_secret) for i in range(20)
        ]

        # Create users
        user_public = user_factory("Public User", sec_public)
        user_secret = user_factory("Secret User", sec_secret)

        # Verify access counts
        user_public_labels = set(user_public.accesses.securities.all())
        user_secret_labels = set(user_secret.accesses.securities.all())

        public_accessible = sum(
            1 for obj in public_objects
            if set(obj.security.securities.all()).issubset(user_public_labels)
        )
        assert public_accessible == 30

        secret_accessible_to_secret_user = sum(
            1 for obj in public_objects + secret_objects
            if set(obj.security.securities.all()).issubset(user_secret_labels)
        )
        assert secret_accessible_to_secret_user == 50


# ==================== Edge Cases and Error Handling ====================


@pytest.mark.unit
class TestEdgeCases:
    """Test edge cases and error handling"""

    def test_security_with_duplicate_labels(self, db, label_public):
        """Test that adding duplicate labels doesn't create duplicates"""
        security = Security.objects.create()
        security.securities.add(label_public)
        security.securities.add(label_public)  # Add same label again

        assert security.securities.count() == 1

    def test_object_at_boundary_coordinates(self, db, security_public, object_factory):
        """Test objects at coordinate boundaries"""
        obj_min = object_factory("Min", security_public, x_coords=0, y_coords=0)
        obj_max = object_factory("Max", security_public, x_coords=100, y_coords=100)

        assert obj_min.x_coords == 0
        assert obj_min.y_coords == 0
        assert obj_max.x_coords == 100
        assert obj_max.y_coords == 100

    def test_label_with_minimum_length_values(self, db):
        """Test label with shortest possible values"""
        label = Label.objects.create(
            short_code="A",
            name="B",
            label_type=Label.LabelType.LEVEL
        )
        assert label.short_code == "A"
        assert label.name == "B"

    def test_user_name_with_special_characters(self, db, security_public):
        """Test user name with special characters"""
        user = FakeUser.objects.create(
            name="Test-User_123 (Special)",
            accesses=security_public
        )
        assert "Test-User_123 (Special)" in user.name

    def test_object_name_with_special_characters(self, db, security_public):
        """Test object name with special characters"""
        obj = Object.objects.create(
            name="USS-123 Test",
            security=security_public
        )
        assert "USS-123 Test" in obj.name

    def test_empty_queryset_operations(self, db):
        """Test operations on empty querysets"""
        assert Label.objects.filter(short_code="NONEXISTENT").count() == 0
        assert not Label.objects.filter(short_code="NONEXISTENT").exists()

    def test_cascading_deletes(self, db, security_public, object_factory):
        """Test cascading delete behavior"""
        obj = object_factory("Test", security_public)
        obj_id = obj.id

        # Deleting security should cascade to object
        security_public.delete()
        assert not Object.objects.filter(id=obj_id).exists()

    def test_security_str_with_only_levels(
        self,
        db,
        label_public,
        label_internal
    ):
        """Test Security __str__ when it only has level labels (no categories)"""
        security = Security.objects.create()
        # Change label types to LEVEL
        label_public.label_type = Label.LabelType.LEVEL
        label_public.save()
        label_internal.label_type = Label.LabelType.LEVEL
        label_internal.save()

        security.securities.add(label_public, label_internal)
        result = str(security)
        # Should return empty or contain no category labels
        assert isinstance(result, str)


# ==================== Parametrized Tests ====================


@pytest.mark.unit
@pytest.mark.parametrize("obj_type,expected", [
    (Object.ObjectType.SHIP, "SHIP"),
    (Object.ObjectType.SUB, "SUB"),
    (Object.ObjectType.AC, "AC"),
    (Object.ObjectType.FILE, "FILE"),
])
class TestObjectTypeParametrized:
    """Parametrized tests for object types"""

    def test_object_type_values(self, obj_type, expected):
        """Test that object type values are correct"""
        assert obj_type == expected

    def test_create_object_with_type(self, db, security_public, obj_type, expected):
        """Test creating objects with each type"""
        obj = Object.objects.create(
            name="Test",
            obj_type=obj_type,
            security=security_public
        )
        assert obj.obj_type == expected


@pytest.mark.unit
@pytest.mark.parametrize("label_type,expected", [
    (Label.LabelType.LEVEL, "LVL"),
    (Label.LabelType.CATEGORY, "CAT"),
])
class TestLabelTypeParametrized:
    """Parametrized tests for label types"""

    def test_label_type_values(self, label_type, expected):
        """Test that label type values are correct"""
        assert label_type == expected

    def test_create_label_with_type(self, db, label_type, expected):
        """Test creating labels with each type"""
        label = Label.objects.create(
            short_code="TST",
            name="Test",
            label_type=label_type
        )
        assert label.label_type == expected


@pytest.mark.functional
@pytest.mark.parametrize("x_coord,y_coord", [
    (0, 0),
    (25, 25),
    (50, 50),
    (75, 75),
    (100, 100),
])
class TestObjectCoordinatesParametrized:
    """Parametrized tests for object coordinates"""

    def test_object_coordinates(self, db, security_public, x_coord, y_coord):
        """Test creating objects at various coordinates"""
        obj = Object.objects.create(
            name="Test",
            x_coords=x_coord,
            y_coords=y_coord,
            security=security_public
        )
        assert obj.x_coords == x_coord
        assert obj.y_coords == y_coord
