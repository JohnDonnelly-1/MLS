# MLS Core - Multi-Level Security for Django

A reusable Django application that provides automatic Multi-Level Security (MLS) enforcement at the ORM level.

## Core Principle

**The fundamental MLS rule**: A subject can access an object **ONLY** if the subject possesses **ALL** of the security labels/attributes that the object requires.

## Features

- **Secure by default**: Automatic MLS filtering on all queries
- **Model-level protection**: Use Meta options to enable MLS
- **Field-level control**: Mark specific fields as MLS control fields
- **Transparent integration**: Works seamlessly with existing Django code
- **Explicit override**: Unfiltered access available when needed

## Installation

1. Add `mls_core` to your `INSTALLED_APPS`:

```python
INSTALLED_APPS = [
    ...
    'mls_core',
]
```

2. Add middleware (place after django-crum middleware):

```python
MIDDLEWARE = [
    ...
    'crum.CurrentRequestUserMiddleware',  # Required: django-crum
    'mls_core.middleware.MLSMiddleware',
    ...
]
```

## Usage

### Option 1: Field-Level MLS Control (Recommended)

Mark specific fields as MLS control fields using custom field types:

```python
from django.db import models
from mls_core import MLSObject, MLSForeignKey

class Document(MLSObject):
    title = models.CharField(max_length=200)
    content = models.TextField()
    # This field controls MLS access
    classification = MLSForeignKey(
        'abac.Security',
        mls_control=True,
        on_delete=models.CASCADE
    )
```

### Option 2: Model-Level MLS Protection

Use Meta options to enable MLS protection:

```python
from django.db import models
from mls_core import MLSObject

class SecureFile(MLSObject):
    filename = models.CharField(max_length=255)
    content = models.BinaryField()
    security_label = models.ForeignKey('abac.Security', on_delete=models.CASCADE)

    class Meta:
        mls_protected = True
        mls_classification_field = 'security_label'
```

### Option 3: Hybrid Approach

Combine both approaches for maximum flexibility:

```python
from django.db import models
from mls_core import MLSObject, MLSOneToOneField

class DatabaseRow(MLSObject):
    data = models.TextField()
    classification = MLSOneToOneField(
        'abac.Security',
        mls_control=True,
        on_delete=models.CASCADE
    )

    class Meta:
        mls_protected = True  # Extra safety
```

## Defining Subjects

Subjects are entities that access objects (users, systems, networks):

```python
from django.db import models
from mls_core import MLSSubject

class User(MLSSubject):
    username = models.CharField(max_length=50)
    clearances = models.OneToOneField(
        'abac.Security',
        on_delete=models.SET_NULL,
        null=True
    )
```

## Querying with MLS

### Automatic Filtering (Default)

All queries are automatically filtered based on the current user's clearances:

```python
# Automatically filtered - only returns accessible documents
documents = Document.objects.all()

# Also filtered
doc = Document.objects.get(id=123)  # Raises DoesNotExist if not accessible
```

### Explicit Subject Filtering

Filter for a specific subject:

```python
user = User.objects.get(username='alice')
accessible_docs = Document.objects.accessible_by(user)
```

### Current User Filtering

Use the current request user:

```python
# In a view:
my_docs = Document.objects.for_current_user()
```

### Unfiltered Access (Admin/System Operations)

When you need to bypass MLS (use with caution):

```python
# Option 1: Use unfiltered() method
all_docs = Document.objects.unfiltered()

# Option 2: Use all_objects manager
all_docs = Document.all_objects.all()
```

## Checking Access Programmatically

Check if a subject can access an object:

```python
user = User.objects.get(username='alice')
document = Document.all_objects.get(id=123)

if user.can_access(document):
    # User has access
    print(document.content)
else:
    # Access denied
    raise PermissionDenied()

# Or from the object side:
if document.accessible_by(user):
    # User has access
    pass
```

## How It Works

1. **Subject Clearances**: Each subject has a set of security labels (clearances)
2. **Object Classifications**: Each object has a set of required security labels
3. **Access Rule**: Subject must have ALL of the object's labels to access it
4. **QuerySet Filtering**: The custom manager automatically filters queries
5. **Secure by Default**: If no subject is found, access is denied

## Architecture

### Components

- **MLSSubject**: Abstract base model for entities that access objects
- **MLSObject**: Abstract base model for protected objects
- **MLSManager**: Custom manager that enforces MLS on all queries
- **MLSQuerySet**: Custom queryset with MLS filtering logic
- **MLSForeignKey/MLSOneToOneField**: Field types with `mls_control` parameter
- **MLSModelBase**: Metaclass that auto-injects MLS behavior
- **MLSMiddleware**: Middleware for user context management

### Security Model

The system uses the existing `Security` model from the `abac` app:

```python
class Security(models.Model):
    securities = models.ManyToManyField(Label)
```

Each `Security` instance contains a set of `Label` objects, which can be:
- Levels (hierarchical): TOP_SECRET, SECRET, CONFIDENTIAL, etc.
- Categories (compartments): CRYPTO, NUCLEAR, INTEL, etc.

## Examples

### Example 1: Simple Document Protection

```python
from mls_core import MLSObject, MLSForeignKey

class Document(MLSObject):
    title = models.CharField(max_length=200)
    classification = MLSForeignKey(
        'abac.Security',
        mls_control=True,
        on_delete=models.CASCADE
    )

# Usage in a view:
def document_list(request):
    # Only shows documents the current user can access
    docs = Document.objects.all()
    return render(request, 'docs.html', {'documents': docs})
```

### Example 2: Database Row-Level Security

```python
from mls_core import MLSObject, MLSForeignKey

class MedicalRecord(MLSObject):
    patient_name = models.CharField(max_length=100)
    diagnosis = models.TextField()
    classification = MLSForeignKey(
        'abac.Security',
        mls_control=True,
        on_delete=models.CASCADE
    )

# Only accessible records are returned
records = MedicalRecord.objects.all()
```

### Example 3: Mixed Access Levels

```python
# Create security labels
public = Security.objects.create()
secret = Security.objects.create()

# Create documents with different classifications
doc1 = Document.objects.create(title="Public", classification=public)
doc2 = Document.objects.create(title="Secret", classification=secret)

# User with only public clearance
user1 = User.objects.create(username='alice', clearances=public)

# User with both clearances
user2_clearances = Security.objects.create()
user2_clearances.securities.add(*public.securities.all())
user2_clearances.securities.add(*secret.securities.all())
user2 = User.objects.create(username='bob', clearances=user2_clearances)

# alice can only see doc1
Document.objects.accessible_by(user1)  # Returns [doc1]

# bob can see both
Document.objects.accessible_by(user2)  # Returns [doc1, doc2]
```

## Best Practices

1. **Use Field-Level MLS**: Prefer `mls_control=True` on fields for clarity
2. **Inherit from MLSObject**: Always use `MLSObject` as base for protected models
3. **Be Explicit with Unfiltered**: Only use `unfiltered()` or `all_objects` when absolutely necessary
4. **Test Access Control**: Write tests to verify MLS rules are enforced
5. **Document Classifications**: Clearly document what security labels mean in your system

## Limitations

- **Performance**: The current implementation loads objects to check labels (can be optimized with better queries)
- **Label Changes**: Changing security labels on objects/subjects may require cache invalidation
- **Complex Queries**: Very complex queries may need manual MLS checks

## Future Enhancements

- Query optimization using annotations and subqueries
- Caching layer for label comparisons
- Admin interface for managing clearances
- Audit logging for access attempts
- Cell-level (field-level) protection within objects
- Write protection (currently focuses on read access)

## License

This is part of the MLS project.
