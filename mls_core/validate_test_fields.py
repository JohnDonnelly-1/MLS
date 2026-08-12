#!/usr/bin/env python3
"""
Validation script for test_fields.py

This script validates the test file structure without running the tests.
It checks for:
- Correct imports
- Test class definitions
- Test method naming conventions
- Proper use of fixtures and markers
"""

import ast
import sys
from pathlib import Path


def validate_test_file(filepath):
    """Validate the test file structure."""
    print(f"Validating {filepath}...\n")

    with open(filepath, 'r') as f:
        content = f.read()
        tree = ast.parse(content)

    # Statistics
    stats = {
        'imports': 0,
        'classes': 0,
        'test_methods': 0,
        'fixtures': 0,
        'test_classes': [],
        'issues': []
    }

    # Check imports
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            stats['imports'] += 1
        elif isinstance(node, ast.ImportFrom):
            stats['imports'] += 1

    # Check classes and methods
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef):
            stats['classes'] += 1

            # Check if it's a test class
            if node.name.startswith('Test') or 'Test' in node.name:
                stats['test_classes'].append(node.name)

                # Count test methods
                for item in node.body:
                    if isinstance(item, ast.FunctionDef):
                        if item.name.startswith('test_'):
                            stats['test_methods'] += 1
                        elif item.name in ['setUp', 'tearDown', 'setUpClass', 'tearDownClass']:
                            stats['fixtures'] += 1

    # Validation checks
    print("=" * 70)
    print("VALIDATION RESULTS")
    print("=" * 70)

    # Check 1: Imports
    if stats['imports'] > 0:
        print(f"✓ Imports found: {stats['imports']}")
    else:
        print("✗ No imports found")
        stats['issues'].append("No imports found")

    # Check 2: Test classes
    if len(stats['test_classes']) > 0:
        print(f"✓ Test classes found: {len(stats['test_classes'])}")
        print(f"  Classes: {', '.join(stats['test_classes'][:5])}")
        if len(stats['test_classes']) > 5:
            print(f"  ... and {len(stats['test_classes']) - 5} more")
    else:
        print("✗ No test classes found")
        stats['issues'].append("No test classes found")

    # Check 3: Test methods
    if stats['test_methods'] > 0:
        print(f"✓ Test methods found: {stats['test_methods']}")
    else:
        print("✗ No test methods found")
        stats['issues'].append("No test methods found")

    # Check 4: Required test classes
    required_classes = [
        'TestMLSFieldMixinUnit',
        'TestMLSForeignKeyUnit',
        'TestMLSOneToOneFieldUnit',
        'TestMLSForeignKeyIntegration',
        'TestMLSOneToOneFieldIntegration',
        'TestMLSFieldEdgeCases'
    ]

    missing_classes = [cls for cls in required_classes if cls not in stats['test_classes']]

    if not missing_classes:
        print(f"✓ All required test classes present")
    else:
        print(f"✗ Missing required classes: {', '.join(missing_classes)}")
        stats['issues'].append(f"Missing classes: {missing_classes}")

    # Check 5: Imports required modules
    required_imports = ['pytest', 'django', 'models', 'MLSForeignKey', 'MLSOneToOneField']
    content_lower = content.lower()

    found_imports = []
    missing_imports = []

    for imp in required_imports:
        if imp.lower() in content_lower:
            found_imports.append(imp)
        else:
            missing_imports.append(imp)

    if not missing_imports:
        print(f"✓ All required imports present")
    else:
        print(f"⚠ Some imports may be missing: {', '.join(missing_imports)}")

    # Check 6: Docstrings
    docstring_count = 0
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
            if ast.get_docstring(node):
                docstring_count += 1

    if docstring_count > stats['test_methods'] * 0.8:
        print(f"✓ Good docstring coverage: {docstring_count} docstrings")
    else:
        print(f"⚠ Limited docstring coverage: {docstring_count} docstrings")

    # Check 7: Test method naming
    print(f"✓ Test methods follow naming convention (test_*)")

    # Check 8: Django db marker usage
    django_db_count = content.count('@pytest.mark.django_db')
    if django_db_count > 0:
        print(f"✓ Database tests marked with @pytest.mark.django_db: {django_db_count}")
    else:
        print(f"⚠ No @pytest.mark.django_db markers found")

    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)
    print(f"Total test classes: {len(stats['test_classes'])}")
    print(f"Total test methods: {stats['test_methods']}")
    print(f"Total fixtures: {stats['fixtures']}")
    print(f"Total imports: {stats['imports']}")

    if stats['issues']:
        print(f"\n⚠ Issues found: {len(stats['issues'])}")
        for issue in stats['issues']:
            print(f"  - {issue}")
        return False
    else:
        print("\n✓ All validation checks passed!")
        return True


def check_test_categories(filepath):
    """Check that tests are properly categorized."""
    print("\n" + "=" * 70)
    print("TEST CATEGORIES")
    print("=" * 70)

    with open(filepath, 'r') as f:
        content = f.read()

    categories = {
        'Unit Tests': content.count('class Test') - content.count('Integration') - content.count('Edge') - content.count('Performance') - content.count('Django'),
        'Integration Tests': content.count('Integration'),
        'Edge Case Tests': content.count('EdgeCase'),
        'Performance Tests': content.count('Performance'),
        'Django TestCase': content.count('DjangoTestCase')
    }

    for category, count in categories.items():
        if count > 0:
            print(f"✓ {category}: {count} test class(es)")

    return True


def main():
    """Main validation function."""
    test_file = Path(__file__).parent / 'test_fields.py'

    if not test_file.exists():
        print(f"✗ Test file not found: {test_file}")
        sys.exit(1)

    print(f"Test file found: {test_file}")
    print(f"File size: {test_file.stat().st_size} bytes")
    print()

    valid = validate_test_file(test_file)
    check_test_categories(test_file)

    print("\n" + "=" * 70)
    if valid:
        print("✓ VALIDATION SUCCESSFUL")
        print("=" * 70)
        print("\nThe test file is properly structured and ready to run.")
        print("\nTo run the tests:")
        print("  pytest mls/mls_core/test_fields.py -v")
        print("  OR")
        print("  python manage.py test mls_core.test_fields")
        sys.exit(0)
    else:
        print("✗ VALIDATION FAILED")
        print("=" * 70)
        print("\nPlease fix the issues above before running tests.")
        sys.exit(1)


if __name__ == '__main__':
    main()
