# ABAC Models Test Suite Documentation

## Overview

This comprehensive pytest test suite validates all ABAC (Attribute-Based Access Control) models including Label, Security, FakeUser, and Object models. The test suite covers unit tests, integration tests, functional access control scenarios, acceptance tests, and performance tests.

## Test Files

- **test_models.py** - Main test file with 100+ tests covering all ABAC models
- **conftest.py** - Shared fixtures and test configuration

## Test Structure

### Test Categories

1. **Unit Tests** (`@pytest.mark.unit`)
   - Individual model functionality
   - Model creation, validation, and methods
   - String representations
   - Field constraints

2. **Integration Tests** (`@pytest.mark.integration`)
   - Relationships between models
   - Cross-model queries
   - Cascading operations

3. **Functional Tests** (`@pytest.mark.functional`)
   - Real-world access control scenarios
   - Hierarchical clearance verification
   - Compartmentalized access control
   - Need-to-know principle validation

4. **Acceptance Tests** (`@pytest.mark.acceptance`)
   - Business requirement validation
   - System behavior verification
   - Policy enforcement

5. **Performance Tests** (`@pytest.mark.performance` and `@pytest.mark.slow`)
   - Large dataset handling
   - Query performance
   - Bulk operations

## Test Coverage

### Label Model Tests (10 tests)
- Creating level and category labels
- Default values
- String representation
- Field length validation
- Querying by type
- Multiple label support

### Security Model Tests (12 tests)
- Creating security profiles
- Adding/removing labels
- Many-to-many relationships
- String representation with category filtering
- Label sharing across securities
- Clearing labels

### FakeUser Model Tests (10 tests)
- User creation with/without clearances
- One-to-one relationship with Security
- URL generation
- Field validation
- SET_NULL cascade behavior
- Clearance access

### Object Model Tests (17 tests)
- Creating objects of all types (SHIP, SUB, AC, FILE)
- Default values
- Coordinate validation
- One-to-one relationship with Security
- CASCADE delete behavior
- Type-based querying
- Security-based querying

### Integration Tests (10 tests)
- Complete relationship chains
- Shared security profiles
- Cascading deletes
- Complex multi-level relationships
- Cross-relationship queries

### Access Control Functional Tests (12+ tests)
- Hierarchical access control
- Compartmentalized access
- Need-to-know principle
- Multiple simultaneous accesses
- Unauthorized access prevention
- Authorized access validation

### Edge Cases and Error Handling (10 tests)
- Duplicate labels
- Boundary coordinates
- Minimum length values
- Special characters
- Empty querysets
- Cascading behaviors

### Parametrized Tests (18 tests)
- Object type combinations
- Label type combinations
- Coordinate combinations

## Running the Tests

### Prerequisites

Install test dependencies:

```bash
pip install -r requirements-test.txt
```

Required packages:
- pytest>=7.4.0
- pytest-django>=4.5.2
- pytest-cov (optional, for coverage)
- pytest-xdist (optional, for parallel execution)
- pytest-benchmark (optional, for benchmarking)

### Run All Tests

```bash
# From the project root (mls/)
cd /mnt/c/Users/john1/Documents/claude/mls/mls
pytest abac/test_models.py -v
```

### Run Specific Test Categories

```bash
# Run only unit tests
pytest abac/test_models.py -v -m unit

# Run only integration tests
pytest abac/test_models.py -v -m integration

# Run only functional tests
pytest abac/test_models.py -v -m functional

# Run only acceptance tests
pytest abac/test_models.py -v -m acceptance

# Run performance tests (slow)
pytest abac/test_models.py -v -m performance

# Exclude slow tests
pytest abac/test_models.py -v -m "not slow"
```

### Run Specific Test Classes

```bash
# Test only Label model
pytest abac/test_models.py::TestLabelModel -v

# Test only Security model
pytest abac/test_models.py::TestSecurityModel -v

# Test only FakeUser model
pytest abac/test_models.py::TestFakeUserModel -v

# Test only Object model
pytest abac/test_models.py::TestObjectModel -v

# Test access control scenarios
pytest abac/test_models.py::TestAccessControlScenarios -v
```

### Run Individual Tests

```bash
# Run a specific test
pytest abac/test_models.py::TestLabelModel::test_create_level_label -v
```

### Run with Coverage

```bash
# Generate coverage report
pytest abac/test_models.py --cov=abac.models --cov-report=html --cov-report=term-missing

# View coverage report
# Open htmlcov/index.html in a browser
```

### Run Tests in Parallel

```bash
# Run tests in parallel with 4 workers
pytest abac/test_models.py -v -n 4
```

### Run with Verbose Output

```bash
# Show all test output
pytest abac/test_models.py -v -s

# Show only failed tests
pytest abac/test_models.py -v --tb=short

# Show detailed failure info
pytest abac/test_models.py -v --tb=long
```

## Fixtures Available

### Label Fixtures
- `label_public`, `label_internal`, `label_restricted`
- `label_confidential`, `label_secret`, `label_top_secret`
- `label_nato`, `label_crypto`, `label_intel`, `label_nuclear`
- `all_level_labels`, `all_category_labels`

