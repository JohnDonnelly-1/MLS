"""
Example Wiki Views - Demonstrates Classification Helper Integration

This shows how to integrate the classification helper into your save workflow.
Copy this pattern to your own views.
"""

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from .example_wiki import WikiPage
from .models import SecurityClearance, SecurityLabel


@login_required
def wiki_create(request):
    """
    Create a new wiki page with classification.

    Flow:
    1. User fills out wiki form
    2. On save, redirect to classification helper
    3. Classification helper posts back to this view with selected labels
    4. Save wiki page with classification
    """

    if request.method == 'POST':
        # Check if this is coming back from classification helper
        if request.POST.get('classification_selected'):
            # Get the selected labels from classification helper
            selected_label_ids = request.POST.get('selected_label_ids', '').split(',')
            selected_label_ids = [int(id) for id in selected_label_ids if id]

            if not selected_label_ids:
                messages.error(request, 'Please select at least a classification level.')
                return redirect('mls_core:classification_helper')

            # Create or get a clearance for these labels
            labels = SecurityLabel.objects.filter(id__in=selected_label_ids)
            clearance_name = f"WIKI_{request.POST.get('title', 'PAGE')}_{labels.count()}LABELS"

            # Try to find existing clearance with same labels
            clearance = None
            for existing in SecurityClearance.objects.all():
                existing_label_ids = set(existing.securities.values_list('id', flat=True))
                if existing_label_ids == set(selected_label_ids):
                    clearance = existing
                    break

            # Create new clearance if not found
            if not clearance:
                clearance = SecurityClearance.objects.create(
                    name=clearance_name,
                    description=f"Auto-generated for wiki page classification"
                )
                clearance.securities.set(labels)

            # Now create the wiki page
            wiki_page = WikiPage.objects.create(
                title=request.POST['title'],
                slug=request.POST['slug'],
                content=request.POST['content'],
                classification=clearance,
                created_by=request.user,
                updated_by=request.user
            )

            messages.success(request, f'Wiki page "{wiki_page.title}" created successfully.')
            return redirect('mls_core:wiki_detail', wiki_page.id)

        else:
            # First form submission - store data in session and redirect to classifier
            request.session['wiki_draft'] = {
                'title': request.POST.get('title'),
                'slug': request.POST.get('slug'),
                'content': request.POST.get('content'),
            }

            # Build classification helper URL
            classify_url = reverse('mls_core:classification_helper')
            classify_url += f'?return_url={reverse("mls_core:wiki_create")}'

            return redirect(classify_url)

    # GET request - show form
    # Restore draft from session if available
    draft = request.session.pop('wiki_draft', {})

    context = {
        'draft': draft,
    }
    return render(request, 'mls_core/wiki_create.html', context)


@login_required
def wiki_edit(request, page_id):
    """
    Edit an existing wiki page.

    Shows how to pre-populate classification helper with existing classification.
    """
    wiki_page = get_object_or_404(WikiPage, pk=page_id)

    # Check MLS access
    if not wiki_page.accessible_by(request.user):
        messages.error(request, 'You do not have clearance to access this page.')
        return redirect('mls_core:wiki_list')

    if request.method == 'POST':
        # Check if this is coming back from classification helper
        if request.POST.get('classification_selected'):
            # Update classification
            selected_label_ids = request.POST.get('selected_label_ids', '').split(',')
            selected_label_ids = [int(id) for id in selected_label_ids if id]

            if selected_label_ids:
                labels = SecurityLabel.objects.filter(id__in=selected_label_ids)

                # Try to find existing clearance
                clearance = None
                for existing in SecurityClearance.objects.all():
                    existing_label_ids = set(existing.securities.values_list('id', flat=True))
                    if existing_label_ids == set(selected_label_ids):
                        clearance = existing
                        break

                if not clearance:
                    clearance_name = f"WIKI_{wiki_page.title}_{labels.count()}LABELS_V{wiki_page.version + 1}"
                    clearance = SecurityClearance.objects.create(
                        name=clearance_name,
                        description=f"Auto-generated for wiki page update"
                    )
                    clearance.securities.set(labels)

                wiki_page.classification = clearance

            # Update content
            wiki_page.title = request.POST['title']
            wiki_page.slug = request.POST['slug']
            wiki_page.content = request.POST['content']
            wiki_page.updated_by = request.user
            wiki_page.version += 1
            wiki_page.save()

            messages.success(request, f'Wiki page "{wiki_page.title}" updated successfully.')
            return redirect('mls_core:wiki_detail', wiki_page.id)

        else:
            # Store draft and redirect to classifier
            request.session['wiki_edit_draft'] = {
                'page_id': page_id,
                'title': request.POST.get('title'),
                'slug': request.POST.get('slug'),
                'content': request.POST.get('content'),
            }

            # Redirect to classification helper with existing classification
            classify_url = reverse('mls_core:classification_helper')
            classify_url += f'?existing_clearance_id={wiki_page.classification.id}'
            classify_url += f'&return_url={reverse("mls_core:wiki_edit", args=[page_id])}'

            # Add parent inheritance option if available
            if wiki_page.parent_page:
                classify_url += f'&inherit_from_id={wiki_page.parent_page.classification.id}'

            return redirect(classify_url)

    # GET request - show form
    draft = request.session.pop('wiki_edit_draft', None)
    if draft and draft['page_id'] == page_id:
        # Use draft data
        context = {
            'wiki_page': wiki_page,
            'draft': draft,
        }
    else:
        context = {
            'wiki_page': wiki_page,
        }

    return render(request, 'mls_core/wiki_edit.html', context)


@login_required
def wiki_detail(request, page_id):
    """View a wiki page."""
    wiki_page = get_object_or_404(WikiPage, pk=page_id)

    # Check MLS access
    if not wiki_page.accessible_by(request.user):
        messages.error(request, 'You do not have clearance to access this page.')
        return redirect('mls_core:wiki_list')

    context = {
        'wiki_page': wiki_page,
        'classification_marking': wiki_page.get_classification_marking(),
    }
    return render(request, 'mls_core/wiki_detail.html', context)


@login_required
def wiki_list(request):
    """List all wiki pages accessible to current user."""
    # MLS filtering happens automatically via MLSManager
    wiki_pages = WikiPage.objects.select_related('classification', 'created_by').all()

    context = {
        'wiki_pages': wiki_pages,
    }
    return render(request, 'mls_core/wiki_list.html', context)
