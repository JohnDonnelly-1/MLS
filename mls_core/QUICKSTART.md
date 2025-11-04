# MLS Core - Quick Start Guide

Get up and running with Multi-Level Security in 5 minutes.

## Installation

### 1. Add to INSTALLED_APPS

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    # ... other apps
    'crum',  # Required: django-crum for user context
    'mls_core',  # Add this
    'abac',  # Your existing security labels app
]
```

### 2. Add Middleware

```python
# settings.py
MIDDLEWARE = [
    # ... other middleware
    'crum.CurrentRequestUserMiddleware',  # Required
    'mls_core.middleware.MLSMiddleware',  # Add this
]
```

### 3. Run Migrations

```bash
python manage.py migrate
```

## Quick Usage

### Protect a Model (Option 1: Field-Level)

```python
from django.db import models
from mls_core import MLSObject, MLSForeignKey

class Document(MLSObject):
    title = models.CharField(max_length=200)
    content = models.TextField()
    classification = MLSForeignKey(
        'abac.Security',
        mls_control=True,  # This enables MLS!
        on_delete=models.CASCADE
    )
```

### Protect a Model (Option 2: Meta-Level)

```python
from django.db import models
from mls_core import MLSObject

class SecureFile(MLSObject):
    filename = models.CharField(max_length=255)
    security_label = models.ForeignKey('abac.Security', on_delete=models.CASCADE)

    class Meta:
        mls_protected = True  # This enables MLS!
        mls_classification_field = 'security_label'
```

### Query with Automatic Filtering

```python
# In your views:
def document_list(request):
    # Automatically filtered by current user's clearances!
    documents = Document.objects.all()
    return render(request, 'docs.html', {'documents': documents})

# Or explicitly:
from .models import FakeUser

user = FakeUser.objects.get(name='Alice')
docs = Document.objects.accessible_by(user)
```

### Check Access Programmatically

```python
user = FakeUser.objects.get(name='Alice')
document = Document.all_objects.get(id=123)  # Unfiltered access

if user.can_access(document):
    # User has all required clearances
    return document.content
else:
    # Access denied
    raise PermissionDenied()
```

## Key Concepts

### Subject vs Object

- **Subject** = Entity that accesses (User, Computer, Network)
  - Inherits from `MLSSubject`
  - Has `clearances` or `accesses` field

- **Object** = Entity that needs protection (File, Database Row, etc.)
  - Inherits from `MLSObject`
  - Has `classification` or `security` field

### The MLS Rule

**A subject can access an object ONLY if the subject has ALL of the object's security labels.**

Example:
- Object requires labels: `[SECRET, CRYPTO]`
- Subject has labels: `[SECRET, CRYPTO, INTEL]`
- **Result**: ✅ Access granted (subject has all required labels)

Example:
- Object requires labels: `[SECRET, CRYPTO]`
- Subject has labels: `[SECRET]`
- **Result**: ❌ Access denied (subject missing CRYPTO label)

### Managers

Every MLS-protected model automatically gets two managers:

1. **`objects`** - MLS filtered (default, secure)
2. **`all_objects`** - Unfiltered (for admin use)

```python
# Filtered by current user
docs = Document.objects.all()

# Unfiltered (admin only)
all_docs = Document.all_objects.all()
```

## Common Patterns

### In Views

```python
def my_view(request):
    # Automatic filtering
    items = MyModel.objects.for_current_user()
    return render(request, 'template.html', {'items': items})
```

### In Admin Views

```python
def admin_view(request):
    if not request.user.is_staff:
        return HttpResponseForbidden()

    # Unfiltered access
    all_items = MyModel.all_objects.all()
    return render(request, 'admin.html', {'items': all_items})
```

### Explicit User Filtering

```python
def user_items(request, user_id):
    subject = FakeUser.objects.get(id=user_id)
    items = MyModel.objects.accessible_by(subject)
    return render(request, 'items.html', {'items': items})
```

## Next Steps

- Read [README.md](README.md) for full documentation
- See [EXAMPLES.md](EXAMPLES.md) for practical examples
- Check out the test cases in `tests.py`
- Migrate your existing models step by step

## Troubleshooting

### No objects returned

**Problem**: `MyModel.objects.all()` returns empty queryset

**Solutions**:
1. Check that current user has clearances set
2. Verify the user's clearances include all required object labels
3. Use `all_objects` to see unfiltered results
4. Check middleware is installed correctly

### DoesNotExist errors

**Problem**: `MyModel.objects.get(id=123)` raises DoesNotExist

**Reason**: The object exists, but current user doesn't have access

**Solution**: Use `all_objects` for unfiltered access, or check user clearances

### Field not found

**Problem**: "Field 'classification' not found"

**Solution**: Make sure your model has a field pointing to `Security` and it's marked with `mls_control=True` or specified in Meta

## Support

For issues, questions, or contributions, see the main project README.
