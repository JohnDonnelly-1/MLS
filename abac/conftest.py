"""
Pytest configuration and shared fixtures for ABAC application tests.

This file provides reusable fixtures for testing ABAC models including
FakeUser, Object, Label, and Security models.
"""

import pytest
from abac.models import Label, Security, FakeUser, Object


# ==================== Label Fixtures ====================


@pytest.fixture
def label_public(db):
    """Public level label"""
    return Label.objects.create(
        short_code="PUB",
        name="Public",
        label_type=Label.LabelType.LEVEL
    )


@pytest.fixture
def label_internal(db):
    """Internal level label"""
    return Label.objects.create(
        short_code="INT",
        name="Internal",
        label_type=Label.LabelType.LEVEL
    )


@pytest.fixture
def label_restricted(db):
    """Restricted level label"""
    return Label.objects.create(
        short_code="RES",
        name="Restricted",
        label_type=Label.LabelType.LEVEL
    )


@pytest.fixture
def label_confidential(db):
    """Confidential level label"""
    return Label.objects.create(
        short_code="CNF",
        name="Confidential",
        label_type=Label.LabelType.LEVEL
    )


@pytest.fixture
def label_secret(db):
    """Secret level label"""
    return Label.objects.create(
        short_code="SEC",
        name="Secret",
        label_type=Label.LabelType.LEVEL
    )


@pytest.fixture
def label_top_secret(db):
    """Top Secret level label"""
    return Label.objects.create(
        short_code="TS",
        name="Top Secret",
        label_type=Label.LabelType.LEVEL
    )


# Category Labels


@pytest.fixture
def label_nato(db):
    """NATO category label"""
    return Label.objects.create(
        short_code="NAT",
        name="NATO",
        label_type=Label.LabelType.CATEGORY
    )


@pytest.fixture
def label_crypto(db):
    """Cryptographic category label"""
    return Label.objects.create(
        short_code="CRY",
        name="Crypto",
        label_type=Label.LabelType.CATEGORY
    )


@pytest.fixture
def label_intel(db):
    """Intelligence category label"""
    return Label.objects.create(
        short_code="INT",
        name="Intelligence",
        label_type=Label.LabelType.CATEGORY
    )


@pytest.fixture
def label_nuclear(db):
    """Nuclear category label"""
    return Label.objects.create(
        short_code="NUC",
        name="Nuclear",
        label_type=Label.LabelType.CATEGORY
    )


@pytest.fixture
def all_level_labels(
    db,
    label_public,
    label_internal,
    label_restricted,
    label_confidential,
    label_secret,
    label_top_secret
):
    """All level labels as a dictionary"""
    return {
        'public': label_public,
        'internal': label_internal,
        'restricted': label_restricted,
        'confidential': label_confidential,
        'secret': label_secret,
        'top_secret': label_top_secret,
    }


@pytest.fixture
def all_category_labels(
    db,
    label_nato,
    label_crypto,
    label_intel,
    label_nuclear
):
    """All category labels as a dictionary"""
    return {
        'nato': label_nato,
        'crypto': label_crypto,
        'intel': label_intel,
        'nuclear': label_nuclear,
    }


# ==================== Security Fixtures ====================


@pytest.fixture
def security_public(db, label_public):
    """Public security profile"""
    security = Security.objects.create()
    security.securities.add(label_public)
    return security


@pytest.fixture
def security_internal(db, label_public, label_internal):
    """Internal security profile (includes public)"""
    security = Security.objects.create()
    security.securities.add(label_public, label_internal)
    return security


@pytest.fixture
def security_restricted(db, label_public, label_internal, label_restricted):
    """Restricted security profile (includes lower levels)"""
    security = Security.objects.create()
    security.securities.add(label_public, label_internal, label_restricted)
    return security


@pytest.fixture
def security_confidential(db, all_level_labels):
    """Confidential security profile (includes lower levels)"""
    security = Security.objects.create()
    security.securities.add(
        all_level_labels['public'],
        all_level_labels['internal'],
        all_level_labels['restricted'],
        all_level_labels['confidential']
    )
    return security


@pytest.fixture
def security_secret(db, all_level_labels):
    """Secret security profile (includes lower levels)"""
    security = Security.objects.create()
    security.securities.add(
        all_level_labels['public'],
        all_level_labels['internal'],
        all_level_labels['restricted'],
        all_level_labels['confidential'],
        all_level_labels['secret']
    )
    return security


@pytest.fixture
def security_top_secret(db, all_level_labels):
    """Top Secret security profile (includes all levels)"""
    security = Security.objects.create()
    security.securities.add(*all_level_labels.values())
    return security


@pytest.fixture
def security_secret_crypto(db, all_level_labels, label_crypto):
    """Secret + Crypto category security profile"""
    security = Security.objects.create()
    security.securities.add(
        all_level_labels['public'],
        all_level_labels['internal'],
        all_level_labels['restricted'],
        all_level_labels['confidential'],
        all_level_labels['secret'],
        label_crypto
    )
    return security


@pytest.fixture
def security_ts_all_categories(db, all_level_labels, all_category_labels):
    """Top Secret with all categories"""
    security = Security.objects.create()
    security.securities.add(
        *all_level_labels.values(),
        *all_category_labels.values()
    )
    return security


@pytest.fixture
def security_empty(db):
    """Empty security profile with no labels"""
    return Security.objects.create()


