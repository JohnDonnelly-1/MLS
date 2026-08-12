"""
Pytest configuration and shared fixtures for MLS Core tests.

This file provides reusable fixtures for testing the MLS system,
including security labels, clearances, and test subjects/objects.
"""

import pytest
from django.contrib.auth.models import User

from mls_core.models import (
    SecurityLabel,
    SecurityClearance,
    SecurityProfile,
    MLSGroup,
    DACGroup,
)


# ==================== Security Label Fixtures ====================


@pytest.fixture
def label_unclassified(db):
    """Unclassified security label (Level 1)"""
    return SecurityLabel.objects.create(
        short_code="U",
        name="Unclassified",
        label_type=SecurityLabel.LabelType.LEVEL,
        rank=1,
        description="Public information",
        color="#00FF00"
    )


@pytest.fixture
def label_confidential(db):
    """Confidential security label (Level 2)"""
    return SecurityLabel.objects.create(
        short_code="C",
        name="Confidential",
        label_type=SecurityLabel.LabelType.LEVEL,
        rank=2,
        description="Sensitive information",
        color="#FFFF00"
    )


@pytest.fixture
def label_secret(db):
    """Secret security label (Level 3)"""
    return SecurityLabel.objects.create(
        short_code="S",
        name="Secret",
        label_type=SecurityLabel.LabelType.LEVEL,
        rank=3,
        description="Classified information",
        color="#FFA500"
    )


@pytest.fixture
def label_top_secret(db):
    """Top Secret security label (Level 4)"""
    return SecurityLabel.objects.create(
        short_code="TS",
        name="Top Secret",
        label_type=SecurityLabel.LabelType.LEVEL,
        rank=4,
        description="Highly classified information",
        color="#FF0000"
    )


@pytest.fixture
def label_crypto(db):
    """Crypto category label"""
    return SecurityLabel.objects.create(
        short_code="CRYPTO",
        name="Cryptographic",
        label_type=SecurityLabel.LabelType.CATEGORY,
        rank=0,
        description="Cryptographic materials",
        color="#0000FF"
    )


@pytest.fixture
def label_intel(db):
    """Intelligence category label"""
    return SecurityLabel.objects.create(
        short_code="INTEL",
        name="Intelligence",
        label_type=SecurityLabel.LabelType.CATEGORY,
        rank=0,
        description="Intelligence information",
        color="#800080"
    )


@pytest.fixture
def label_nato(db):
    """NATO category label"""
    return SecurityLabel.objects.create(
        short_code="NATO",
        name="NATO",
        label_type=SecurityLabel.LabelType.CATEGORY,
        rank=0,
        description="NATO alliance information",
        color="#000080"
    )


@pytest.fixture
def all_level_labels(db, label_unclassified, label_confidential, label_secret, label_top_secret):
    """All level labels as a dict"""
    return {
        'unclassified': label_unclassified,
        'confidential': label_confidential,
        'secret': label_secret,
        'top_secret': label_top_secret,
    }


@pytest.fixture
def all_category_labels(db, label_crypto, label_intel, label_nato):
    """All category labels as a dict"""
    return {
        'crypto': label_crypto,
        'intel': label_intel,
        'nato': label_nato,
    }


# ==================== Security Clearance Fixtures ====================


@pytest.fixture
def clearance_unclassified(db, label_unclassified):
    """Unclassified clearance"""
    clearance = SecurityClearance.objects.create(
        name="Unclassified Only",
        description="Public access only"
    )
    clearance.securities.add(label_unclassified)
    return clearance


@pytest.fixture
def clearance_confidential(db, label_unclassified, label_confidential):
    """Confidential clearance (includes unclassified)"""
    clearance = SecurityClearance.objects.create(
        name="Confidential Clearance",
        description="Access to confidential and below"
    )
    clearance.securities.add(label_unclassified, label_confidential)
    return clearance


@pytest.fixture
def clearance_secret(db, label_unclassified, label_confidential, label_secret):
    """Secret clearance (includes lower levels)"""
    clearance = SecurityClearance.objects.create(
        name="Secret Clearance",
        description="Access to secret and below"
    )
    clearance.securities.add(label_unclassified, label_confidential, label_secret)
    return clearance


