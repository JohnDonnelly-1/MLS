# ABAC Test Suite - Quick Start Guide

## Files Created

1. **test_models.py** - Main test file (46 KB, 96 tests, 13 test classes)
2. **conftest.py** - Test fixtures (13 KB, 42 fixtures)
3. **TEST_README.md** - Complete documentation
4. **TEST_SUITE_SUMMARY.md** - Detailed summary
5. **run_tests.sh** - Test runner script
6. **QUICK_START.md** - This file

## Installation

```bash
# Install test dependencies
pip install -r requirements-test.txt
```

## Running Tests

### Using the Test Runner (Easiest)

```bash
cd /mnt/c/Users/john1/Documents/claude/mls/mls

# Run all tests
./abac/run_tests.sh

# Run specific categories
./abac/run_tests.sh unit          # Unit tests only
./abac/run_tests.sh integration   # Integration tests
./abac/run_tests.sh functional    # Functional tests
./abac/run_tests.sh fast          # Skip slow tests

# Run specific models
./abac/run_tests.sh label         # Label model tests
./abac/run_tests.sh security      # Security model tests
./abac/run_tests.sh user          # FakeUser model tests
./abac/run_tests.sh object        # Object model tests
./abac/run_tests.sh access        # Access control tests

# Run with coverage
./abac/run_tests.sh coverage

# Get help
./abac/run_tests.sh help
```

### Using pytest Directly

```bash
cd /mnt/c/Users/john1/Documents/claude/mls/mls

# Run all tests
pytest abac/test_models.py -v

# Run by marker
pytest abac/test_models.py -v -m unit
pytest abac/test_models.py -v -m integration
pytest abac/test_models.py -v -m functional
pytest abac/test_models.py -v -m acceptance
pytest abac/test_models.py -v -m performance

# Run specific test class
pytest abac/test_models.py::TestLabelModel -v
pytest abac/test_models.py::TestSecurityModel -v
pytest abac/test_models.py::TestFakeUserModel -v
pytest abac/test_models.py::TestObjectModel -v

# Run specific test
pytest abac/test_models.py::TestLabelModel::test_create_level_label -v

# Run with coverage
pytest abac/test_models.py --cov=abac.models --cov-report=term-missing
```

## Test Coverage

### Models Tested
- **Label** - Security labels (levels and categories)
- **Security** - Security profiles with multiple labels
- **FakeUser** - Users with security clearances
- **Object** - Protected objects (ships, submarines, aircraft, files)

### Test Categories
- **96 test functions** across **13 test classes**
- **42 reusable fixtures** in conftest.py

#### Breakdown
- Unit Tests: 59 tests
- Integration Tests: 10 tests
- Functional Tests: 15 tests
- Acceptance Tests: 7 tests
- Performance Tests: 8 tests
- Parametrized Tests: 18 variations

## Key Test Classes

| Test Class | Tests | Focus |
|------------|-------|-------|
| TestLabelModel | 10 | Label creation, types, validation |
| TestSecurityModel | 12 | Security profiles, label management |
| TestFakeUserModel | 10 | User creation, clearances, URLs |
| TestObjectModel | 17 | Object creation, types, coordinates |
| TestModelRelationships | 10 | Model integration, cascades |
| TestAccessControlScenarios | 12 | Real-world access control |
| TestObjectCoordinatesAndTypes | 3 | Object positioning, types |
| TestBusinessRequirements | 7 | Business rule validation |
| TestPerformance | 8 | Large dataset handling |
| TestEdgeCases | 10 | Edge cases, error handling |
| + 3 Parametrized Classes | 18 | Data-driven tests |

## Common Test Scenarios

### Access Control Testing
```python
# Verify hierarchical access
- Public user → Public objects ✓
- Public user → Secret objects ✗
- Secret user → Public objects ✓
- Secret user → Secret objects ✓
- Top Secret user → All level objects ✓

# Verify compartmentalized access
- Secret user → Crypto objects ✗ (needs crypto clearance)
- Secret+Crypto user → Crypto objects ✓
```

### Relationship Testing
```python
# Test complete chains
Label → Security → User
Label → Security → Object

# Test cascading deletes
Delete Security → User.accesses = NULL (SET_NULL)
Delete Security → Object deleted (CASCADE)
```

## Available Fixtures

### Quick Access
```python
# Labels
label_public, label_secret, label_top_secret
label_crypto, label_intel, label_nato
all_level_labels, all_category_labels

# Security Profiles
security_public, security_secret, security_top_secret
security_secret_crypto, security_ts_all_categories
all_securities

# Users
user_public, user_secret, user_top_secret
user_secret_crypto, user_ts_all
all_users

# Objects
object_public_ship, object_secret_submarine
object_ts_aircraft, object_crypto_file
all_objects

# Factories
label_factory, security_factory
user_factory, object_factory
```

## Troubleshooting

### Tests Not Running
```bash
# Ensure you're in the correct directory
cd /mnt/c/Users/john1/Documents/claude/mls/mls

# Check pytest is installed
pytest --version

# Install dependencies if needed
pip install -r requirements-test.txt
```

### Database Errors
```bash
# Reset test database
pytest abac/test_models.py --create-db
```

### Import Errors
```bash
# Set Django settings
export DJANGO_SETTINGS_MODULE=mls.settings
```

## Next Steps

1. **Run the tests**: `./abac/run_tests.sh`
2. **Check coverage**: `./abac/run_tests.sh coverage`
3. **Read full docs**: See TEST_README.md
4. **View summary**: See TEST_SUITE_SUMMARY.md

## Example Output

```
================================ test session starts =================================
collected 96 items

abac/test_models.py::TestLabelModel::test_create_level_label PASSED          [  1%]
abac/test_models.py::TestLabelModel::test_create_category_label PASSED       [  2%]
...
abac/test_models.py::TestAccessControlScenarios::test_top_secret_user_can_access_all_level_objects PASSED [95%]
abac/test_models.py::TestPerformance::test_create_many_objects PASSED       [100%]

================================ 96 passed in 12.34s =================================
```

## CI/CD Integration

```yaml
# GitHub Actions example
- name: Run ABAC Tests
  run: |
    cd mls
    pip install -r ../requirements-test.txt
    pytest abac/test_models.py -v --cov=abac.models
```

## Documentation Files

- **QUICK_START.md** (this file) - Quick reference
- **TEST_README.md** - Complete documentation
- **TEST_SUITE_SUMMARY.md** - Detailed summary with statistics

## Support

Run `./abac/run_tests.sh help` for all available options.

For detailed information, see TEST_README.md.

---

**Quick Start Version**: 1.0
**Last Updated**: 2025-11-25