### Security Fixtures
- `security_public`, `security_internal`, `security_restricted`
- `security_confidential`, `security_secret`, `security_top_secret`
- `security_secret_crypto`, `security_ts_all_categories`
- `security_empty`, `all_securities`

### User Fixtures
- `user_public`, `user_internal`, `user_restricted`
- `user_confidential`, `user_secret`, `user_top_secret`
- `user_secret_crypto`, `user_ts_all`
- `user_no_clearance`, `all_users`

### Object Fixtures
- `object_public_ship`, `object_secret_submarine`
- `object_ts_aircraft`, `object_crypto_file`
- `all_objects`

### Factory Fixtures
- `label_factory(short_code, name, label_type)`
- `security_factory(labels)`
- `user_factory(name, security)`
- `object_factory(name, security, obj_type, x_coords, y_coords)`

## Test Scenarios Covered

### Basic Model Operations
- Creating models with required fields
- Default value application
- String representations
- Field validation
- Max length enforcement

### Relationship Testing
- One-to-one relationships (User-Security, Object-Security)
- Many-to-many relationships (Security-Label)
- Reverse relationships
- Cascade behaviors (SET_NULL, CASCADE)

### Access Control Scenarios

#### Hierarchical Access Control
- Public user accessing public objects: ALLOWED
- Public user accessing classified objects: DENIED
- Secret user accessing public objects: ALLOWED
- Secret user accessing secret objects: ALLOWED
- Secret user accessing top secret objects: DENIED
- Top secret user accessing all level objects: ALLOWED

#### Compartmentalized Access Control
- Secret user without crypto accessing crypto objects: DENIED
- Secret + crypto user accessing crypto objects: ALLOWED
- User with NATO compartment accessing crypto objects: DENIED
- Need-to-know principle enforcement

#### Complex Scenarios
- Multiple clearances and compartments
- Mixed level and category requirements
- Simultaneous access by multiple users
- Large dataset access control

### Performance Scenarios
- Creating 100+ labels efficiently
- Creating 50+ security profiles
- Creating 100+ users
- Creating 100+ objects
- Querying large label sets
- Complex security profiles with 20+ labels
- Access control with 50+ objects

## Expected Test Results

All tests should pass. The test suite includes:
- **100+ total tests**
- **10 test classes**
- **Multiple parametrized test variations**
- **Edge case coverage**
- **Performance benchmarks**

## Troubleshooting

### Database Issues

If you encounter database errors:

```bash
# Reset the test database
pytest abac/test_models.py --create-db

# Or use Django's test command
python manage.py test abac.test_models
```

### Import Errors

If you see import errors:

```bash
# Ensure Django settings are configured
export DJANGO_SETTINGS_MODULE=mls.settings

# Or set it in pytest.ini (already configured)
```

### Fixture Errors

If fixtures are not found:
- Ensure `conftest.py` is in the same directory as `test_models.py`
- Check that pytest discovers the conftest file
- Run with `-v` to see fixture loading

## Code Quality Metrics

### Test Coverage Goals
- **Target**: 95%+ coverage for ABAC models
- **Unit tests**: 100% coverage of public methods
- **Integration tests**: All relationships tested
- **Functional tests**: All access control paths tested

### Test Reliability
- All tests are deterministic
- No test interdependencies
- Tests can run in any order
- Database isolation between tests

## Continuous Integration

Add to your CI pipeline:

```yaml
# Example GitHub Actions workflow
- name: Run ABAC Model Tests
  run: |
    pytest mls/abac/test_models.py -v --cov=abac.models --cov-fail-under=90
```

## Extending the Tests

### Adding New Tests

Follow the existing patterns:

```python
@pytest.mark.unit
class TestNewFeature:
    """Unit tests for new feature"""

    def test_new_functionality(self, db, existing_fixture):
        """Test description"""
        # Arrange
        # Act
        # Assert
        pass
```

### Adding New Fixtures

Add to `conftest.py`:

```python
@pytest.fixture
def new_fixture(db, dependency_fixture):
    """Fixture description"""
    return create_object()
```

## Best Practices Followed

1. **Descriptive test names**: `test_<action>_<scenario>_<expected_result>`
2. **One concept per test**: Each test validates one specific behavior
3. **Arrange-Act-Assert pattern**: Clear test structure
4. **Fixture reuse**: DRY principle with shared fixtures
5. **Isolation**: Tests don't depend on each other
6. **Documentation**: Docstrings explain test purpose
7. **Markers**: Tests properly categorized
8. **Performance**: Slow tests marked appropriately

## Related Documentation

- Django Testing: https://docs.djangoproject.com/en/stable/topics/testing/
- Pytest: https://docs.pytest.org/
- Pytest-Django: https://pytest-django.readthedocs.io/

## Support

For issues or questions about the test suite:
1. Check test output for detailed error messages
2. Review fixture definitions in conftest.py
3. Verify database state with `--create-db`
4. Run with `-v -s` for verbose output

## Summary

This comprehensive test suite ensures that the ABAC models work correctly in isolation, integrate properly with each other, and enforce access control policies as required. The tests cover normal operations, edge cases, error conditions, and performance scenarios, providing confidence in the system's reliability and correctness.
