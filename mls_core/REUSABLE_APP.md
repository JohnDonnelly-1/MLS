# Making MLS Core a Reusable Django App

This guide explains how MLS Core is designed to be reusable across any Django project.

## Overview

MLS Core is now **fully reusable** - it doesn't depend on any specific models from your project. Instead, it uses configurable settings (similar to Django's `AUTH_USER_MODEL`) to adapt to your security models.

## What Makes It Reusable?

### 1. Configurable Security Models

MLS Core doesn't hardcode which models to use for security. Instead, you configure them in `settings.py`:

```python
# settings.py
MLS_SECURITY_MODEL = 'myapp.SecurityClearance'  # Your security model
MLS_LABEL_MODEL = 'myapp.SecurityLabel'         # Your label model
```

### 2. Configurable Field Names

Different projects may use different field names. MLS Core supports this:

```python
# settings.py

# Field name on the security model that contains labels (default: 'securities')
MLS_SECURITY_LABELS_FIELD = 'labels'

# Field names to check on subjects for clearances (defaults shown)
MLS_SUBJECT_CLEARANCE_FIELDS = ['clearances', 'accesses', 'security']

# Field names to check on objects for classifications (defaults shown)
MLS_OBJECT_CLASSIFICATION_FIELDS = ['classification', 'security', 'security_label']
```

### 3. No Hard Dependencies

MLS Core only requires:
- Django (any recent version)
- `django-crum` (for current user context)

It doesn't require any specific security models to be installed.

## Using MLS Core in a New Project

### Step 1: Copy or Install MLS Core

**Option A: Copy the app to your project**
```bash
cp -r mls_core /path/to/your/project/
```

**Option B: Install as a package** (if you create setup.py)
```bash
pip install django-mls-core
```

### Step 2: Create Your Security Models

You have two options:

**Option A: Use the example models**

Copy the example models to your app:

```python
# myapp/models.py
from django.db import models

class SecurityLabel(models.Model):
    """Security label (level or category)"""
    class LabelType(models.TextChoices):
        LEVEL = "LVL", "Level"
        CATEGORY = "CAT", "Category"

    short_code = models.CharField(max_length=10, unique=True)
    name = models.CharField(max_length=100)
    label_type = models.CharField(max_length=3, choices=LabelType.choices)

    def __str__(self):
        return f"{self.short_code} - {self.name}"

class SecurityClearance(models.Model):
    """Security clearance/classification"""
    name = models.CharField(max_length=100, blank=True)

    # IMPORTANT: This field name must match MLS_SECURITY_LABELS_FIELD
    securities = models.ManyToManyField(SecurityLabel, related_name="clearances")

    def __str__(self):
        return self.name or f"Security {self.pk}"
```

**Option B: Adapt your existing models**

If you already have security models, just ensure they have:
1. A many-to-many relationship to labels
2. The field name specified in `MLS_SECURITY_LABELS_FIELD`

### Step 3: Configure Settings

```python
# settings.py

INSTALLED_APPS = [
    # ... other apps
    'mls_core',
    'myapp',  # Your app with security models
]

# Configure MLS Core
MLS_SECURITY_MODEL = 'myapp.SecurityClearance'
MLS_LABEL_MODEL = 'myapp.SecurityLabel'

# Optional: customize field names (these are defaults)
MLS_SECURITY_LABELS_FIELD = 'securities'
MLS_SUBJECT_CLEARANCE_FIELDS = ['clearances', 'accesses', 'security']
MLS_OBJECT_CLASSIFICATION_FIELDS = ['classification', 'security', 'security_label']

# Add middleware
MIDDLEWARE = [
    # ... other middleware
    'crum.CurrentRequestUserMiddleware',
    'mls_core.middleware.MLSMiddleware',
]
```

### Step 4: Use MLS Core in Your Models

