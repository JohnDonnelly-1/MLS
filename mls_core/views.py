"""
Views for MLS Core security management.

Permissions required:
- security_manager: Can edit security profiles, assign labels to users/groups
- senior_security_manager: Can CRUD labels, groups, and manage all security objects
"""

from django.core.management import call_command
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib.auth.models import User
from django.contrib import messages
from django.db.models import Q, Count
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_POST

from .models import (
    SecurityLabel,
    SecurityClearance,
    SecurityProfile,
    MLSGroup,
    DACGroup
)


# ==================== Dashboard ====================

@login_required
def dashboard(request):
    """
    MLS Core dashboard - shows overview of security system.
    """
    context = {
        'total_users': SecurityProfile.objects.count(),
        'total_labels': SecurityLabel.objects.count(),
        'total_clearances': SecurityClearance.objects.count(),
        'total_mls_groups': MLSGroup.objects.count(),
        'total_dac_groups': DACGroup.objects.count(),
        'user_profile': getattr(request.user, 'security_profile', None),
    }
    return render(request, 'mls_core/dashboard.html', context)


@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
@require_POST
def setup_sample_labels(request):
    """Seed the demo security labels (idempotent - get_or_create under the hood)."""
    call_command('setup_sample_labels')
    messages.success(request, 'Sample security labels created (or already existed).')
    return redirect('mls_core:dashboard')


# ==================== Security Profile Management ====================

@login_required
@permission_required('mls_core.security_manager', raise_exception=True)
def profile_list(request):
    """
    List all security profiles.
    Requires: security_manager permission
    """
    profiles = SecurityProfile.objects.select_related('user', 'clearances').prefetch_related(
        'mls_groups', 'dac_groups'
    )

    # Filter by search query
    query = request.GET.get('q')
    if query:
        profiles = profiles.filter(
            Q(user__username__icontains=query) |
            Q(user__first_name__icontains=query) |
            Q(user__last_name__icontains=query)
        )

    context = {
        'profiles': profiles,
        'query': query,
    }
    return render(request, 'mls_core/profile_list.html', context)


@login_required
@permission_required('mls_core.security_manager', raise_exception=True)
def profile_detail(request, profile_id):
    """
    View details of a security profile.
    Shows all clearances, groups, and effective permissions.
    """
    profile = get_object_or_404(
        SecurityProfile.objects.select_related('user', 'clearances').prefetch_related(
            'mls_groups__clearance_template__securities',
            'dac_groups'
        ),
        pk=profile_id
    )

    # Get all effective labels
    all_labels = profile.get_all_labels()

    # Get all effective DAC groups
    all_dac_groups = profile.get_all_dac_groups()

    context = {
        'profile': profile,
        'all_labels': all_labels,
        'all_dac_groups': all_dac_groups,
    }
    return render(request, 'mls_core/profile_detail.html', context)


@login_required
@permission_required('mls_core.security_manager', raise_exception=True)
def profile_edit(request, profile_id):
    """
    Edit a security profile.
    Allows assigning clearances, MLS groups, and DAC groups.
    """
    profile = get_object_or_404(SecurityProfile, pk=profile_id)

    if request.method == 'POST':
        # Update clearance
        clearance_id = request.POST.get('clearances')
        if clearance_id:
            profile.clearances = SecurityClearance.objects.get(pk=clearance_id)
        else:
            profile.clearances = None

        # Update MLS groups
        mls_group_ids = request.POST.getlist('mls_groups')
        profile.mls_groups.set(mls_group_ids)

        # Update DAC groups
        dac_group_ids = request.POST.getlist('dac_groups')
        profile.dac_groups.set(dac_group_ids)

        # Update other fields
        profile.is_active = request.POST.get('is_active') == 'on'
        profile.notes = request.POST.get('notes', '')
        clearance_expires = request.POST.get('clearance_expires')
        if clearance_expires:
            profile.clearance_expires = clearance_expires
        else:
            profile.clearance_expires = None

        profile.save()
        messages.success(request, f'Security profile for {profile.user.username} updated successfully.')
        return redirect('mls_core:profile_detail', profile_id=profile.id)

    # GET request - show form
    context = {
        'profile': profile,
        'all_clearances': SecurityClearance.objects.all(),
        'all_mls_groups': MLSGroup.objects.filter(is_active=True),
        'all_dac_groups': DACGroup.objects.filter(is_active=True),
    }
    return render(request, 'mls_core/profile_edit.html', context)


