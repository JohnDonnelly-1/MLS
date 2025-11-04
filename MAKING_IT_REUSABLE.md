# Making MLS Core a Reusable Django App - Complete Guide

## What Was Done to Make It Reusable

MLS Core has been refactored to be **completely independent** of your specific project. Here's what was changed:

### 1. Configuration-Based Design ✅

**Before**: Hardcoded imports from `abac` app
```python
from abac.models import Security, Label
```

**After**: Configurable via Django settings
```python
from .settings import get_mls_security_model, get_mls_label_model

Security = get_mls_security_model()
Label = get_mls_label_model()
```

### 2. Added Settings Module ✅

Created `mls_core/settings.py` with configurable options:

```python
# In your project's settings.py:
MLS_SECURITY_MODEL = 'your_app.SecurityClearance'
MLS_LABEL_MODEL = 'your_app.SecurityLabel'
MLS_SECURITY_LABELS_FIELD = 'securities'  # Configurable field name
MLS_SUBJECT_CLEARANCE_FIELDS = ['clearances', 'accesses', 'security']
MLS_OBJECT_CLASSIFICATION_FIELDS = ['classification', 'security', 'security_label']
```

### 3. Flexible Field Names ✅

The code now uses configured field names instead of hardcoded ones:

```python
# Gets field name from settings
labels_field = getattr(security_obj, MLS_SECURITY_LABELS_FIELD)
```

### 4. Example Models Provided ✅

Created `example_models.py` with reference implementations that projects can copy:

```python
class SecurityLabel(models.Model):
    short_code = models.CharField(max_length=10)
    name = models.CharField(max_length=100)
    label_type = models.CharField(max_length=3)

class SecurityClearance(models.Model):
    securities = models.ManyToManyField(SecurityLabel)
```

### 5. Distribution Files ✅

- `setup.py` - For pip installation
- `MANIFEST.in` - Package file inclusion
- `LICENSE` - MIT license
- `REUSABLE_APP.md` - Complete reusability guide

## How to Use MLS Core in ANY Django Project

### Quick Start (3 Steps)

**Step 1: Add MLS Core to your project**

```bash
# Option A: Copy into your project
cp -r mls_core /path/to/your/project/

# Option B: Install via pip (if packaged)
pip install django-mls-core
```

**Step 2: Create your security models**

```python
# your_app/models.py
from django.db import models

class SecurityLabel(models.Model):
    name = models.CharField(max_length=100)

class SecurityClearance(models.Model):
    securities = models.ManyToManyField(SecurityLabel)
```

**Step 3: Configure settings**

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'mls_core',
    'your_app',
]

MLS_SECURITY_MODEL = 'your_app.SecurityClearance'
MLS_LABEL_MODEL = 'your_app.SecurityLabel'

MIDDLEWARE = [
    # ...
    'crum.CurrentRequestUserMiddleware',
    'mls_core.middleware.MLSMiddleware',
]
```

That's it! Now use MLS Core in your models:

```python
from mls_core import MLSObject, MLSForeignKey

class Document(MLSObject):
    title = models.CharField(max_length=200)
    classification = MLSForeignKey(
        'SecurityClearance',
        mls_control=True,
        on_delete=models.CASCADE
    )

# Queries automatically filtered!
docs = Document.objects.for_current_user()
```

## What Each File Does

### Core Files

| File | Purpose | Reusable? |
|------|---------|-----------|
| `__init__.py` | Package exports | ✅ Yes |
| `settings.py` | Configuration management | ✅ Yes |
| `fields.py` | Custom field types | ✅ Yes |
| `managers.py` | QuerySet and Manager | ✅ Yes |
| `metaclasses.py` | Auto-injection of MLS | ✅ Yes |
| `models.py` | Abstract base models | ✅ Yes |
| `middleware.py` | User context | ✅ Yes |
| `apps.py` | App configuration | ✅ Yes |

### Documentation Files

| File | Purpose |
|------|---------|
| `README.md` | Full documentation |
| `QUICKSTART.md` | 5-minute guide |
| `EXAMPLES.md` | Usage examples |
| `REUSABLE_APP.md` | Reusability guide |
| `TEST_GUIDE.md` | Testing documentation |

### Distribution Files

| File | Purpose |
|------|---------|
| `setup.py` | pip package configuration |
| `MANIFEST.in` | Package file inclusion |
| `LICENSE` | MIT license |
| `example_models.py` | Reference implementation |

### Test Files

| File | Purpose |
|------|---------|
| `tests.py` | Comprehensive test suite |

## Requirements for Your Security Models

Your security models only need to meet these minimal requirements:

### Security Model Requirements

**Must Have:**
```python
class YourSecurityModel(models.Model):
    # A ManyToManyField to your label model
    # Field name must match MLS_SECURITY_LABELS_FIELD (default: 'securities')
    securities = models.ManyToManyField(YourLabelModel)