```python
# myapp/models.py
from django.db import models
from mls_core import MLSSubject, MLSObject, MLSForeignKey

class User(MLSSubject):
    """User with security clearances"""
    username = models.CharField(max_length=50)
    clearances = models.OneToOneField(
        'SecurityClearance',
        on_delete=models.SET_NULL,
        null=True
    )

class Document(MLSObject):
    """MLS-protected document"""
    title = models.CharField(max_length=200)
    content = models.TextField()
    classification = MLSForeignKey(
        'SecurityClearance',
        mls_control=True,
        on_delete=models.CASCADE
    )
```

### Step 5: Run Migrations

```bash
python manage.py makemigrations
python manage.py migrate
```

### Step 6: Use MLS Filtering

```python
# In your views
def document_list(request):
    # Automatically filtered by current user's clearances
    docs = Document.objects.for_current_user()
    return render(request, 'documents.html', {'documents': docs})

# Explicit filtering
user = User.objects.get(username='alice')
accessible_docs = Document.objects.accessible_by(user)

# Check access
if user.can_access(document):
    # User has access
    pass
```

## Security Model Requirements

Your security model must have:

### Required
- A **ManyToManyField** to a label model
- The field name must match `MLS_SECURITY_LABELS_FIELD` (default: `securities`)

### Example Minimal Security Model

```python
class MinimalSecurity(models.Model):
    # This field name must match MLS_SECURITY_LABELS_FIELD setting
    securities = models.ManyToManyField('SecurityLabel')
```

### Example Minimal Label Model

```python
class MinimalLabel(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name
```

That's it! No other requirements.

## Distribution Options

### Option 1: Copy Into Project

Simplest approach - just copy the `mls_core` folder into your project.

**Pros:**
- Easy to customize
- No external dependencies
- Can modify as needed

**Cons:**
- Need to manually update
- Not shared across projects

### Option 2: Create a Pip Package

Create a `setup.py` to distribute via pip:

```python
# setup.py
from setuptools import setup, find_packages

setup(
    name='django-mls-core',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Django>=3.2',
        'django-crum>=0.7.9',
    ],
    description='Multi-Level Security for Django',
    author='Your Name',
    author_email='you@example.com',
    url='https://github.com/yourusername/django-mls-core',
    classifiers=[
        'Framework :: Django',
        'License :: OSI Approved :: MIT License',
        'Programming Language :: Python :: 3',
    ],
)
```

Then install with:
```bash
pip install django-mls-core
```

**Pros:**
- Easy to install across projects
- Versioned releases
- Can share publicly

**Cons:**
- More setup required
- Harder to customize

### Option 3: Git Submodule

Add as a git submodule:

```bash
git submodule add https://github.com/yourusername/mls_core.git
```

**Pros:**
- Version controlled
- Easy to update
- Can contribute back changes

**Cons:**
- Requires git knowledge
- Submodule complexity

## Example Projects

### Project A: Government Documents

```python
# settings.py
MLS_SECURITY_MODEL = 'clearance.Classification'
MLS_LABEL_MODEL = 'clearance.SecurityLevel'

# models.py
class SecurityLevel(models.Model):
    name = models.CharField(max_length=50)
    # ... other fields

class Classification(models.Model):
    securities = models.ManyToManyField(SecurityLevel)

class GovDocument(MLSObject):
    title = models.CharField(max_length=200)
    classification = MLSForeignKey(Classification, mls_control=True)
```

### Project B: Medical Records

```python
# settings.py
MLS_SECURITY_MODEL = 'medical.AccessLevel'
MLS_LABEL_MODEL = 'medical.AccessTag'
MLS_SECURITY_LABELS_FIELD = 'tags'  # Different field name

# models.py
class AccessTag(models.Model):
    name = models.CharField(max_length=50)

class AccessLevel(models.Model):
    tags = models.ManyToManyField(AccessTag)  # Note: 'tags' not 'securities'

class MedicalRecord(MLSObject):
    patient = models.CharField(max_length=100)
    access_level = MLSForeignKey(AccessLevel, mls_control=True)
```

### Project C: Corporate Data