@login_required
@permission_required('mls_core.security_manager', raise_exception=True)
def profile_create_select_user(request):
    """
    Select a user to create a security profile for.
    """
    # Get all users without security profiles
    users_with_profiles = SecurityProfile.objects.values_list('user_id', flat=True)
    users_without_profiles = User.objects.exclude(id__in=users_with_profiles).order_by('username')

    context = {
        'users': users_without_profiles,
    }
    return render(request, 'mls_core/profile_create_select_user.html', context)


@login_required
@permission_required('mls_core.security_manager', raise_exception=True)
def profile_create(request, user_id):
    """
    Create a security profile for an existing Django user.
    """
    user = get_object_or_404(User, pk=user_id)

    # Check if profile already exists
    if hasattr(user, 'security_profile'):
        messages.warning(request, f'{user.username} already has a security profile.')
        return redirect('mls_core:profile_detail', profile_id=user.security_profile.id)

    if request.method == 'POST':
        profile = SecurityProfile.objects.create(user=user)

        # Set clearance if selected
        clearance_id = request.POST.get('clearances')
        if clearance_id:
            profile.clearances = SecurityClearance.objects.get(pk=clearance_id)

        # Set MLS groups
        mls_group_ids = request.POST.getlist('mls_groups')
        profile.mls_groups.set(mls_group_ids)

        # Set DAC groups
        dac_group_ids = request.POST.getlist('dac_groups')
        profile.dac_groups.set(dac_group_ids)

        profile.notes = request.POST.get('notes', '')
        profile.save()

        messages.success(request, f'Security profile created for {user.username}.')
        return redirect('mls_core:profile_detail', profile_id=profile.id)

    # GET request - show form
    context = {
        'user': user,
        'all_clearances': SecurityClearance.objects.all(),
        'all_mls_groups': MLSGroup.objects.filter(is_active=True),
        'all_dac_groups': DACGroup.objects.filter(is_active=True),
    }
    return render(request, 'mls_core/profile_create.html', context)


@login_required
@permission_required('mls_core.security_manager', raise_exception=True)
def profile_delete(request, profile_id):
    """
    Delete a security profile.
    """
    profile = get_object_or_404(SecurityProfile, pk=profile_id)

    if request.method == 'POST':
        username = profile.user.username
        profile.delete()
        messages.success(request, f'Security profile for {username} has been deleted.')
        return redirect('mls_core:profile_list')

    context = {
        'profile': profile,
    }
    return render(request, 'mls_core/profile_delete.html', context)


# ==================== Security Label Management ====================

@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def label_list(request):
    """
    List all security labels.
    Requires: senior_security_manager permission
    """
    labels = SecurityLabel.objects.all()

    label_type = request.GET.get('type')
    if label_type:
        labels = labels.filter(label_type=label_type)

    context = {
        'level_labels': labels.filter(label_type=SecurityLabel.LabelType.LEVEL).order_by('rank'),
        'category_labels': labels.filter(label_type=SecurityLabel.LabelType.CATEGORY).order_by('short_code'),
        'label_types': SecurityLabel.LabelType.choices,
        'selected_type': label_type,
    }
    return render(request, 'mls_core/label_list.html', context)


