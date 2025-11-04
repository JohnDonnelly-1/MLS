# MLS Core - Practical Examples

## Migrating Existing ABAC App to MLS Core

Here's how to refactor your existing `abac` app to use the new MLS core.

### Before (Original Code)

```python
# abac/models.py
from django.db import models

class FakeUser(models.Model):
    name = models.CharField(max_length=50)
    accesses = models.OneToOneField(Security, on_delete=models.SET_NULL, null=True)

class Object(models.Model):
    name = models.CharField(max_length=15)
    obj_type = models.CharField(max_length=4, choices=ObjectType.choices)
    x_coords = models.PositiveSmallIntegerField(default=50)
    y_coords = models.PositiveSmallIntegerField(default=50)
    security = models.OneToOneField(Security, on_delete=models.CASCADE)
```

### After (Using MLS Core)

```python
# abac/models.py
from django.db import models
from mls_core import MLSSubject, MLSObject, MLSOneToOneField

class FakeUser(MLSSubject):
    """MLS Subject - can access objects based on clearances"""
    name = models.CharField(max_length=50)
    accesses = models.OneToOneField(Security, on_delete=models.SET_NULL, null=True)

    # Inherits can_access() method from MLSSubject

class Object(MLSObject):
    """MLS Object - access controlled by security classification"""

    class ObjectType(models.TextChoices):
        SHIP = "SHIP", "Ship"
        SUB = "SUB", "Submarine"
        AC = "AC", "Aircraft"
        FILE = "FILE", "File"

    name = models.CharField(max_length=15)
    obj_type = models.CharField(max_length=4, choices=ObjectType.choices, default=ObjectType.SHIP)
    x_coords = models.PositiveSmallIntegerField(default=50)
    y_coords = models.PositiveSmallIntegerField(default=50)

    # Mark this field as the MLS control field
    security = MLSOneToOneField(Security, mls_control=True, on_delete=models.CASCADE)

    # Automatically inherits:
    # - objects manager (MLS filtered)
    # - all_objects manager (unfiltered)
    # - accessible_by() method
```

### Updated Views with Automatic Filtering

```python
# abac/views.py
from django.shortcuts import get_object_or_404
from django.template.response import TemplateResponse
from .models import FakeUser, Object

def object_list(request):
    # Automatically filtered based on current user's clearances!
    objs = Object.objects.for_current_user()
    return TemplateResponse(
        request,
        template="abac/objects.html",
        context={'objs': objs}
    )

def item(request, pk):
    # Automatically checks access - raises 404 if user can't access
    obj = get_object_or_404(Object.objects.for_current_user(), pk=pk)
    return TemplateResponse(
        request,
        template="abac/object.html",
        context={'obj': obj}
    )

def user_accessible_objects(request, user_pk):
    """Show what objects a specific user can access"""
    user = get_object_or_404(FakeUser, pk=user_pk)

    # Explicitly filter for a specific subject
    accessible_objs = Object.objects.accessible_by(user)

    return TemplateResponse(
        request,
        template="abac/user_objects.html",
        context={'user': user, 'objects': accessible_objs}
    )

def admin_all_objects(request):
    """Admin view - see ALL objects regardless of clearance"""
    if not request.user.is_staff:
        return HttpResponseForbidden()

    # Explicit unfiltered access
    all_objs = Object.all_objects.all()

    return TemplateResponse(
        request,
        template="abac/admin_objects.html",
        context={'objects': all_objs}
    )
```

## Example: File System with MLS

```python
from django.db import models
from mls_core import MLSObject, MLSForeignKey

class FileSystem(MLSObject):
    """MLS-protected file system"""

    class FileType(models.TextChoices):
        FILE = 'FILE', 'File'
        DIRECTORY = 'DIR', 'Directory'

    name = models.CharField(max_length=255)
    file_type = models.CharField(max_length=4, choices=FileType.choices)
    content = models.TextField(blank=True)
    parent = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE)

    # MLS control
    classification = MLSForeignKey(
        'abac.Security',
        mls_control=True,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return self.name

# Usage:
# Only accessible files for current user
files = FileSystem.objects.for_current_user()

# Check if user can access a specific file
user = FakeUser.objects.get(name='Alice')
file = FileSystem.all_objects.get(name='secret.txt')
if user.can_access(file):
    print(file.content)
```

## Example: Database with Row and Column Level Security

```python
from django.db import models
from mls_core import MLSObject, MLSForeignKey

class DatabaseTable(models.Model):
    """Not MLS protected - just a container"""
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name

class DatabaseRow(MLSObject):
    """MLS protected at row level"""
    table = models.ForeignKey(DatabaseTable, on_delete=models.CASCADE)
    row_number = models.IntegerField()

    # Row-level classification
    classification = MLSForeignKey(
        'abac.Security',
        mls_control=True,
        on_delete=models.CASCADE,
        related_name='protected_rows'
    )

class DatabaseColumn(MLSObject):
    """MLS protected at column level"""
    table = models.ForeignKey(DatabaseTable, on_delete=models.CASCADE)
    column_name = models.CharField(max_length=100)

    # Column-level classification
    classification = MLSForeignKey(
        'abac.Security',
        mls_control=True,
        on_delete=models.CASCADE,
        related_name='protected_columns'
    )

class DatabaseCell(MLSObject):
    """MLS protected at cell level (most granular)"""
    row = models.ForeignKey(DatabaseRow, on_delete=models.CASCADE)
    column = models.ForeignKey(DatabaseColumn, on_delete=models.CASCADE)
    value = models.TextField()

    # Cell-level classification (most restrictive)
    classification = MLSForeignKey(
        'abac.Security',
        mls_control=True,
        on_delete=models.CASCADE,
        related_name='protected_cells'
    )

    class Meta:
        unique_together = ['row', 'column']

# Usage:
def get_table_data(user, table_name):
    """Get all accessible data from a table for a user"""
    table = DatabaseTable.objects.get(name=table_name)

    # Get accessible rows
    rows = DatabaseRow.objects.accessible_by(user).filter(table=table)

    # Get accessible columns
    columns = DatabaseColumn.objects.accessible_by(user).filter(table=table)

    # Get accessible cells (must be in accessible rows AND columns)
    cells = DatabaseCell.objects.accessible_by(user).filter(
        row__in=rows,
        column__in=columns
    )

    return {
        'rows': rows,
        'columns': columns,
        'cells': cells
    }
```