```python
# settings.py
MLS_SECURITY_MODEL = 'corp.DataClassification'
MLS_LABEL_MODEL = 'corp.SecurityMarking'

# models.py
class SecurityMarking(models.Model):
    name = models.CharField(max_length=50)
    level = models.IntegerField()  # Custom fields OK

class DataClassification(models.Model):
    name = models.CharField(max_length=100)
    securities = models.ManyToManyField(SecurityMarking)
    department = models.CharField(max_length=50)  # Custom fields OK

class CorporateFile(MLSObject):
    filename = models.CharField(max_length=255)
    classification = MLSForeignKey(DataClassification, mls_control=True)
```

## Testing Your Reusable App

When using MLS Core in a new project, test it works:

```python
# Test basic functionality
from myapp.models import User, Document, SecurityClearance, SecurityLabel

# Create labels
public = SecurityLabel.objects.create(name="Public", short_code="PUB")
secret = SecurityLabel.objects.create(name="Secret", short_code="SEC")

# Create clearances
public_clearance = SecurityClearance.objects.create(name="Public")
public_clearance.securities.add(public)

secret_clearance = SecurityClearance.objects.create(name="Secret")
secret_clearance.securities.add(public, secret)

# Create users
low_user = User.objects.create(username="low", clearances=public_clearance)
high_user = User.objects.create(username="high", clearances=secret_clearance)

# Create documents
pub_doc = Document.objects.create(title="Public", classification=public_clearance)
sec_doc = Document.objects.create(title="Secret", classification=secret_clearance)

# Test access
assert low_user.can_access(pub_doc) == True
assert low_user.can_access(sec_doc) == False
assert high_user.can_access(pub_doc) == True
assert high_user.can_access(sec_doc) == True

print("✅ MLS Core is working correctly!")
```

## Configuration Reference

### All Available Settings

```python
# settings.py

# Required: Specify your security models
MLS_SECURITY_MODEL = 'app.Model'  # Model that holds sets of labels
MLS_LABEL_MODEL = 'app.Model'     # Model that represents individual labels

# Optional: Field name configuration
MLS_SECURITY_LABELS_FIELD = 'securities'  # Field on security model for labels
MLS_SUBJECT_CLEARANCE_FIELDS = [          # Fields to check on subjects
    'clearances',
    'accesses',
    'security'
]
MLS_OBJECT_CLASSIFICATION_FIELDS = [      # Fields to check on objects
    'classification',
    'security',
    'security_label'
]
```

### Defaults

If you don't specify settings, MLS Core uses these defaults:

```python
MLS_SECURITY_MODEL = 'abac.Security'
MLS_LABEL_MODEL = 'abac.Label'
MLS_SECURITY_LABELS_FIELD = 'securities'
MLS_SUBJECT_CLEARANCE_FIELDS = ['clearances', 'accesses', 'security']
MLS_OBJECT_CLASSIFICATION_FIELDS = ['classification', 'security', 'security_label']
```

## Troubleshooting

### Error: "MLS_SECURITY_MODEL refers to model that has not been installed"

**Solution**: Ensure your security model's app is in `INSTALLED_APPS` and comes *before* `mls_core`.

### Error: "AttributeError: 'SecurityClearance' object has no attribute 'securities'"

**Solution**: Make sure your security model has a field matching `MLS_SECURITY_LABELS_FIELD`.

### No objects returned by queries

**Solution**: Check that:
1. Field names match your configuration
2. Users have clearances set
3. Objects have classifications set
4. Labels are correctly added to security clearances

## Summary

MLS Core is fully reusable because:

✅ **No hard-coded models** - Uses configurable settings
✅ **Flexible field names** - Adapts to your naming conventions
✅ **Minimal requirements** - Just needs ManyToManyField to labels
✅ **No dependencies** - Only Django and django-crum
✅ **Example models** - Reference implementation provided
✅ **Well documented** - Complete guides and examples

Use it in any Django project that needs Multi-Level Security! 🚀