```

**That's it!** Everything else is optional.

### Label Model Requirements

**Must Have:**
```python
class YourLabelModel(models.Model):
    # Any fields you want - MLS Core doesn't care about internal structure
    # It just needs to be queryable
    pass
```

**That's it!** No specific fields required.

### Subject Model Requirements

```python
class YourSubjectModel(MLSSubject):
    # Must have ONE of these fields (or configure custom names):
    clearances = models.OneToOneField(YourSecurityModel, ...)
    # OR
    accesses = models.OneToOneField(YourSecurityModel, ...)
    # OR
    security = models.OneToOneField(YourSecurityModel, ...)
```

### Object Model Requirements

```python
class YourObjectModel(MLSObject):
    # Must have ONE of these fields (or configure custom names):
    classification = models.ForeignKey(YourSecurityModel, mls_control=True, ...)
    # OR
    security = models.ForeignKey(YourSecurityModel, mls_control=True, ...)
    # OR
    security_label = models.ForeignKey(YourSecurityModel, mls_control=True, ...)
```

## Distribution Options

### Option 1: Internal Use (Copy)

**Best for:** Single project or organization

```bash
# Just copy the folder
cp -r mls_core /path/to/your/project/
```

**Pros:**
- Simple
- Easy to customize
- No packaging needed

**Cons:**
- Manual updates
- Not shareable

### Option 2: Git Repository

**Best for:** Multiple projects in same organization

```bash
# Create a git repo
cd mls_core
git init
git add .
git commit -m "Initial commit"

# Push to your git server
git remote add origin https://your-git-server.com/mls_core.git
git push -u origin main

# Install in projects
pip install git+https://your-git-server.com/mls_core.git
```

**Pros:**
- Version controlled
- Easy to update
- Shareable within organization

**Cons:**
- Requires git infrastructure
- Not public

### Option 3: PyPI Package

**Best for:** Public distribution

```bash
# Build the package
cd mls_core
python setup.py sdist bdist_wheel

