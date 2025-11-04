# Running MLS Core Tests

Quick reference for running the MLS Core test suite.

## Prerequisites

1. Ensure Django environment is set up
2. Make sure `mls_core` is in `INSTALLED_APPS`
3. Run migrations: `python manage.py migrate`

## Quick Start

```bash
# Run all MLS Core tests
python manage.py test mls_core

# Expected output:
# ----------------------------------------------------------------------
# Ran 30 tests in X.XXXs
#
# OK
```

## Common Test Commands

```bash
# Run all tests
python manage.py test mls_core

# Run with verbose output
python manage.py test mls_core --verbosity=2

# Run specific test class
python manage.py test mls_core.tests.BasicMLSAccessTestCase

# Run specific test method
python manage.py test mls_core.tests.BasicMLSAccessTestCase.test_subject_must_have_all_labels

# Run with keep database (faster for repeated runs)
python manage.py test mls_core --keepdb

# Run all tests in the project
python manage.py test
```

## Test Classes

| Test Class | Tests | Focus |
|------------|-------|-------|
| `BasicMLSAccessTestCase` | 4 | Fundamental MLS rules |
| `FieldLevelMLSTestCase` | 3 | Field-level protection |
| `MetaLevelMLSTestCase` | 2 | Meta-level protection |
| `ExistingABACModelsTestCase` | 2 | ABAC compatibility |
| `EdgeCasesTestCase` | 5 | Boundary conditions |
| `ManagerMethodsTestCase` | 3 | Manager methods |
| `IntegrationTestCase` | 2 | Realistic scenarios |
| `PerformanceTestCase` | 1 | Large datasets |

## Test Coverage

The test suite covers:

✅ **Core MLS Rule**: Subject must have ALL object labels
✅ **Field-Level MLS**: Using `mls_control=True` parameter
✅ **Meta-Level MLS**: Using `mls_protected=True` in Meta
✅ **Manager Methods**: `accessible_by()`, `unfiltered()`, etc.
✅ **QuerySet Filtering**: Automatic and explicit filtering
✅ **Edge Cases**: None values, empty sets, complex combinations
✅ **Integration**: Multiple users with multiple objects
✅ **Performance**: 100+ objects

## Understanding Test Results

### All Passed ✅
```
----------------------------------------------------------------------
Ran 30 tests in 2.450s

OK
```
All tests passed! MLS Core is working correctly.

### Some Failed ❌
```
======================================================================
FAIL: test_subject_must_have_all_labels (mls_core.tests.BasicMLSAccessTestCase)
----------------------------------------------------------------------
AssertionError: False is not true
```
Check the test output for details. Common issues:
- Database not migrated
- Incorrect label configuration
- Logic error in MLS implementation

### Test Errors ⚠️
```
======================================================================
ERROR: test_accessible_by_filters_correctly (mls_core.tests.FieldLevelMLSTestCase)
----------------------------------------------------------------------
ImportError: No module named 'mls_core'
```
Configuration issue. Check:
- Is `mls_core` in `INSTALLED_APPS`?
- Are you in the correct directory?
- Is the virtual environment activated?

## Debugging Failed Tests

### Add Print Statements
```python
def test_my_scenario(self):
    print(f"User clearances: {self.user.clearances.securities.all()}")
    print(f"Object classification: {self.obj.classification.securities.all()}")
    accessible = Object.objects.accessible_by(self.user)
    print(f"Accessible count: {accessible.count()}")
    self.assertTrue(self.user.can_access(self.obj))
```

### Run Single Test with Output
```bash
python manage.py test mls_core.tests.BasicMLSAccessTestCase.test_subject_must_have_all_labels --verbosity=2
```

### Use Django Shell
```bash
python manage.py shell

>>> from abac.models import Label, Security
>>> from mls_core import MLSSubject, MLSObject
>>> # Test your scenario interactively
```

## CI/CD Integration

### GitHub Actions Example
```yaml
name: Run Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - run: pip install -r requirements.txt
      - run: python manage.py migrate
      - run: python manage.py test mls_core
```

### GitLab CI Example
```yaml
test:
  script:
    - pip install -r requirements.txt
    - python manage.py migrate
    - python manage.py test mls_core
```

## Coverage Report

Install coverage:
```bash
pip install coverage
```

Run with coverage:
```bash
coverage run --source='mls_core' manage.py test mls_core
coverage report
```

Generate HTML report:
```bash
coverage html
# Open htmlcov/index.html in browser
```

## Performance Testing

Run performance test specifically:
```bash
python manage.py test mls_core.tests.PerformanceTestCase.test_large_dataset_filtering
```

This test creates 100 objects and verifies filtering works correctly at scale.

## Next Steps

After tests pass:

1. ✅ **Review TEST_GUIDE.md** - Detailed test documentation
2. ✅ **Read README.md** - Full MLS Core documentation
3. ✅ **Check EXAMPLES.md** - Usage examples
4. ✅ **Try QUICKSTART.md** - Get started in 5 minutes

## Need Help?

- Check test output for specific error messages
- Review the TEST_GUIDE.md for detailed test documentation
- Examine test code in `mls_core/tests.py` for examples
- Ensure all prerequisites are met (migrations, settings, etc.)

## Summary

The MLS Core test suite provides comprehensive coverage of all functionality:

- **30+ tests** ensuring MLS rules are enforced correctly
- **Both field-level and meta-level** protection tested
- **Edge cases covered** for robust security
- **Integration tests** for realistic scenarios
- **Performance validated** with larger datasets

Run `python manage.py test mls_core` to verify everything works! 🚀
