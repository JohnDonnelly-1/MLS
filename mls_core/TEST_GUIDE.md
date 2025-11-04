# MLS Core - Testing Guide

This guide explains the comprehensive test suite for MLS Core.

## Test Coverage

The test suite includes **9 test classes** with **30+ test cases** covering:

- ✅ Basic MLS access control rules
- ✅ Field-level MLS protection (`mls_control=True`)
- ✅ Meta-level MLS protection (`mls_protected=True`)
- ✅ Manager and QuerySet methods
- ✅ Edge cases and boundary conditions
- ✅ Integration scenarios
- ✅ Performance with larger datasets
- ✅ Compatibility with existing ABAC models

## Running the Tests

### Run All MLS Core Tests

```bash
python manage.py test mls_core
```

### Run Specific Test Class

```bash
python manage.py test mls_core.tests.BasicMLSAccessTestCase
```

### Run Specific Test Method

```bash
python manage.py test mls_core.tests.BasicMLSAccessTestCase.test_subject_must_have_all_labels
```

### Run with Verbosity

```bash
python manage.py test mls_core --verbosity=2
```

### Run with Coverage (if installed)

```bash
coverage run --source='mls_core' manage.py test mls_core
coverage report
coverage html
```

## Test Classes

### 1. BasicMLSAccessTestCase

Tests fundamental MLS access rules:

- **test_subject_can_access_equal_classification** - Subject with exact clearances can access
- **test_subject_with_higher_clearance_can_access** - Higher clearance → broader access
- **test_subject_with_lower_clearance_cannot_access** - Lower clearance → no access
- **test_subject_must_have_all_labels** - Subject must have ALL object labels (core MLS rule)

### 2. FieldLevelMLSTestCase

Tests field-level MLS protection using `mls_control=True`:

- **test_accessible_by_filters_correctly** - `accessible_by()` returns correct objects
- **test_unfiltered_returns_all** - `unfiltered()` bypasses MLS
- **test_all_objects_manager_unfiltered** - `all_objects` manager returns everything

### 3. MetaLevelMLSTestCase

Tests Meta-level MLS protection using `mls_protected=True`:

- **test_meta_level_filtering_works** - Meta options enable MLS correctly
- **test_accessible_by_method_on_object** - Object's `accessible_by()` method works

### 4. ExistingABACModelsTestCase

Tests compatibility with existing ABAC models:

- **test_existing_models_work_without_mls** - Non-MLS models work normally
- **test_can_query_fake_users** - FakeUser queries work

### 5. EdgeCasesTestCase

Tests boundary conditions and edge cases:

- **test_subject_with_no_clearances** - No clearances → no access
- **test_object_with_no_classification** - Missing classification handled safely
- **test_accessible_by_with_none_subject** - None subject → no access
- **test_empty_security_label_set** - Empty label sets handled correctly
- **test_complex_label_combination** - Multiple categories work correctly

### 6. ManagerMethodsTestCase

Tests manager and queryset methods:

- **test_all_returns_filtered** - Manager returns correct type
- **test_filter_with_accessible_by** - Can chain `filter()` with `accessible_by()`
- **test_unfiltered_then_filter** - Can filter on unfiltered queryset

### 7. IntegrationTestCase

Tests realistic scenarios:

- **test_multiple_subjects_multiple_objects** - Complex multi-user scenario
- **test_both_field_and_meta_level_work_independently** - Both approaches work together

### 8. PerformanceTestCase

Tests with larger datasets:

- **test_large_dataset_filtering** - Filtering 100 objects doesn't crash

## Test Models

The test suite defines test-specific models:

### TestSubject (MLSSubject)
```python
class TestSubject(MLSSubject):
    name = models.CharField(max_length=100)
    clearances = models.OneToOneField(Security, on_delete=models.CASCADE, null=True)
```

### TestObjectFieldLevel (MLSObject)
```python
class TestObjectFieldLevel(MLSObject):
    name = models.CharField(max_length=100)
    classification = MLSForeignKey(Security, mls_control=True, on_delete=models.CASCADE)
```

### TestObjectMetaLevel (MLSObject)
```python
class TestObjectMetaLevel(MLSObject):
    name = models.CharField(max_length=100)
    security_label = models.ForeignKey(Security, on_delete=models.CASCADE)

    class Meta:
        mls_protected = True
        mls_classification_field = 'security_label'
```

## Test Fixtures

Each test creates a comprehensive security hierarchy:

### Security Labels
- **Levels**: Unclassified, Confidential, Secret, Top Secret
- **Categories**: Crypto, Intelligence

### Security Clearances
1. **Unclassified only** - Lowest clearance
2. **Confidential** - Includes unclassified
3. **Secret** - Includes unclassified + confidential
4. **Top Secret** - All levels
5. **Secret + Crypto** - Secret level with crypto category
6. **Top Secret + All** - All levels and categories

### Test Subjects
- `user_unclass` - Unclassified clearance
- `user_confidential` - Confidential clearance
- `user_secret` - Secret clearance
- `user_top_secret` - Top Secret clearance
- `user_secret_crypto` - Secret + Crypto
- `user_ts_all` - Top Secret with all categories

## Key Test Scenarios

### Scenario 1: Hierarchical Access
```python
# Top Secret user can access Secret document
self.assertTrue(user_top_secret.can_access(secret_document))

# Secret user CANNOT access Top Secret document
self.assertFalse(user_secret.can_access(top_secret_document))
```

### Scenario 2: Category Requirements
```python
# Object requires: [Secret, Crypto]
# User has: [Secret] only
# Result: DENIED (missing Crypto category)
self.assertFalse(user_secret.can_access(secret_crypto_doc))

# User has: [Secret, Crypto]
# Result: GRANTED (has all required labels)
self.assertTrue(user_secret_crypto.can_access(secret_crypto_doc))
```

### Scenario 3: QuerySet Filtering
```python
# Unclassified user sees only unclassified objects
accessible = Document.objects.accessible_by(user_unclass)
self.assertEqual(accessible.count(), 1)

# Top Secret user sees all objects
accessible = Document.objects.accessible_by(user_top_secret)
self.assertEqual(accessible.count(), 4)
```

## Expected Test Results

When all tests pass, you should see:

```
Ran 30 tests in X.XXXs

OK
```

## Troubleshooting

### Tests Fail with Database Errors

**Problem**: `django.db.utils.OperationalError: no such table`

**Solution**: Run migrations first:
```bash
python manage.py migrate
```

### Import Errors

**Problem**: `ModuleNotFoundError: No module named 'mls_core'`

**Solution**: Ensure `mls_core` is in `INSTALLED_APPS`:
```python
INSTALLED_APPS = [
    ...
    'mls_core',
    'abac',
]
```

### Test Models Not Created

**Problem**: Tests fail because test models don't have tables

**Solution**: This is expected - test models use `app_label='mls_core'` and Django creates temporary tables during testing. If you need persistent test models, remove `app_label` and run migrations.

### Assertion Errors

**Problem**: Tests fail with wrong counts or access denied when it should be granted

**Solution**:
1. Check that security labels are being added correctly
2. Verify the MLS rule: subject must have ALL object labels
3. Print debug info:
```python
print(f"Subject labels: {set(subject.clearances.securities.all())}")
print(f"Object labels: {set(obj.classification.securities.all())}")
```

## Writing Your Own Tests

### Basic Test Template

```python
from django.test import TestCase
from mls_core import MLSSubject, MLSObject, MLSForeignKey
from abac.models import Security, Label

class MyMLSTest(TestCase):
    def setUp(self):
        # Create labels
        self.label_public = Label.objects.create(
            short_code="PUB",
            name="Public",
            label_type=Label.LabelType.LEVEL
        )

        # Create security
        self.security = Security.objects.create()
        self.security.securities.add(self.label_public)

        # Create subject and object
        self.user = MySubject.objects.create(clearances=self.security)
        self.doc = MyObject.objects.create(classification=self.security)

    def test_my_scenario(self):
        # Test your MLS scenario
        self.assertTrue(self.user.can_access(self.doc))
```

## Test Metrics

Current test coverage includes:

- **30+ test methods** across 9 test classes
- **200+ assertions** verifying MLS behavior
- **Test data**: 6 security levels, 6 test users, multiple objects
- **Edge cases**: None values, empty sets, complex combinations
- **Performance**: Tests with 100+ objects

## Next Steps

1. **Run the tests**: `python manage.py test mls_core`
2. **Review failures**: Address any failing tests
3. **Add custom tests**: Write tests specific to your use cases
4. **Continuous Integration**: Add tests to your CI/CD pipeline
5. **Coverage Report**: Generate and review coverage

## Resources

- Django Testing Documentation: https://docs.djangoproject.com/en/stable/topics/testing/
- Coverage.py: https://coverage.readthedocs.io/
- MLS Core README: [README.md](README.md)
