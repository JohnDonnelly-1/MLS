# Classification Helper Guide

## Overview

The Classification Helper is an interactive UI for applying security markings to files, database entries, wiki pages, documents, and any other objects that need MLS classification.

**Access:** `/mls/classify/`

## Features

✅ **Organized by Category:**
- Classification Level (hierarchical, single selection)
- SCI Caveats (Sensitive Compartmented Information)
- SAP Access (Special Access Programs)
- Dissemination Controls (NOFORN, ORCON, etc.)
- Additional Controls (other categories)

✅ **Live Preview:** See classification marking as you make selections

✅ **Inheritance Support:** Option to inherit classification from parent objects

✅ **Existing Classification:** Pre-populate with current classification when editing

## Label Organization

The classification helper automatically organizes security labels:

### Classification Levels (Single Selection)
- UNCLASSIFIED (rank=0)
- CONFIDENTIAL (rank=1)
- SECRET (rank=2)
- TOP SECRET (rank=3)

*Hierarchical - select the highest level that applies*

### SCI Caveats (Multiple Selection)
Labels with `short_code` starting with "SCI":
- SCI-GAMMA
- SCI-DELTA
- etc.

### SAP Access (Multiple Selection)
Labels with `short_code` starting with "SAP":
- SAP-ALPHA
- SAP-BETA
- etc.

### Dissemination Controls (Multiple Selection)
Predefined dissemination control codes:
- NOFORN (No Foreign Nationals)
- ORCON (Originator Controlled)
- PROPIN (Proprietary Information)
- RELTO (Releasable To)
- FOUO (For Official Use Only)
- LES (Law Enforcement Sensitive)

### Other Categories
Any other category labels that don't fit the above groups.

## Usage in Your Models

### Step 1: Create Your Model

```python
from django.db import models
from mls_core.models import MLSObject, SecurityClearance

class Document(MLSObject):
    title = models.CharField(max_length=200)
    content = models.TextField()

    # MLS classification field
    classification = models.ForeignKey(
        SecurityClearance,
        on_delete=models.PROTECT,
        related_name='classified_documents'
    )

    class Meta:
        mls_classification_field = 'classification'
```

### Step 2: Integrate Classification Helper in Your View

```python
from django.shortcuts import render, redirect
from django.urls import reverse

def document_create(request):
    if request.method == 'POST':
        # Check if returning from classification helper
        if request.POST.get('classification_selected'):
            # Get selected labels
            selected_label_ids = request.POST.get('selected_label_ids', '').split(',')
            selected_label_ids = [int(id) for id in selected_label_ids if id]

            # Create clearance from selected labels
            clearance = create_or_find_clearance(selected_label_ids)

            # Create your document
            doc = Document.objects.create(
                title=request.POST['title'],
                content=request.POST['content'],
                classification=clearance
            )
            return redirect('document_detail', doc.id)

        else:
            # First submission - save to session and redirect to classifier
            request.session['doc_draft'] = {
                'title': request.POST.get('title'),
                'content': request.POST.get('content'),
            }

            # Redirect to classification helper
            classify_url = reverse('mls_core:classification_helper')
            classify_url += f'?return_url={reverse("document_create")}'
            return redirect(classify_url)

    # GET request
    draft = request.session.pop('doc_draft', {})
    return render(request, 'document_create.html', {'draft': draft})
```

### Step 3: Helper Function for Creating Clearances

```python
from mls_core.models import SecurityClearance, SecurityLabel

def create_or_find_clearance(label_ids):
    """
    Find existing clearance with same labels or create new one.
    Reuses clearances to avoid duplicates.
    """
    if not label_ids:
        return None

    # Try to find existing clearance with exact same labels
    for existing in SecurityClearance.objects.all():
        existing_label_ids = set(existing.securities.values_list('id', flat=True))
        if existing_label_ids == set(label_ids):
            return existing

    # Create new clearance
    labels = SecurityLabel.objects.filter(id__in=label_ids)
    clearance_name = f"AUTO_{len(label_ids)}LABELS"

    clearance = SecurityClearance.objects.create(
        name=clearance_name,
        description="Auto-generated from classification helper"
    )
    clearance.securities.set(labels)

    return clearance
```

