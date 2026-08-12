# MLS Metaclass Test Suite Documentation

This directory contains comprehensive tests for the MLS (Multi-Level Security) metaclass system, which is CRITICAL infrastructure that makes MLS work transparently.

## Overview

The `MLSModelBase` metaclass automatically injects MLS behavior into Django models by:

1. Detecting models that need MLS protection via `Meta.mls_protected = True`
2. Detecting fields marked with `mls_control=True`
3. Automatically injecting `MLSManager` as the default manager
4. Preserving explicitly set custom managers

## Test Files

### `test_metaclasses.py`
Comprehensive test suite for the metaclass system with **6 test layers**:

1. **Unit Tests** - Test individual metaclass behaviors in isolation
2. **Integration Tests** - Test metaclass interaction with Django ORM
3. **Functional Tests** - Test complete MLS protection features
4. **End-to-End Tests** - Test complete workflows
5. **Acceptance Tests** - Validate business requirements
6. **Performance Tests** - Ensure metaclass doesn't slow down the system

### `conftest.py`
Shared pytest fixtures including:
- Security labels (all classification levels and categories)
- Security clearances (various combinations)
- Test users with different clearance levels
- Factory fixtures for dynamic test data generation

## Running Tests

### Run All Tests
```bash
# From project root
pytest mls/mls_core/test_metaclasses.py

# Or with verbose output
pytest mls/mls_core/test_metaclasses.py -v
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest mls/mls_core/test_metaclasses.py -m unit

# Integration tests only
pytest mls/mls_core/test_metaclasses.py -m integration

# Skip slow tests
pytest mls/mls_core/test_metaclasses.py -m "not slow"

# E2E and acceptance tests
pytest mls/mls_core/test_metaclasses.py -m "e2e or acceptance"
```

### Run Specific Test Classes
```bash
# Test basic behavior only
pytest mls/mls_core/test_metaclasses.py::TestMLSModelBaseBasicBehavior

# Test manager injection
pytest mls/mls_core/test_metaclasses.py::TestMLSModelBaseManagerInjection

# Test field detection
pytest mls/mls_core/test_metaclasses.py::TestMLSModelBaseFieldDetection
```

### Run Specific Test Methods
```bash
# Test that Meta option triggers injection
pytest mls/mls_core/test_metaclasses.py::TestMLSModelBaseBasicBehavior::test_meta_protected_model_gets_mls_manager

# Test field marker detection
pytest mls/mls_core/test_metaclasses.py::TestMLSModelBaseFieldDetection::test_detects_foreign_key_with_mls_control
```

### Run with Coverage
```bash
# Generate coverage report
pytest mls/mls_core/test_metaclasses.py --cov=mls_core.metaclasses --cov-report=html

# View coverage in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Run Performance Tests
```bash
# Run only performance tests
pytest mls/mls_core/test_metaclasses.py -m performance

# Run performance tests with benchmarking
pytest mls/mls_core/test_metaclasses.py -m performance --benchmark-only
```

### Run in Parallel
```bash
# Run tests in parallel (4 workers)
pytest mls/mls_core/test_metaclasses.py -n 4

# Auto-detect number of CPUs
pytest mls/mls_core/test_metaclasses.py -n auto
```

## Test Structure

### Unit Tests (Layer 1)
```python
class TestMLSModelBaseBasicBehavior(TestCase):
    """Tests for basic metaclass behavior"""

class TestMLSModelBaseManagerInjection(TestCase):
    """Tests for manager injection logic"""

class TestMLSModelBaseAbstractModels(TestCase):
    """Tests for abstract model handling"""

class TestMLSModelBaseFieldDetection(TestCase):
    """Tests for mls_control field detection"""

class TestMLSModelBaseMetaOptions(TestCase):
    """Tests for Meta option detection"""

class TestMLSModelBaseEdgeCases(TestCase):
    """Tests for edge cases"""
```

### Integration Tests (Layer 2)
```python
class TestMLSModelBaseIntegration(TestCase):
    """Tests for metaclass with real model operations"""

class TestMLSModelBaseWithRealSecurityModels(TestCase):
    """Tests using actual SecurityClearance models"""
```

### Functional Tests (Layer 3)
```python
class TestMLSModelBaseTransparency(TestCase):
    """Tests ensuring metaclass works transparently"""

class TestMLSModelBaseDjangoCompatibility(TestCase):
    """Tests ensuring Django compatibility"""
```

### End-to-End Tests (Layer 4)
```python
@pytest.mark.e2e
class TestMLSModelBaseEndToEnd:
    """E2E tests simulating real usage"""
```

### Acceptance Tests (Layer 5)
```python
class TestMLSModelBaseAcceptance(TestCase):
    """Acceptance tests from business perspective"""
```

### Performance Tests (Layer 6)
```python
@pytest.mark.slow
class TestMLSModelBasePerformance(TestCase):
    """Performance tests for metaclass operations"""