## Example: Network Resources

```python
from django.db import models
from mls_core import MLSSubject, MLSObject, MLSForeignKey

class NetworkNode(MLSSubject):
    """A network node that can access resources"""
    hostname = models.CharField(max_length=255)
    ip_address = models.GenericIPAddressField()
    clearances = models.OneToOneField('abac.Security', on_delete=models.CASCADE)

    def __str__(self):
        return f"{self.hostname} ({self.ip_address})"

class NetworkResource(MLSObject):
    """Protected network resource"""

    class ResourceType(models.TextChoices):
        SERVER = 'SRV', 'Server'
        DATABASE = 'DB', 'Database'
        API = 'API', 'API Endpoint'
        FILE = 'FILE', 'File Share'

    name = models.CharField(max_length=255)
    resource_type = models.CharField(max_length=4, choices=ResourceType.choices)
    url = models.URLField()

    classification = MLSForeignKey(
        'abac.Security',
        mls_control=True,
        on_delete=models.CASCADE
    )

    def __str__(self):
        return f"{self.name} ({self.resource_type})"

# Usage:
def can_node_access_resource(node, resource):
    """Check if a network node can access a resource"""
    return node.can_access(resource)

def get_accessible_apis(node):
    """Get all APIs accessible to a network node"""
    return NetworkResource.objects.accessible_by(node).filter(
        resource_type=NetworkResource.ResourceType.API
    )
```

## Example: Testing MLS Access Control

```python
from django.test import TestCase
from abac.models import Label, Security, FakeUser, Object

class MLSAccessTestCase(TestCase):
    def setUp(self):
        # Create labels
        self.unclassified = Label.objects.create(
            short_code="U",
            name="Unclassified",
            label_type=Label.LabelType.LEVEL
        )
        self.secret = Label.objects.create(
            short_code="S",
            name="Secret",
            label_type=Label.LabelType.LEVEL
        )
        self.top_secret = Label.objects.create(
            short_code="TS",
            name="Top Secret",
            label_type=Label.LabelType.LEVEL
        )

        # Create security clearances
        self.unclass_security = Security.objects.create()
        self.unclass_security.securities.add(self.unclassified)

        self.secret_security = Security.objects.create()
        self.secret_security.securities.add(self.unclassified, self.secret)

        self.ts_security = Security.objects.create()
        self.ts_security.securities.add(self.unclassified, self.secret, self.top_secret)

        # Create users
        self.low_user = FakeUser.objects.create(
            name="Low Clearance",
            accesses=self.unclass_security
        )
        self.med_user = FakeUser.objects.create(
            name="Medium Clearance",
            accesses=self.secret_security
        )
        self.high_user = FakeUser.objects.create(
            name="High Clearance",
            accesses=self.ts_security
        )

        # Create objects with different classifications
        self.public_obj = Object.objects.create(
            name="Public File",
            security=self.unclass_security
        )
        self.secret_obj = Object.objects.create(
            name="Secret File",
            security=self.secret_security
        )
        self.ts_obj = Object.objects.create(
            name="Top Secret File",
            security=self.ts_security
        )

    def test_low_user_access(self):
        """User with low clearance can only access unclassified"""
        accessible = Object.objects.accessible_by(self.low_user)
        self.assertEqual(accessible.count(), 1)
        self.assertIn(self.public_obj, accessible)

    def test_medium_user_access(self):
        """User with medium clearance can access unclassified and secret"""
        accessible = Object.objects.accessible_by(self.med_user)
        self.assertEqual(accessible.count(), 2)
        self.assertIn(self.public_obj, accessible)
        self.assertIn(self.secret_obj, accessible)
        self.assertNotIn(self.ts_obj, accessible)

    def test_high_user_access(self):
        """User with high clearance can access everything"""
        accessible = Object.objects.accessible_by(self.high_user)
        self.assertEqual(accessible.count(), 3)

    def test_can_access_method(self):
        """Test the can_access() method"""
        self.assertTrue(self.high_user.can_access(self.ts_obj))
        self.assertFalse(self.low_user.can_access(self.ts_obj))
        self.assertTrue(self.med_user.can_access(self.secret_obj))

    def test_accessible_by_method(self):
        """Test the accessible_by() method on objects"""
        self.assertTrue(self.public_obj.accessible_by(self.low_user))
        self.assertFalse(self.ts_obj.accessible_by(self.low_user))
        self.assertTrue(self.ts_obj.accessible_by(self.high_user))
```

## Tips for Migration

1. **Start Small**: Migrate one model at a time
2. **Test Thoroughly**: Write tests before and after migration
3. **Update Views Gradually**: Start with `for_current_user()` then optimize
4. **Keep Unfiltered Access**: Use `all_objects` for admin views
5. **Document Changes**: Note which models have MLS protection enabled
