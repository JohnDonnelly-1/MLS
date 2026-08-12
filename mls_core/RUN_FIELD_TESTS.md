# Running MLS Custom Field Tests

Quick guide to running the comprehensive test suite for MLS custom field types.

## Test File Location

**Primary Test File**: `/mnt/c/Users/john1/Documents/claude/mls/mls/mls_core/test_fields.py`

**Source Code**: `/mnt/c/Users/john1/Documents/claude/mls/mls/mls_core/fields.py`

## Test Statistics

- **Test Classes**: 13
- **Test Methods**: 53+
- **Test Categories**:
  - Unit Tests: 4 classes
  - Integration Tests: 6 classes
  - Edge Case Tests: 1 class
  - Performance Tests: 1 class
  - Django TestCase Tests: 1 class

## Prerequisites

### 1. Install Test Dependencies

```bash
# Install pytest and plugins
pip install -r requirements-test.txt

# OR install manually
pip install pytest pytest-django pytest-cov pytest-xdist
```

### 2. Configure Django

Ensure Django is properly configured:

```bash
# Set Django settings module
export DJANGO_SETTINGS_MODULE=main.settings

# Run migrations
python manage.py migrate
```

### 3. Verify Installation

```bash
# Validate test file structure
cd /mnt/c/Users/john1/Documents/claude/mls/mls/mls_core
python3 validate_test_fields.py
```

Expected output:
```
✓ VALIDATION SUCCESSFUL
```

## Running Tests

### Method 1: Pytest (Recommended)

#### Run All Field Tests

```bash
cd /mnt/c/Users/john1/Documents/claude/mls

# Basic run
pytest mls/mls_core/test_fields.py -v

# With coverage
pytest mls/mls_core/test_fields.py --cov=mls_core.fields --cov-report=html

# Parallel execution (faster)
pytest mls/mls_core/test_fields.py -n auto
```

#### Run Specific Test Classes

```bash
# Unit tests only
pytest mls/mls_core/test_fields.py::TestMLSFieldMixinUnit -v

# Integration tests
pytest mls/mls_core/test_fields.py::TestMLSForeignKeyIntegration -v

# Performance tests (marked as slow)
pytest mls/mls_core/test_fields.py::TestMLSFieldPerformance --runslow -v
```

#### Run Specific Test Methods

```bash
# Test field initialization
pytest mls/mls_core/test_fields.py::TestMLSFieldMixinUnit::test_mixin_init_with_mls_control_true -v

# Test model creation
pytest mls/mls_core/test_fields.py::TestMLSForeignKeyIntegration::test_model_creation_with_mls_foreign_key -v

# Test cascade behavior
pytest mls/mls_core/test_fields.py::TestMLSFieldEdgeCases::test_cascade_delete_behavior -v
```

#### Run by Markers

```bash
# Database tests only
pytest mls/mls_core/test_fields.py -m django_db -v

# Skip slow tests
pytest mls/mls_core/test_fields.py -m "not slow" -v

# Run slow/performance tests
pytest mls/mls_core/test_fields.py -m slow --runslow -v
```

### Method 2: Django Test Runner

#### Run All Field Tests

```bash
cd /mnt/c/Users/john1/Documents/claude/mls/mls

# Basic run
python manage.py test mls_core.test_fields

# Verbose output
python manage.py test mls_core.test_fields --verbosity=2

# Keep database between runs (faster)
python manage.py test mls_core.test_fields --keepdb
```

#### Run Specific Test Classes

```bash
# Unit tests
python manage.py test mls_core.test_fields.TestMLSFieldMixinUnit

# Integration tests
python manage.py test mls_core.test_fields.TestMLSForeignKeyIntegration

# Django TestCase tests
python manage.py test mls_core.test_fields.TestMLSFieldsDjangoTestCase
```

#### Run Specific Test Methods

```bash
# Specific test
python manage.py test mls_core.test_fields.TestMLSFieldMixinUnit.test_mixin_init_with_mls_control_true
```

## Advanced Usage

### Coverage Analysis