@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def label_create(request):
    """Create a new security label."""
    if request.method == 'POST':
        label = SecurityLabel.objects.create(
            short_code=request.POST['short_code'],
            name=request.POST['name'],
            label_type=request.POST['label_type'],
            rank=int(request.POST.get('rank', 0)),
            description=request.POST.get('description', ''),
            color=request.POST.get('color', '#808080'),
        )
        messages.success(request, f'Security label "{label.name}" created successfully.')
        return redirect('mls_core:label_list')

    context = {
        'label_types': SecurityLabel.LabelType.choices,
    }
    return render(request, 'mls_core/label_create.html', context)


@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def label_edit(request, label_id):
    """Edit a security label."""
    label = get_object_or_404(SecurityLabel, pk=label_id)

    if request.method == 'POST':
        label.short_code = request.POST['short_code']
        label.name = request.POST['name']
        label.label_type = request.POST['label_type']
        label.rank = int(request.POST.get('rank', 0))
        label.description = request.POST.get('description', '')
        label.color = request.POST.get('color', '#808080')
        label.save()

        messages.success(request, f'Security label "{label.name}" updated successfully.')
        return redirect('mls_core:label_list')

    context = {
        'label': label,
        'label_types': SecurityLabel.LabelType.choices,
    }
    return render(request, 'mls_core/label_edit.html', context)


@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def label_delete(request, label_id):
    """Delete a security label."""
    label = get_object_or_404(SecurityLabel, pk=label_id)

    if request.method == 'POST':
        label_name = label.name
        label.delete()
        messages.success(request, f'Security label "{label_name}" deleted successfully.')
        return redirect('mls_core:label_list')

    context = {'label': label}
    return render(request, 'mls_core/label_delete.html', context)


# ==================== MLS Group Management ====================

@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def mls_group_list(request):
    """List all MLS groups."""
    groups = MLSGroup.objects.select_related('clearance_template').prefetch_related('parent_groups')
    context = {'groups': groups}
    return render(request, 'mls_core/mls_group_list.html', context)


@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def mls_group_create(request):
    """Create a new MLS group."""
    if request.method == 'POST':
        # Get or create clearance
        clearance_id = request.POST.get('clearance_template')
        clearance = SecurityClearance.objects.get(pk=clearance_id)

        group = MLSGroup.objects.create(
            name=request.POST['name'],
            description=request.POST.get('description', ''),
            clearance_template=clearance,
        )

        # Set parent groups
        parent_group_ids = request.POST.getlist('parent_groups')
        group.parent_groups.set(parent_group_ids)

        messages.success(request, f'MLS group "{group.name}" created successfully.')
        return redirect('mls_core:mls_group_list')

    context = {
        'clearances': SecurityClearance.objects.all(),
        'all_groups': MLSGroup.objects.all(),
    }
    return render(request, 'mls_core/mls_group_create.html', context)


@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def mls_group_edit(request, group_id):
    """Edit an MLS group."""
    group = get_object_or_404(MLSGroup, pk=group_id)

    if request.method == 'POST':
        group.name = request.POST['name']
        group.description = request.POST.get('description', '')
        group.is_active = request.POST.get('is_active') == 'on'

        clearance_id = request.POST.get('clearance_template')
        group.clearance_template = SecurityClearance.objects.get(pk=clearance_id)

        group.save()

        # Update parent groups
        parent_group_ids = request.POST.getlist('parent_groups')
        group.parent_groups.set(parent_group_ids)

        messages.success(request, f'MLS group "{group.name}" updated successfully.')
        return redirect('mls_core:mls_group_list')

    context = {
        'group': group,
        'clearances': SecurityClearance.objects.all(),
        'all_groups': MLSGroup.objects.exclude(pk=group.id),  # Exclude self to prevent circular reference
    }
    return render(request, 'mls_core/mls_group_edit.html', context)


