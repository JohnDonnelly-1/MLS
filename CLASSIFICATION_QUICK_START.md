## Classification Helper - Quick Start

### Access the Helper

```
http://localhost:8000/mls/classify/
```

### Setup: Create Sample Labels

```python
docker-compose exec web python manage.py shell
```

```python
from mls_core.models import SecurityLabel

# Classification Levels
SecurityLabel.objects.create(short_code="UNCLASS", name="Unclassified", label_type="LVL", rank=0, color="#008000")
SecurityLabel.objects.create(short_code="CONFIDENTIAL", name="Confidential", label_type="LVL", rank=1, color="#0000FF")
SecurityLabel.objects.create(short_code="SECRET", name="Secret", label_type="LVL", rank=2, color="#FFA500")
SecurityLabel.objects.create(short_code="TS", name="Top Secret", label_type="LVL", rank=3, color="#FF0000")

# SCI Caveats
SecurityLabel.objects.create(short_code="SCI-TK", name="Talent Keyhole", label_type="CAT", color="#800080")
SecurityLabel.objects.create(short_code="SCI-SI", name="Special Intelligence", label_type="CAT", color="#800080")
SecurityLabel.objects.create(short_code="SCI-G", name="Gamma", label_type="CAT", color="#800080")

# SAP
SecurityLabel.objects.create(short_code="SAP-ALPHA", name="SAP Alpha", label_type="CAT", color="#8B4513")
SecurityLabel.objects.create(short_code="SAP-BRAVO", name="SAP Bravo", label_type="CAT", color="#8B4513")

# Dissemination
SecurityLabel.objects.create(short_code="NOFORN", name="No Foreign Nationals", label_type="CAT", color="#FF6347")
SecurityLabel.objects.create(short_code="ORCON", name="Originator Controlled", label_type="CAT", color="#FF6347")
SecurityLabel.objects.create(short_code="PROPIN", name="Proprietary Information", label_type="CAT", color="#FF6347")
SecurityLabel.objects.create(short_code="FOUO", name="For Official Use Only", label_type="CAT", color="#FFD700")
```

### Integration Pattern

```python
# In your view:
from django.urls import reverse

def my_create_view(request):
    if request.method == 'POST':
        if request.POST.get('classification_selected'):
            # Coming back from classifier
            label_ids = request.POST.get('selected_label_ids', '').split(',')
            label_ids = [int(id) for id in label_ids if id]

            # Create clearance and save your object
            clearance = create_clearance(label_ids)
            my_obj.classification = clearance
            my_obj.save()
            return redirect('success')
        else:
            # First save - redirect to classifier
            request.session['draft'] = request.POST.dict()
            url = reverse('mls_core:classification_helper')
            url += f'?return_url={reverse("my_create_view")}'
            return redirect(url)
```

### URL Parameters

```python
# Edit with existing classification
url = f"/mls/classify/?existing_clearance_id={obj.classification.id}&return_url=/edit/"

# With inheritance option
url = f"/mls/classify/?inherit_from_id={parent.classification.id}&return_url=/create/"
```

### Display Classification Marking

```python
# In your model:
def get_marking(self):
    labels = self.classification.securities.all().order_by('-rank')
    return "//".join([l.short_code for l in labels])
```

```html
<!-- In your template: -->
<div class="classification-banner">
    {{ object.get_marking }}
</div>
```

### Example Results

| Selection | Output Marking |
|-----------|---------------|
| TS + SCI-TK + NOFORN | `TS//SCI-TK//NOFORN` |
| SECRET + ORCON | `SECRET//ORCON` |
| CONFIDENTIAL + FOUO | `CONFIDENTIAL//FOUO` |

That's it! See `CLASSIFICATION_HELPER_GUIDE.md` for full documentation.