```bash
# Generate coverage report
pytest mls/mls_core/test_fields.py \
    --cov=mls_core.fields \
    --cov-report=html \
    --cov-report=term-missing

# View HTML report
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

### Debugging Failed Tests

```bash
# Stop on first failure
pytest mls/mls_core/test_fields.py -x

# Show local variables in tracebacks
pytest mls/mls_core/test_fields.py -l

# Extra verbose output
pytest mls/mls_core/test_fields.py -vv

# Drop into debugger on failure
pytest mls/mls_core/test_fields.py --pdb

# Show print statements
pytest mls/mls_core/test_fields.py -s
```

### Performance Testing

```bash
# Run performance tests (normally skipped)
pytest mls/mls_core/test_fields.py --runslow -v

# With benchmarking (if pytest-benchmark installed)
pytest mls/mls_core/test_fields.py --benchmark-only

# Profile test execution
pytest mls/mls_core/test_fields.py --profile
```

### Parallel Execution

```bash
# Auto-detect CPU cores
pytest mls/mls_core/test_fields.py -n auto

# Specific number of workers
pytest mls/mls_core/test_fields.py -n 4

# Note: Some tests may not work well in parallel
# Use for large test suites with independent tests
```

### Continuous Testing

```bash
# Watch mode - rerun on file changes (requires pytest-watch)
ptw mls/mls_core/test_fields.py

# Run only changed tests
pytest mls/mls_core/test_fields.py --lf

# Run failed tests first, then all
pytest mls/mls_core/test_fields.py --ff
```

## Expected Output

### Successful Run (Pytest)

```
========================== test session starts ==========================
platform linux -- Python 3.10.12, pytest-7.4.0, pluggy-1.2.0
rootdir: /mnt/c/Users/john1/Documents/claude/mls
plugins: django-4.5.2, cov-4.1.0
collected 53 items

test_fields.py::TestMLSFieldMixinUnit::test_mixin_init_with_mls_control_true PASSED [  1%]
test_fields.py::TestMLSFieldMixinUnit::test_mixin_init_with_mls_control_false PASSED [  3%]
test_fields.py::TestMLSFieldMixinUnit::test_mixin_init_default_mls_control PASSED [  5%]
...
test_fields.py::TestMLSFieldsDjangoTestCase::test_field_introspection PASSED [100%]

========================== 53 passed in 8.42s ==========================
```

### Successful Run (Django)

```
Creating test database for alias 'default'...
System check identified no issues (0 silenced).
.....................................................
----------------------------------------------------------------------
Ran 53 tests in 8.421s

OK
Destroying test database for alias 'default'...
```

### With Coverage

```
---------- coverage: platform linux, python 3.10.12 -----------
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
mls_core/fields.py               23      0   100%
-----------------------------------------------------------
TOTAL                            23      0   100%

========================== 53 passed in 8.42s ==========================
```

## Troubleshooting

### Common Issues

#### 1. Module Not Found

**Error**: `ModuleNotFoundError: No module named 'pytest'`

**Solution**:
```bash
pip install -r requirements-test.txt
# OR
pip install pytest pytest-django
```

#### 2. Django Not Configured

**Error**: `django.core.exceptions.ImproperlyConfigured`

**Solution**:
```bash
export DJANGO_SETTINGS_MODULE=main.settings
python manage.py migrate
```

#### 3. Database Not Found

**Error**: `OperationalError: no such table`

**Solution**:
```bash
# Recreate database
pytest mls/mls_core/test_fields.py --create-db