# Upload to PyPI
pip install twine
twine upload dist/*

# Install from PyPI
pip install django-mls-core
```

**Pros:**
- Professional distribution
- Easy installation
- Version management
- Public availability

**Cons:**
- Most setup required
- Naming conflicts possible
- PyPI account needed

### Option 4: Private Package Server

**Best for:** Enterprise use

```bash
# Upload to your private PyPI
twine upload --repository-url https://your-pypi.company.com/simple dist/*

# Install from private server
pip install --index-url https://your-pypi.company.com/simple django-mls-core
```

**Pros:**
- Professional + Private
- Control over distribution
- Version management

**Cons:**
- Requires infrastructure
- Most complex setup

## Configuration Examples

### Example 1: Government Classification

```python
# settings.py
MLS_SECURITY_MODEL = 'clearance.Classification'
MLS_LABEL_MODEL = 'clearance.Level'

# models.py
class Level(models.Model):
    """UNCLASSIFIED, CONFIDENTIAL, SECRET, TOP SECRET"""
    name = models.CharField(max_length=50)
    rank = models.IntegerField()  # Hierarchical order

class Classification(models.Model):
    securities = models.ManyToManyField(Level)
    department = models.CharField(max_length=100)

class Document(MLSObject):
    classification = MLSForeignKey(Classification, mls_control=True)
```

### Example 2: Healthcare HIPAA

```python
# settings.py
MLS_SECURITY_MODEL = 'medical.AccessLevel'
MLS_LABEL_MODEL = 'medical.PrivacyTag'
MLS_SECURITY_LABELS_FIELD = 'tags'  # Different field name!

# models.py
class PrivacyTag(models.Model):
    """PHI, PII, RESTRICTED, etc."""
    name = models.CharField(max_length=50)

class AccessLevel(models.Model):
    tags = models.ManyToManyField(PrivacyTag)  # Note: 'tags' not 'securities'
    role = models.CharField(max_length=50)

class PatientRecord(MLSObject):
    patient_name = models.CharField(max_length=100)
    access_level = MLSForeignKey(AccessLevel, mls_control=True)

    class Meta:
        mls_protected = True
        mls_classification_field = 'access_level'
```

### Example 3: Corporate Data

```python
# settings.py
MLS_SECURITY_MODEL = 'corp.DataClass'
MLS_LABEL_MODEL = 'corp.Sensitivity'

# models.py
class Sensitivity(models.Model):
    """PUBLIC, INTERNAL, CONFIDENTIAL, RESTRICTED"""
    level = models.CharField(max_length=20)
    color_code = models.CharField(max_length=7)  # Custom field

class DataClass(models.Model):
    name = models.CharField(max_length=100)
    securities = models.ManyToManyField(Sensitivity)
    department = models.CharField(max_length=50)

class File(MLSObject):
    filename = models.CharField(max_length=255)
    classification = MLSForeignKey(DataClass, mls_control=True)
```

## Testing Reusability

### Test in a Fresh Django Project

```bash
# Create new project
django-admin startproject testproject
cd testproject

# Add mls_core
cp -r /path/to/mls_core .

# Create test app
python manage.py startapp testapp
```

```python
# testapp/models.py
from django.db import models
from mls_core import MLSSubject, MLSObject, MLSForeignKey

class Label(models.Model):
    name = models.CharField(max_length=50)

class Security(models.Model):
    securities = models.ManyToManyField(Label)

class User(MLSSubject):
    name = models.CharField(max_length=50)
    clearances = models.OneToOneField(Security, on_delete=models.CASCADE, null=True)

class Document(MLSObject):
    title = models.CharField(max_length=200)
    classification = MLSForeignKey(Security, mls_control=True, on_delete=models.CASCADE)
```

```python
# testproject/settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'crum',
    'mls_core',
    'testapp',
]

MLS_SECURITY_MODEL = 'testapp.Security'
MLS_LABEL_MODEL = 'testapp.Label'
```

```bash
# Run migrations and test
python manage.py makemigrations
python manage.py migrate
python manage.py shell
```

```python
# In shell - test it works
from testapp.models import *

# Create labels
pub = Label.objects.create(name="Public")
sec = Label.objects.create(name="Secret")

# Create securities
pub_sec = Security.objects.create()
pub_sec.securities.add(pub)

secret_sec = Security.objects.create()
secret_sec.securities.add(pub, sec)

# Create users
low = User.objects.create(name="Low", clearances=pub_sec)
high = User.objects.create(name="High", clearances=secret_sec)

# Create docs
doc1 = Document.objects.create(title="Public", classification=pub_sec)
doc2 = Document.objects.create(title="Secret", classification=secret_sec)

# Test access
assert low.can_access(doc1) == True
assert low.can_access(doc2) == False
assert high.can_access(doc1) == True
assert high.can_access(doc2) == True

print("✅ MLS Core works in new project!")
```

## Summary

### What Makes MLS Core Reusable

✅ **No hardcoded models** - Uses Django settings
✅ **Configurable field names** - Adapts to your conventions
✅ **Minimal requirements** - Just needs ManyToManyField
✅ **Example models** - Copy and customize
✅ **Well documented** - Multiple guides
✅ **Tested** - Comprehensive test suite
✅ **Licensed** - MIT license
✅ **Distributable** - setup.py included

### What You Need to Do

1. **Copy or install** MLS Core
2. **Create security models** (2 simple models)
3. **Configure settings** (3 lines)
4. **Use in your models** (inherit from MLSObject)

That's it! 🚀

### Files to Distribute

If sharing MLS Core, include:

**Essential:**
- `mls_core/*.py` - All Python files
- `README.md` - Documentation
- `LICENSE` - MIT license

**Recommended:**
- `QUICKSTART.md` - Quick guide
- `REUSABLE_APP.md` - Reusability guide
- `EXAMPLES.md` - Usage examples
- `example_models.py` - Reference models
- `setup.py` - pip packaging

**Optional:**
- `tests.py` - Test suite
- `TEST_GUIDE.md` - Testing docs
- `MANIFEST.in` - Package config

MLS Core is now a **fully reusable Django app** that can be used in any Django project! 🎉