@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def mls_group_delete(request, group_id):
    """Delete an MLS group."""
    group = get_object_or_404(MLSGroup, pk=group_id)

    if request.method == 'POST':
        group_name = group.name
        group.delete()
        messages.success(request, f'MLS group "{group_name}" deleted successfully.')
        return redirect('mls_core:mls_group_list')

    context = {'group': group}
    return render(request, 'mls_core/mls_group_delete.html', context)


# ==================== DAC Group Management ====================

@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def dac_group_list(request):
    """List all DAC groups."""
    groups = DACGroup.objects.prefetch_related('parent_groups')
    context = {'groups': groups}
    return render(request, 'mls_core/dac_group_list.html', context)


@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def dac_group_create(request):
    """Create a new DAC group."""
    if request.method == 'POST':
        group = DACGroup.objects.create(
            name=request.POST['name'],
            description=request.POST.get('description', ''),
        )

        # Set parent groups
        parent_group_ids = request.POST.getlist('parent_groups')
        group.parent_groups.set(parent_group_ids)

        messages.success(request, f'DAC group "{group.name}" created successfully.')
        return redirect('mls_core:dac_group_list')

    context = {
        'all_groups': DACGroup.objects.all(),
    }
    return render(request, 'mls_core/dac_group_create.html', context)


@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def dac_group_edit(request, group_id):
    """Edit a DAC group."""
    group = get_object_or_404(DACGroup, pk=group_id)

    if request.method == 'POST':
        group.name = request.POST['name']
        group.description = request.POST.get('description', '')
        group.is_active = request.POST.get('is_active') == 'on'
        group.save()

        # Update parent groups
        parent_group_ids = request.POST.getlist('parent_groups')
        group.parent_groups.set(parent_group_ids)

        messages.success(request, f'DAC group "{group.name}" updated successfully.')
        return redirect('mls_core:dac_group_list')

    context = {
        'group': group,
        'all_groups': DACGroup.objects.exclude(pk=group.id),  # Exclude self to prevent circular reference
    }
    return render(request, 'mls_core/dac_group_edit.html', context)


@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def dac_group_delete(request, group_id):
    """Delete a DAC group."""
    group = get_object_or_404(DACGroup, pk=group_id)

    if request.method == 'POST':
        group_name = group.name
        group.delete()
        messages.success(request, f'DAC group "{group_name}" deleted successfully.')
        return redirect('mls_core:dac_group_list')

    context = {'group': group}
    return render(request, 'mls_core/dac_group_delete.html', context)


# ==================== Security Clearance Management ====================

@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def clearance_list(request):
    """List all security clearances."""
    clearances = SecurityClearance.objects.prefetch_related('securities')
    context = {'clearances': clearances}
    return render(request, 'mls_core/clearance_list.html', context)


@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def clearance_create(request):
    """Create a new security clearance."""
    if request.method == 'POST':
        clearance = SecurityClearance.objects.create(
            name=request.POST['name'],
            description=request.POST.get('description', ''),
        )

        # Set securities (labels)
        label_ids = request.POST.getlist('securities')
        clearance.securities.set(label_ids)

        messages.success(request, f'Security clearance "{clearance.name}" created successfully.')
        return redirect('mls_core:clearance_list')

    context = {
        'level_labels': SecurityLabel.objects.filter(label_type=SecurityLabel.LabelType.LEVEL).order_by('rank'),
        'category_labels': SecurityLabel.objects.filter(label_type=SecurityLabel.LabelType.CATEGORY).order_by('short_code'),
    }
    return render(request, 'mls_core/clearance_create.html', context)


@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def clearance_edit(request, clearance_id):
    """Edit a security clearance."""
    clearance = get_object_or_404(SecurityClearance, pk=clearance_id)

    if request.method == 'POST':
        clearance.name = request.POST['name']
        clearance.description = request.POST.get('description', '')
        clearance.save()

        # Update securities (labels)
        label_ids = request.POST.getlist('securities')
        clearance.securities.set(label_ids)

        messages.success(request, f'Security clearance "{clearance.name}" updated successfully.')
        return redirect('mls_core:clearance_list')

    context = {
        'clearance': clearance,
        'level_labels': SecurityLabel.objects.filter(label_type=SecurityLabel.LabelType.LEVEL).order_by('rank'),
        'category_labels': SecurityLabel.objects.filter(label_type=SecurityLabel.LabelType.CATEGORY).order_by('short_code'),
        'checked_ids': set(clearance.securities.values_list('id', flat=True)),
    }
    return render(request, 'mls_core/clearance_edit.html', context)