```

## Test Coverage

The test suite covers:

### Automatic Manager Injection
- ✅ Models with `Meta.mls_protected = True` get `MLSManager`
- ✅ Models with `mls_control=True` fields get `MLSManager`
- ✅ Models with both Meta option and field marker get `MLSManager`
- ✅ Models without markers keep default `Manager`
- ✅ Explicitly set managers are preserved (when not default `Manager`)

### Field Detection
- ✅ Detection of `MLSForeignKey` with `mls_control=True`
- ✅ Detection of `MLSOneToOneField` with `mls_control=True`
- ✅ Detection of multiple `mls_control` fields
- ✅ Regular ForeignKey fields are ignored

### Meta Option Detection
- ✅ Detection of `Meta.mls_protected = True`
- ✅ Default behavior when option is absent
- ✅ Meta option alone is sufficient for protection

### Abstract Model Handling
- ✅ Abstract models are skipped (no manager injection)
- ✅ Concrete children of abstract models get injection
- ✅ Name-based skipping for `MLSSubject` and `MLSObject`

### Edge Cases
- ✅ Models using metaclass but no MLS markers
- ✅ Multiple inheritance scenarios
- ✅ Manager binding to correct model
- ✅ Separate manager instances per model

### Django Integration
- ✅ Migrations compatibility
- ✅ Django Admin compatibility
- ✅ QuerySet chaining
- ✅ Related queries
- ✅ All standard ORM operations (filter, exclude, order_by, etc.)

### MLS Functionality
- ✅ `accessible_by()` method available
- ✅ `for_current_user()` method available
- ✅ `unfiltered()` method available
- ✅ Methods callable and return correct results

## Test Models

The test suite defines several test models to exercise different scenarios:

- `BasicModel` - No MLS protection (control)
- `MLSProtectedViaMetaOption` - Protected via `Meta.mls_protected`
- `MLSProtectedViaFieldMarker` - Protected via `mls_control=True` field
- `MLSProtectedViaOneToOneField` - Protected via OneToOne field
- `MLSProtectedViaBothMetaAndField` - Both protection methods
- `MLSWithExplicitManager` - Explicitly set custom manager
- `AbstractMLSModel` - Abstract model
- `ConcreteMLSChild` - Concrete child of abstract
- `ModelWithMultipleMLSFields` - Multiple `mls_control` fields
- `ModelWithoutMLSProtection` - Using metaclass but no protection

## Fixtures

### Security Labels
```python
label_unclassified  # Level 1
label_confidential  # Level 2
label_secret        # Level 3
label_top_secret    # Level 4
label_crypto        # Category
label_intel         # Category
label_nato          # Category
```

### Security Clearances
```python
clearance_unclassified      # U only
clearance_confidential      # U, C
clearance_secret            # U, C, S
clearance_top_secret        # U, C, S, TS
clearance_secret_crypto     # U, C, S, CRYPTO
clearance_ts_all_categories # TS + all categories
```

### Test Users
```python
user_unclassified   # Unclassified clearance
user_confidential   # Confidential clearance
user_secret         # Secret clearance
user_top_secret     # Top Secret clearance
user_secret_crypto  # Secret + Crypto
user_ts_all         # TS + all categories
```

### Factories
```python
security_label_factory  # Create labels on demand
clearance_factory       # Create clearances on demand
user_factory            # Create users on demand
```

## Continuous Integration

### GitHub Actions Example
```yaml
name: Test MLS Metaclass

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt

    - name: Run tests with coverage
      run: |
        pytest mls/mls_core/test_metaclasses.py \
          --cov=mls_core.metaclasses \
          --cov-report=xml \
          --cov-fail-under=90

    - name: Upload coverage
      uses: codecov/codecov-action@v3
```

## Expected Coverage

Target coverage: **>90%** for `metaclasses.py`

The test suite provides comprehensive coverage of:
- All code paths in `MLSModelBase.__new__`
- All conditional branches
- All edge cases
- Integration with Django's model system
- Real-world usage scenarios

## Performance Benchmarks

Expected performance characteristics:
- Model instantiation: <10ms for 100 instances
- Manager injection: One-time at class creation (not per instance)
- Bulk operations: No significant overhead vs. regular models

## Troubleshooting

### Tests Fail with "No module named 'mls_core'"
```bash
# Make sure you're running from the project root
cd /mnt/c/Users/john1/Documents/claude/mls

# Or set PYTHONPATH
export PYTHONPATH=/mnt/c/Users/john1/Documents/claude/mls/mls:$PYTHONPATH
```

### Database Errors
```bash
# Create test database
python manage.py migrate --settings=mls.settings

# Or use pytest-django's database creation
pytest --create-db
```

### Import Errors
```bash
# Ensure Django settings are configured
export DJANGO_SETTINGS_MODULE=mls.settings

# Or use pytest.ini configuration (already set)
```

### Slow Tests
```bash
# Skip performance tests
pytest -m "not slow"

# Run in parallel
pytest -n auto
```

## Best Practices

### Writing New Tests
1. Use descriptive test names: `test_<what>_<scenario>_<expected>`
2. One assertion per test (when possible)
3. Use appropriate markers (`@pytest.mark.unit`, etc.)
4. Use fixtures for test data
5. Test both success and failure cases
6. Add docstrings explaining complex scenarios

### Test Organization
1. Group related tests in classes
2. Use setUp/tearDown for common setup
3. Use fixtures for reusable data
4. Keep tests independent (no order dependencies)
5. Use parametrize for similar test cases

### Coverage Goals
1. Aim for >90% line coverage
2. Ensure all branches are tested
3. Test edge cases explicitly
4. Use mutation testing mentally (would test catch bugs?)

## References

- Django Testing: https://docs.djangoproject.com/en/stable/topics/testing/
- Pytest: https://docs.pytest.org/
- Pytest-Django: https://pytest-django.readthedocs.io/
- MLS Core Documentation: (link to main docs)

## Maintainers

When modifying the metaclass (`metaclasses.py`), ensure:
1. All existing tests still pass
2. New behavior has corresponding tests
3. Coverage remains >90%
4. Performance benchmarks don't regress
5. Documentation is updated

## License

Same as main MLS project (MIT)