@pytest.fixture
def all_securities(
    db,
    security_public,
    security_internal,
    security_restricted,
    security_confidential,
    security_secret,
    security_top_secret,
    security_secret_crypto,
    security_ts_all_categories
):
    """All security profiles as a dictionary"""
    return {
        'public': security_public,
        'internal': security_internal,
        'restricted': security_restricted,
        'confidential': security_confidential,
        'secret': security_secret,
        'top_secret': security_top_secret,
        'secret_crypto': security_secret_crypto,
        'ts_all': security_ts_all_categories,
    }


# ==================== FakeUser Fixtures ====================


@pytest.fixture
def user_public(db, security_public):
    """User with public clearance"""
    return FakeUser.objects.create(
        name="Public User",
        accesses=security_public
    )


@pytest.fixture
def user_internal(db, security_internal):
    """User with internal clearance"""
    return FakeUser.objects.create(
        name="Internal User",
        accesses=security_internal
    )


@pytest.fixture
def user_restricted(db, security_restricted):
    """User with restricted clearance"""
    return FakeUser.objects.create(
        name="Restricted User",
        accesses=security_restricted
    )


@pytest.fixture
def user_confidential(db, security_confidential):
    """User with confidential clearance"""
    return FakeUser.objects.create(
        name="Confidential User",
        accesses=security_confidential
    )


@pytest.fixture
def user_secret(db, security_secret):
    """User with secret clearance"""
    return FakeUser.objects.create(
        name="Secret User",
        accesses=security_secret
    )


@pytest.fixture
def user_top_secret(db, security_top_secret):
    """User with top secret clearance"""
    return FakeUser.objects.create(
        name="Top Secret User",
        accesses=security_top_secret
    )


@pytest.fixture
def user_secret_crypto(db, security_secret_crypto):
    """User with secret + crypto clearance"""
    return FakeUser.objects.create(
        name="Secret Crypto User",
        accesses=security_secret_crypto
    )


@pytest.fixture
def user_ts_all(db, security_ts_all_categories):
    """User with top secret + all categories clearance"""
    return FakeUser.objects.create(
        name="TS All Access User",
        accesses=security_ts_all_categories
    )


@pytest.fixture
def user_no_clearance(db):
    """User with no clearance"""
    return FakeUser.objects.create(
        name="No Clearance User",
        accesses=None
    )


@pytest.fixture
def all_users(
    db,
    user_public,
    user_internal,
    user_restricted,
    user_confidential,
    user_secret,
    user_top_secret,
    user_secret_crypto,
    user_ts_all
):
    """All users as a dictionary"""
    return {
        'public': user_public,
        'internal': user_internal,
        'restricted': user_restricted,
        'confidential': user_confidential,
        'secret': user_secret,
        'top_secret': user_top_secret,
        'secret_crypto': user_secret_crypto,
        'ts_all': user_ts_all,
    }


# ==================== Object Fixtures ====================


@pytest.fixture
def object_public_ship(db, security_public):
    """Public ship object"""
    return Object.objects.create(
        name="USS Public",
        obj_type=Object.ObjectType.SHIP,
        x_coords=25,
        y_coords=50,
        security=security_public
    )


@pytest.fixture
def object_secret_submarine(db, security_secret):
    """Secret submarine object"""
    return Object.objects.create(
        name="USS Secret Sub",
        obj_type=Object.ObjectType.SUB,
        x_coords=75,
        y_coords=30,
        security=security_secret
    )


@pytest.fixture
def object_ts_aircraft(db, security_top_secret):
    """Top Secret aircraft object"""
    return Object.objects.create(
        name="B-2 Stealth",
        obj_type=Object.ObjectType.AC,
        x_coords=50,
        y_coords=80,
        security=security_top_secret
    )


@pytest.fixture
def object_crypto_file(db, security_secret_crypto):
    """Secret + Crypto file object"""
    return Object.objects.create(
        name="Crypto Keys",
        obj_type=Object.ObjectType.FILE,
        x_coords=10,
        y_coords=10,
        security=security_secret_crypto
    )


@pytest.fixture
def all_objects(
    db,
    object_public_ship,
    object_secret_submarine,
    object_ts_aircraft,
    object_crypto_file
):
    """All objects as a dictionary"""
    return {
        'public_ship': object_public_ship,
        'secret_sub': object_secret_submarine,
        'ts_aircraft': object_ts_aircraft,
        'crypto_file': object_crypto_file,
    }


# ==================== Factory Fixtures ====================


@pytest.fixture
def label_factory(db):
    """Factory for creating labels on demand"""
    def create_label(
        short_code,
        name,
        label_type=Label.LabelType.LEVEL
    ):
        return Label.objects.create(
            short_code=short_code,
            name=name,
            label_type=label_type
        )
    return create_label


@pytest.fixture
def security_factory(db):
    """Factory for creating security profiles on demand"""
    def create_security(labels=None):
        security = Security.objects.create()
        if labels:
            if isinstance(labels, (list, tuple)):
                security.securities.add(*labels)
            else:
                security.securities.add(labels)
        return security
    return create_security


@pytest.fixture
def user_factory(db):
    """Factory for creating FakeUser instances on demand"""
    def create_user(name, security=None):
        return FakeUser.objects.create(
            name=name,
            accesses=security
        )
    return create_user


@pytest.fixture
def object_factory(db):
    """Factory for creating Object instances on demand"""
    def create_object(
        name,
        security,
        obj_type=Object.ObjectType.SHIP,
        x_coords=50,
        y_coords=50
    ):
        return Object.objects.create(
            name=name,
            obj_type=obj_type,
            x_coords=x_coords,
            y_coords=y_coords,
            security=security
        )
    return create_object


# ==================== Pytest Configuration Hooks ====================


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Automatically enable database access for all tests.

    This is a convenience fixture that ensures all tests can access the database
    without explicitly marking them with @pytest.mark.django_db.
    """
    pass