@pytest.fixture
def clearance_top_secret(db, all_level_labels):
    """Top Secret clearance (includes all levels)"""
    clearance = SecurityClearance.objects.create(
        name="Top Secret Clearance",
        description="Access to all classification levels"
    )
    clearance.securities.add(*all_level_labels.values())
    return clearance


@pytest.fixture
def clearance_secret_crypto(db, label_unclassified, label_confidential, label_secret, label_crypto):
    """Secret clearance with Crypto category"""
    clearance = SecurityClearance.objects.create(
        name="Secret + Crypto",
        description="Secret clearance with crypto compartment"
    )
    clearance.securities.add(
        label_unclassified,
        label_confidential,
        label_secret,
        label_crypto
    )
    return clearance


@pytest.fixture
def clearance_ts_all_categories(db, all_level_labels, all_category_labels):
    """Top Secret with all categories"""
    clearance = SecurityClearance.objects.create(
        name="TS All Access",
        description="Top Secret with all compartments"
    )
    clearance.securities.add(*all_level_labels.values(), *all_category_labels.values())
    return clearance


@pytest.fixture
def all_clearances(
    db,
    clearance_unclassified,
    clearance_confidential,
    clearance_secret,
    clearance_top_secret,
    clearance_secret_crypto,
    clearance_ts_all_categories
):
    """All clearances as a dict"""
    return {
        'unclassified': clearance_unclassified,
        'confidential': clearance_confidential,
        'secret': clearance_secret,
        'top_secret': clearance_top_secret,
        'secret_crypto': clearance_secret_crypto,
        'ts_all': clearance_ts_all_categories,
    }


# ==================== User and Profile Fixtures ====================


