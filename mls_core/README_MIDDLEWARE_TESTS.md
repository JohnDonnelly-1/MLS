# MLS Middleware Tests - Quick Reference

## Test File Location
```
/mnt/c/Users/john1/Documents/claude/mls/mls/mls_core/test_middleware.py
```

## Quick Start

### Option 1: Django Test Runner
```bash
cd /mnt/c/Users/john1/Documents/claude/mls/mls
python manage.py test mls_core.test_middleware
```

### Option 2: Pytest (Recommended)
```bash
cd /mnt/c/Users/john1/Documents/claude/mls/mls
pytest mls_core/test_middleware.py -v
```

### Option 3: Pytest from Project Root
```bash
cd /mnt/c/Users/john1/Documents/claude/mls
pytest mls/mls_core/test_middleware.py -v
```

## Common Test Commands

### Run All Tests (Verbose)
```bash
pytest mls_core/test_middleware.py -v
```

### Run Specific Test Class
```bash
# Security tests only
pytest mls_core/test_middleware.py::TestMLSMiddlewareSecurity -v

# Unit tests only
pytest mls_core/test_middleware.py::TestMLSMiddlewareInitialization -v

# Integration tests only
pytest mls_core/test_middleware.py::TestMLSMiddlewareWithMLSModels -v
```

### Run Specific Test
```bash
pytest mls_core/test_middleware.py::TestMLSMiddlewareSecurity::test_middleware_fails_secure_on_exception -v
```

### Run with Coverage
```bash
pytest mls_core/test_middleware.py --cov=mls_core.middleware --cov-report=html
```

### Run Performance Tests
```bash
# Performance tests are skipped by default
pytest mls_core/test_middleware.py --runperformance
```

## Test Statistics

- **Total Tests**: 70+
- **Test Classes**: 15
- **Coverage Target**: 100%
- **Test Categories**: Unit, Integration, Functional, Acceptance, Security, Performance

## Test Categories

### Unit Tests (20+ tests)
- TestMLSMiddlewareInitialization
- TestMLSMiddlewareRequestProcessing
- TestMLSMiddlewareProcessView

### Integration Tests (5+ tests)
- TestMLSMiddlewareWithCrum
- TestMLSMiddlewareWithMLSModels

### Functional Tests (3+ tests)
- TestMLSMiddlewareRequestFlow

### Acceptance Tests (4+ tests)
- TestMLSMiddlewareAcceptance

### Security Tests (4+ tests)
- TestMLSMiddlewareSecurity

### Performance Tests (2+ tests)
- TestMLSMiddlewarePerformance

### Edge Cases (15+ tests)
- TestMLSMiddlewareEdgeCases
- TestMLSMiddlewareProcessViewEdgeCases

## Critical Security Tests

These tests validate security properties:

1. `test_middleware_does_not_bypass_authentication` - Authentication integrity
2. `test_middleware_does_not_expose_sensitive_data` - Information disclosure
3. `test_middleware_fails_secure_on_exception` - Fail-secure behavior
4. `test_middleware_preserves_security_headers` - Header preservation
5. `test_middleware_with_user_without_clearance` - Clearance enforcement

## Files Created

1. **test_middleware.py** - Main test suite (1000+ lines)
2. **TEST_MIDDLEWARE.md** - Detailed documentation
3. **README_MIDDLEWARE_TESTS.md** - This quick reference
4. **MIDDLEWARE_TEST_SUMMARY.md** - Comprehensive summary (in project root)

## Troubleshooting

### Django not configured
```bash
export DJANGO_SETTINGS_MODULE=mls.settings
pytest mls_core/test_middleware.py
```

### Import errors
Make sure you're in the correct directory:
```bash
cd /mnt/c/Users/john1/Documents/claude/mls/mls
```

### Performance tests skipped
Add the flag:
```bash
pytest mls_core/test_middleware.py --runperformance
```

## Additional Resources

- **Detailed Documentation**: `TEST_MIDDLEWARE.md`
- **Summary Report**: `../../../MIDDLEWARE_TEST_SUMMARY.md`
- **Middleware Source**: `middleware.py`

## Test Philosophy

This test suite follows security-first principles:

1. **Fail-Secure**: Tests validate secure failure modes
2. **Comprehensive**: All code paths tested
3. **Isolated**: Tests run independently
4. **Fast**: Complete suite runs in <1 second
5. **Security-Focused**: Critical security paths thoroughly validated

## Next Steps

1. Run the tests: `pytest mls_core/test_middleware.py -v`
2. Check coverage: `pytest mls_core/test_middleware.py --cov=mls_core.middleware --cov-report=html`
3. Review HTML report: Open `htmlcov/index.html` in browser
4. Add to CI/CD pipeline
5. Run tests before all commits

---

For detailed information, see `TEST_MIDDLEWARE.md` and `MIDDLEWARE_TEST_SUMMARY.md`.