## Query Parameters

### `existing_clearance_id`
Pre-populate with existing classification (for editing):
```
/mls/classify/?existing_clearance_id=5&return_url=/wiki/edit/3/
```

### `inherit_from_id`
Show inheritance option from parent object:
```
/mls/classify/?inherit_from_id=3&return_url=/wiki/create/
```

### `return_url`
Where to POST the selected classification:
```
/mls/classify/?return_url=/documents/create/
```

## Return Data

When the classification helper POSTs back to your view:

**Form Fields:**
- `classification_selected`: "1" (indicates coming from helper)
- `selected_label_ids`: Comma-separated label IDs (e.g., "1,5,7,12")
- `classification_mode`: "inherit" or "custom" (if inheritance available)

**Your view should:**
1. Check for `classification_selected` in POST data
2. Parse `selected_label_ids`
3. Create or find matching SecurityClearance
4. Save your object with the clearance

## Example: Full Wiki Page Integration

See `example_wiki.py` and `example_wiki_views.py` for complete working examples including:

- Creating pages with classification
- Editing with existing classification
- Inheritance from parent pages
- Auto-save patterns with session storage
- Classification marking display

## Classification Display

### Get Classification Marking String

```python
def get_classification_marking(self):
    """Returns formatted marking like: SECRET//SCI//NOFORN"""
    labels = self.classification.securities.all().order_by('-rank', 'short_code')
    return "//".join([label.short_code for label in labels])
```

### Display in Templates

```html
<div class="classification-banner" style="background-color: #dc3545; color: white; padding: 10px; text-align: center; font-weight: bold;">
    {{ object.get_classification_marking }}
</div>
```

## Creating Appropriate Labels

For the classification helper to work best, create labels with appropriate naming:

### Levels
```python
SecurityLabel.objects.create(short_code="UNCLASS", name="Unclassified", label_type="LVL", rank=0, color="#008000")
SecurityLabel.objects.create(short_code="CONFIDENTIAL", name="Confidential", label_type="LVL", rank=1, color="#0000FF")
SecurityLabel.objects.create(short_code="SECRET", name="Secret", label_type="LVL", rank=2, color="#FFA500")
SecurityLabel.objects.create(short_code="TS", name="Top Secret", label_type="LVL", rank=3, color="#FF0000")
```

### SCI Caveats (prefix with "SCI")
```python
SecurityLabel.objects.create(short_code="SCI-TK", name="Talent Keyhole", label_type="CAT", color="#800080")
SecurityLabel.objects.create(short_code="SCI-SI", name="Special Intelligence", label_type="CAT", color="#800080")
```

### SAP (prefix with "SAP")
```python
SecurityLabel.objects.create(short_code="SAP-ALPHA", name="Special Access Program Alpha", label_type="CAT", color="#8B4513")
```

### Dissemination
```python
SecurityLabel.objects.create(short_code="NOFORN", name="Not Releasable to Foreign Nationals", label_type="CAT", color="#FF6347")
SecurityLabel.objects.create(short_code="ORCON", name="Originator Controlled", label_type="CAT", color="#FF6347")
```

## Testing

1. Create security labels using the examples above
2. Access `/mls/classify/` directly to test the UI
3. Try different combinations
4. Check the classification summary updates in real-time
5. Test inheritance option with parent objects

## Best Practices

1. **Reuse Clearances:** Always search for existing clearances with the same label combination before creating new ones
2. **Session Storage:** Use session storage to preserve form data during classification step
3. **Validation:** Validate that at least a classification level is selected
4. **Access Control:** Only allow authorized users to classify documents
5. **Audit Trail:** Log classification changes for compliance
6. **Display Markings:** Always show classification marking prominently on classified content

## Future Enhancements

Consider adding:
- DAC group selection in the classifier
- Classification change history
- Bulk classification operations
- Templates/presets for common classifications
- AI-suggested classifications based on content analysis