@login_required
@permission_required('mls_core.senior_security_manager', raise_exception=True)
def clearance_delete(request, clearance_id):
    """Delete a security clearance."""
    clearance = get_object_or_404(SecurityClearance, pk=clearance_id)

    if request.method == 'POST':
        clearance_name = clearance.name
        clearance.delete()
        messages.success(request, f'Security clearance "{clearance_name}" deleted successfully.')
        return redirect('mls_core:clearance_list')

    context = {'clearance': clearance}
    return render(request, 'mls_core/clearance_delete.html', context)


# ==================== Classification Helper ====================

@login_required
def classification_helper(request):
    """
    Interactive classification helper for labeling objects.

    Returns a modal interface for selecting security labels organized by type:
    - Classification Level (single selection, hierarchical)
    - SCI Caveats (multiple selection, categories)
    - SAP Access (multiple selection, categories)
    - Dissemination Controls (multiple selection, categories)

    Query parameters:
    - existing_clearance_id: Pre-populate with existing clearance
    - inherit_from_id: Show option to inherit from parent object
    - return_url: Where to redirect after classification
    """
    # Get all labels organized by type
    levels = SecurityLabel.objects.filter(label_type='LVL').order_by('rank')

    # Get categories - organize by naming convention
    all_categories = SecurityLabel.objects.filter(label_type='CAT').order_by('short_code')

    # Organize categories by prefix/type
    sci_caveats = all_categories.filter(short_code__istartswith='SCI').order_by('short_code')

    # Dissemination controls (predefined list)
    dissemination = all_categories.filter(
        short_code__in=['NOFORN', 'ORCON', 'PROPIN', 'RELTO', 'FOUO', 'LES']
    ).order_by('short_code')

    # SAP Access - everything that starts with SAP OR anything not SCI/dissemination (treat "additional" as SAP)
    excluded_codes = list(sci_caveats.values_list('short_code', flat=True)) + \
                     list(dissemination.values_list('short_code', flat=True))
    sap_access = all_categories.exclude(short_code__in=excluded_codes).order_by('short_code')

    # No separate "other_categories" - everything goes into SAP
    other_categories = None

    # Get existing classification if provided
    existing_clearance = None
    existing_labels = []
    existing_level = None
    if request.GET.get('existing_clearance_id'):
        try:
            existing_clearance = SecurityClearance.objects.get(pk=request.GET['existing_clearance_id'])
            existing_labels = list(existing_clearance.securities.values_list('id', flat=True))
            existing_level_qs = existing_clearance.securities.filter(label_type='LVL')
            if existing_level_qs.exists():
                existing_level = existing_level_qs.first().id
        except SecurityClearance.DoesNotExist:
            pass

    # Get inherit option if provided
    inherit_clearance = None
    if request.GET.get('inherit_from_id'):
        try:
            inherit_clearance = SecurityClearance.objects.get(pk=request.GET['inherit_from_id'])
        except SecurityClearance.DoesNotExist:
            pass

    context = {
        'levels': levels,
        'sci_caveats': sci_caveats,
        'sap_access': sap_access,
        'dissemination': dissemination,
        'other_categories': other_categories,
        'existing_clearance': existing_clearance,
        'existing_labels': existing_labels,
        'existing_level': existing_level,
        'inherit_clearance': inherit_clearance,
        'return_url': request.GET.get('return_url', '/'),
    }

    return render(request, 'mls_core/classification_helper.html', context)