@pytest.fixture
def django_user(db):
    """Basic Django user without security profile"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='testpass123'
    )


@pytest.fixture
def user_unclassified(db, django_user, clearance_unclassified):
    """User with unclassified clearance"""
    user = User.objects.create_user(
        username='user_unclass',
        email='unclass@example.com',
        password='testpass123'
    )
    profile = SecurityProfile.objects.create(
        user=user,
        clearances=clearance_unclassified,
        is_active=True
    )
    return user


@pytest.fixture
def user_confidential(db, clearance_confidential):
    """User with confidential clearance"""
    user = User.objects.create_user(
        username='user_conf',
        email='conf@example.com',
        password='testpass123'
    )
    profile = SecurityProfile.objects.create(
        user=user,
        clearances=clearance_confidential,
        is_active=True
    )
    return user


@pytest.fixture
def user_secret(db, clearance_secret):
    """User with secret clearance"""
    user = User.objects.create_user(
        username='user_secret',
        email='secret@example.com',
        password='testpass123'
    )
    profile = SecurityProfile.objects.create(
        user=user,
        clearances=clearance_secret,
        is_active=True
    )
    return user


@pytest.fixture
def user_top_secret(db, clearance_top_secret):
    """User with top secret clearance"""
    user = User.objects.create_user(
        username='user_ts',
        email='ts@example.com',
        password='testpass123'
    )
    profile = SecurityProfile.objects.create(
        user=user,
        clearances=clearance_top_secret,
        is_active=True
    )
    return user


@pytest.fixture
def user_secret_crypto(db, clearance_secret_crypto):
    """User with secret + crypto clearance"""
    user = User.objects.create_user(
        username='user_sec_crypto',
        email='crypto@example.com',
        password='testpass123'
    )
    profile = SecurityProfile.objects.create(
        user=user,
        clearances=clearance_secret_crypto,
        is_active=True
    )
    return user


@pytest.fixture
def user_ts_all(db, clearance_ts_all_categories):
    """User with top secret + all categories"""
    user = User.objects.create_user(
        username='user_ts_all',
        email='tsall@example.com',
        password='testpass123'
    )
    profile = SecurityProfile.objects.create(
        user=user,
        clearances=clearance_ts_all_categories,
        is_active=True
    )
    return user


@pytest.fixture
def all_users(
    db,
    user_unclassified,
    user_confidential,
    user_secret,
    user_top_secret,
    user_secret_crypto,
    user_ts_all
):
    """All test users as a dict"""
    return {
        'unclassified': user_unclassified,
        'confidential': user_confidential,
        'secret': user_secret,
        'top_secret': user_top_secret,
        'secret_crypto': user_secret_crypto,
        'ts_all': user_ts_all,
    }


# ==================== MLS Group Fixtures ====================


@pytest.fixture
def mls_group_secret(db, clearance_secret):
    """MLS group granting secret clearance"""
    return MLSGroup.objects.create(
        name="Secret Personnel",
        description="Personnel with secret clearance",
        clearance_template=clearance_secret,
        is_active=True
    )


@pytest.fixture
def mls_group_crypto(db, label_crypto):
    """MLS group for crypto compartment"""
    clearance = SecurityClearance.objects.create(name="Crypto Compartment")
    clearance.securities.add(label_crypto)

    return MLSGroup.objects.create(
        name="Crypto Access",
        description="Access to cryptographic materials",
        clearance_template=clearance,
        is_active=True
    )


# ==================== DAC Group Fixtures ====================


@pytest.fixture
def dac_group_engineering(db):
    """DAC group for engineering team"""
    return DACGroup.objects.create(
        name="Engineering",
        description="Engineering department",
        is_active=True
    )


@pytest.fixture
def dac_group_management(db):
    """DAC group for management"""
    return DACGroup.objects.create(
        name="Management",
        description="Management team",
        is_active=True
    )


# ==================== Utility Fixtures ====================


@pytest.fixture
def security_labels(all_level_labels, all_category_labels):
    """Combined fixture with all labels"""
    return {**all_level_labels, **all_category_labels}


@pytest.fixture
def clearances(all_clearances):
    """Alias for all_clearances"""
    return all_clearances


@pytest.fixture
def users(all_users):
    """Alias for all_users"""
    return all_users


# ==================== Pytest Configuration Hooks ====================


def pytest_configure(config):
    """Configure pytest for Django testing"""
    # Add custom markers
    config.addinivalue_line(
        "markers", "unit: Unit tests for individual components"
    )
    config.addinivalue_line(
        "markers", "integration: Integration tests for component interaction"
    )
    config.addinivalue_line(
        "markers", "functional: Functional tests for complete features"
    )
    config.addinivalue_line(
        "markers", "e2e: End-to-end tests for complete workflows"
    )
    config.addinivalue_line(
        "markers", "acceptance: Acceptance tests for business requirements"
    )
    config.addinivalue_line(
        "markers", "performance: Performance and benchmark tests"
    )


@pytest.fixture(autouse=True)
def enable_db_access_for_all_tests(db):
    """
    Automatically enable database access for all tests.

    This is a convenience fixture that ensures all tests can access the database
    without explicitly marking them with @pytest.mark.django_db.

    Remove this if you prefer explicit database access marking.
    """
    pass


# ==================== Factory Fixtures ====================


@pytest.fixture
def security_label_factory(db):
    """Factory for creating security labels on demand"""
    def create_label(short_code, name, label_type=SecurityLabel.LabelType.LEVEL, rank=0):
        return SecurityLabel.objects.create(
            short_code=short_code,
            name=name,
            label_type=label_type,
            rank=rank
        )
    return create_label


@pytest.fixture
def clearance_factory(db):
    """Factory for creating clearances on demand"""
    def create_clearance(name, labels=None):
        clearance = SecurityClearance.objects.create(name=name)
        if labels:
            clearance.securities.add(*labels)
        return clearance
    return create_clearance


@pytest.fixture
def user_factory(db):
    """Factory for creating users with security profiles"""
    def create_user(username, clearance=None, **kwargs):
        user = User.objects.create_user(
            username=username,
            email=f"{username}@example.com",
            password='testpass123',
            **kwargs
        )
        if clearance:
            SecurityProfile.objects.create(
                user=user,
                clearances=clearance,
                is_active=True
            )
        return user
    return create_user