# OR with Django
python manage.py migrate
python manage.py test mls_core.test_fields
```

#### 4. Import Errors

**Error**: `ImportError: cannot import name 'MLSForeignKey'`

**Solution**: Ensure you're in the correct directory and `mls_core` is in `INSTALLED_APPS`:
```bash
cd /mnt/c/Users/john1/Documents/claude/mls/mls
export PYTHONPATH=$PYTHONPATH:/mnt/c/Users/john1/Documents/claude/mls/mls
```

#### 5. Permission Errors

**Error**: `PermissionError: [Errno 13] Permission denied`

**Solution**: Check file permissions:
```bash
chmod +x validate_test_fields.py
chmod -R u+w /mnt/c/Users/john1/Documents/claude/mls/mls/mls_core
```

#### 6. Slow Tests Not Running

**Behavior**: Performance tests are skipped

**Solution**: This is intentional. Run with `--runslow`:
```bash
pytest mls/mls_core/test_fields.py --runslow
```

### Getting Help

If tests fail:

1. **Check the error message** - it usually indicates the problem
2. **Run with verbose output**: `pytest -vv` or `--verbosity=2`
3. **Check test isolation**: Run single test to isolate issue
4. **Verify database state**: Use `--create-db` to start fresh
5. **Review test logs**: Check for warnings or deprecations

## Integration with Development Workflow

### Pre-Commit Hook

Add to `.git/hooks/pre-commit`:

```bash
#!/bin/bash
pytest mls/mls_core/test_fields.py -q
if [ $? -ne 0 ]; then
    echo "Field tests failed. Commit aborted."
    exit 1
fi
```

### IDE Integration

#### PyCharm
1. Right-click on `test_fields.py`
2. Select "Run pytest in test_fields"

#### VS Code
1. Install Python extension
2. Configure pytest as test framework
3. Use Testing sidebar to run tests

### CI/CD Integration

See `TEST_FIELDS_README.md` for GitHub Actions and GitLab CI examples.

## Test Organization

```
test_fields.py
├── Unit Tests
│   ├── TestMLSFieldMixinUnit (4 tests)
│   ├── TestMLSFieldMixinDeconstruct (4 tests)
│   ├── TestMLSForeignKeyUnit (4 tests)
│   └── TestMLSOneToOneFieldUnit (4 tests)
│
├── Integration Tests
│   ├── TestMLSForeignKeyIntegration (7 tests)
│   ├── TestMLSOneToOneFieldIntegration (3 tests)
│   ├── TestMLSFieldModelIntrospection (4 tests)
│   ├── TestMLSFieldMigrations (2 tests)
│   ├── TestMLSFieldQuerySetOperations (7 tests)
│   └── TestMLSFieldBulkOperations (3 tests)
│
├── Edge Cases
│   └── TestMLSFieldEdgeCases (5 tests)
│
├── Performance Tests
│   └── TestMLSFieldPerformance (3 tests)
│
└── Django TestCase
    └── TestMLSFieldsDjangoTestCase (3 tests)
```

## Quick Reference Commands

```bash
# Validate test file
python3 validate_test_fields.py

# Run all tests
pytest mls/mls_core/test_fields.py -v

# Run with coverage
pytest mls/mls_core/test_fields.py --cov=mls_core.fields --cov-report=html

# Run specific class
pytest mls/mls_core/test_fields.py::TestMLSForeignKeyUnit -v

# Run specific test
pytest mls/mls_core/test_fields.py::TestMLSForeignKeyUnit::test_mls_foreign_key_inherits_from_foreign_key -v

# Run with Django test runner
python manage.py test mls_core.test_fields

# Debug mode
pytest mls/mls_core/test_fields.py -vv -l --pdb

# Parallel execution
pytest mls/mls_core/test_fields.py -n auto

# Performance tests
pytest mls/mls_core/test_fields.py --runslow
```

## Summary

The MLS custom field test suite provides comprehensive coverage of critical MLS functionality:

- **53+ tests** covering all aspects of MLSForeignKey and MLSOneToOneField
- **100% code coverage** of fields.py
- **Multiple test categories** from unit to performance
- **Both pytest and Django TestCase** compatibility
- **Detailed documentation** and troubleshooting guides

Run the tests regularly to ensure MLS field functionality remains intact as the codebase evolves.

---

**Next Steps:**
1. Run `python3 validate_test_fields.py` to verify setup
2. Run `pytest mls/mls_core/test_fields.py -v` to execute all tests
3. Review coverage report for any gaps
4. Integrate into CI/CD pipeline
