"""
Wiki views.

Read access control is enforced by WikiPage.objects / WikiAttachment.objects
themselves (the MLS-filtered default manager) - most views below don't need
an explicit clearance check at all, since get_object_or_404() against the
default manager already 404s on anything the current user isn't cleared for.
Write actions (create/edit/delete/upload) require login only for now, per
the "not all the administrative features (yet)" scope of this app - there is
no additional clearance gate on *writing* content beyond being logged in.
"""

import difflib

import bleach
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils.text import slugify
from django.views.decorators.http import require_POST

from .classification import get_or_create_clearance, get_user_labels_grouped
from .models import Space, WikiAttachment, WikiPage, WikiRevision
from .sanitize import sanitize_page_html


# ==================== Helpers ====================

def _parse_label_ids(request):
    return [v for v in request.POST.getlist('label_ids') if v.strip()]


def _build_page_tree(pages):
    """
    Turn a flat, already-MLS-filtered list of pages into a nested tree
    (list of {'page': WikiPage, 'children': [...]}), pages the user can't
    see are simply absent from `pages` and therefore from the tree - a
    child of an invisible parent surfaces as its own top-level entry rather
    than disappearing, so nothing is silently hidden.
    """
    by_id = {page.pk: {'page': page, 'children': []} for page in pages}
    roots = []
    for page in pages:
        node = by_id[page.pk]
        parent_id = page.parent_id
        if parent_id and parent_id in by_id:
            by_id[parent_id]['children'].append(node)
        else:
            roots.append(node)
    return roots


def _get_page_or_404(space_key, page_slug):
    return get_object_or_404(
        WikiPage.objects.select_related('space', 'classification', 'created_by', 'updated_by'),
        space__key=space_key, slug=page_slug,
    )


# ==================== Home / Spaces ====================

@login_required
def wiki_home(request):
    space = Space.objects.order_by('name').first()
    if space:
        return redirect('wiki:space_detail', space_key=space.key)
    return render(request, 'wiki/space_list.html', {'spaces': [], 'no_spaces': True})


@login_required
def space_list(request):
    spaces = Space.objects.order_by('name')
    return render(request, 'wiki/space_list.html', {'spaces': spaces})


@login_required
def space_create(request):
    if request.method == 'POST':
        key = slugify(request.POST.get('key', ''))[:20].upper()
        name = request.POST.get('name', '').strip()
        if not key or not name:
            messages.error(request, 'A space needs both a key and a name.')
        elif Space.objects.filter(key=key).exists():
            messages.error(request, f'Space key "{key}" is already in use.')
        else:
            space = Space.objects.create(
                key=key,
                name=name,
                description=request.POST.get('description', '').strip(),
                icon=request.POST.get('icon', '').strip(),
                created_by=request.user,
            )
            messages.success(request, f'Space "{space.name}" created.')
            return redirect('wiki:space_detail', space_key=space.key)

    return render(request, 'wiki/space_form.html', {})


@login_required
def space_detail(request, space_key):
    space = get_object_or_404(Space, key=space_key)
    pages = list(
        WikiPage.objects
        .filter(space=space)
        .select_related('classification', 'updated_by')
        .order_by('title')
    )
    tree = _build_page_tree(pages)
    other_spaces = Space.objects.exclude(pk=space.pk).order_by('name')
    return render(request, 'wiki/space_detail.html', {
        'space': space,
        'tree': tree,
        'page_count': len(pages),
        'other_spaces': other_spaces,
    })


# ==================== Pages ====================

@login_required
def page_detail(request, space_key, page_slug):
    page = _get_page_or_404(space_key, page_slug)
    all_pages = list(WikiPage.objects.filter(space=page.space).select_related('classification'))
    tree = _build_page_tree(all_pages)
    attachments = page.attachments.select_related('classification', 'uploaded_by')
    levels, categories = get_user_labels_grouped(request.user)
    return render(request, 'wiki/page_detail.html', {
        'space': page.space,
        'page': page,
        'tree': tree,
        'attachments': attachments,
        'children': page.children.all(),
        'attach_levels': levels,
        'attach_categories': categories,
    })


@login_required
def page_create(request, space_key):
    space = get_object_or_404(Space, key=space_key)
    parent = None
    parent_id = request.GET.get('parent') or request.POST.get('parent')
    if parent_id:
        parent = get_object_or_404(WikiPage, pk=parent_id, space=space)

    levels, categories = get_user_labels_grouped(request.user)
    allowed_label_ids = set(levels.values_list('id', flat=True)) | set(categories.values_list('id', flat=True))

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        slug = slugify(request.POST.get('slug') or title)
        content_html = sanitize_page_html(request.POST.get('content_html', ''))
        label_ids = _parse_label_ids(request)
        clearance = get_or_create_clearance(label_ids, allowed_label_ids, name_hint=title)

        if not title or not slug:
            messages.error(request, 'A page needs a title.')
        elif not clearance:
            messages.error(request, 'Choose a classification level before saving.')
        elif WikiPage.objects.filter(space=space, slug=slug).exists() or \
                WikiPage.DANGER.filter(space=space, slug=slug).exists():
            messages.error(request, f'A page with slug "{slug}" already exists in this space.')
        else:
            page = WikiPage.objects.create(
                space=space, parent=parent, title=title, slug=slug,
                content_html=content_html, classification=clearance,
                created_by=request.user, updated_by=request.user,
            )
            WikiRevision.objects.create(
                page=page, version=1, title=title, content_html=content_html,
                classification=clearance, edited_by=request.user,
                change_note='Initial version',
            )
            messages.success(request, f'Page "{page.title}" created.')
            return redirect(page.get_absolute_url())

    return render(request, 'wiki/page_form.html', {
        'space': space,
        'parent': parent,
        'levels': levels,
        'categories': categories,
        'is_new': True,
    })


@login_required
def page_edit(request, space_key, page_slug):
    page = _get_page_or_404(space_key, page_slug)
    levels, categories = get_user_labels_grouped(request.user)
    allowed_label_ids = set(levels.values_list('id', flat=True)) | set(categories.values_list('id', flat=True))
    existing_label_ids = set(page.classification.securities.values_list('id', flat=True))

    if request.method == 'POST':
        title = request.POST.get('title', '').strip()
        content_html = sanitize_page_html(request.POST.get('content_html', ''))
        change_note = request.POST.get('change_note', '').strip()
        label_ids = _parse_label_ids(request)
        clearance = get_or_create_clearance(label_ids, allowed_label_ids, name_hint=title) or page.classification

        if not title:
            messages.error(request, 'A page needs a title.')
        else:
            page.title = title
            page.content_html = content_html
            page.classification = clearance
            page.updated_by = request.user
            page.current_version += 1
            page.save()

            WikiRevision.objects.create(
                page=page, version=page.current_version, title=title,
                content_html=content_html, classification=clearance,
                edited_by=request.user, change_note=change_note,
            )
            messages.success(request, f'Page "{page.title}" updated (v{page.current_version}).')
            return redirect(page.get_absolute_url())

    return render(request, 'wiki/page_form.html', {
        'space': page.space,
        'page': page,
        'levels': levels,
        'categories': categories,
        'existing_label_ids': existing_label_ids,
        'is_new': False,
    })


@login_required
@require_POST
def page_delete(request, space_key, page_slug):
    page = _get_page_or_404(space_key, page_slug)
    space = page.space
    title = page.title
    page.delete()
    messages.success(request, f'Page "{title}" deleted.')
    return redirect('wiki:space_detail', space_key=space.key)


# ==================== History / diff / restore ====================

@login_required
def page_history(request, space_key, page_slug):
    page = _get_page_or_404(space_key, page_slug)
    revisions = page.revisions.select_related('edited_by', 'classification')
    return render(request, 'wiki/page_history.html', {
        'space': page.space, 'page': page, 'revisions': revisions,
    })


@login_required
def page_revision_detail(request, space_key, page_slug, version):
    page = _get_page_or_404(space_key, page_slug)
    revision = get_object_or_404(WikiRevision, page=page, version=version)
    return render(request, 'wiki/page_revision_detail.html', {
        'space': page.space, 'page': page, 'revision': revision,
    })


def _diff_html(old_html, new_html):
    """Word-level inline diff (old struck through, new inserted) for readability."""
    old_words = (old_html or '').split()
    new_words = (new_html or '').split()
    matcher = difflib.SequenceMatcher(a=old_words, b=new_words)
    parts = []
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == 'equal':
            parts.append(' '.join(new_words[j1:j2]))
        else:
            if i1 != i2:
                parts.append(f'<del>{" ".join(old_words[i1:i2])}</del>')
            if j1 != j2:
                parts.append(f'<ins>{" ".join(new_words[j1:j2])}</ins>')
    return ' '.join(parts)


@login_required
def page_diff(request, space_key, page_slug, from_version, to_version):
    page = _get_page_or_404(space_key, page_slug)
    from_rev = get_object_or_404(WikiRevision, page=page, version=from_version)
    to_rev = get_object_or_404(WikiRevision, page=page, version=to_version)

    from_text = bleach.clean(from_rev.content_html, tags=set(), strip=True)
    to_text = bleach.clean(to_rev.content_html, tags=set(), strip=True)

    return render(request, 'wiki/page_diff.html', {
        'space': page.space, 'page': page,
        'from_rev': from_rev, 'to_rev': to_rev,
        'diff_html': _diff_html(from_text, to_text),
        'title_changed': from_rev.title != to_rev.title,
        'classification_changed': from_rev.classification_id != to_rev.classification_id,
    })


@login_required
@require_POST
def page_restore(request, space_key, page_slug, version):
    page = _get_page_or_404(space_key, page_slug)
    old_revision = get_object_or_404(WikiRevision, page=page, version=version)

    page.title = old_revision.title
    page.content_html = old_revision.content_html
    page.classification = old_revision.classification
    page.updated_by = request.user
    page.current_version += 1
    page.save()

    WikiRevision.objects.create(
        page=page, version=page.current_version, title=page.title,
        content_html=page.content_html, classification=page.classification,
        edited_by=request.user, change_note=f'Restored from v{old_revision.version}',
    )
    messages.success(request, f'Restored v{old_revision.version} as the new current version (v{page.current_version}).')
    return redirect(page.get_absolute_url())


# ==================== Attachments ====================

@login_required
@require_POST
def attachment_upload(request, space_key, page_slug):
    page = _get_page_or_404(space_key, page_slug)
    uploaded = request.FILES.get('file')
    levels, categories = get_user_labels_grouped(request.user)
    allowed_label_ids = set(levels.values_list('id', flat=True)) | set(categories.values_list('id', flat=True))
    label_ids = _parse_label_ids(request)
    clearance = get_or_create_clearance(label_ids, allowed_label_ids, name_hint=page.title) or page.classification

    if not uploaded:
        messages.error(request, 'Choose a file to attach.')
        return redirect(page.get_absolute_url())

    WikiAttachment.objects.create(
        page=page, file=uploaded, filename=uploaded.name,
        content_type=uploaded.content_type or '', size=uploaded.size,
        classification=clearance, uploaded_by=request.user,
    )
    messages.success(request, f'Attached "{uploaded.name}".')
    return redirect(page.get_absolute_url())


@login_required
def attachment_download(request, attachment_id):
    """
    The one and only place attachment bytes are served from. Never link
    directly to attachment.file.url anywhere - that would bypass this
    accessible_by check (raw MEDIA_URL serving is never enabled for this
    app; see mls/urls.py).
    """
    attachment = get_object_or_404(WikiAttachment, pk=attachment_id)
    try:
        handle = attachment.file.open('rb')
    except FileNotFoundError:
        raise Http404('File not found.')
    return FileResponse(
        handle, as_attachment=True, filename=attachment.filename,
        content_type=attachment.content_type or 'application/octet-stream',
    )


@login_required
@require_POST
def attachment_delete(request, attachment_id):
    attachment = get_object_or_404(WikiAttachment, pk=attachment_id)
    page = attachment.page
    filename = attachment.filename
    attachment.file.delete(save=False)
    attachment.delete()
    messages.success(request, f'Deleted attachment "{filename}".')
    return redirect(page.get_absolute_url())


# ==================== Search ====================

@login_required
def search(request):
    query = request.GET.get('q', '').strip()
    results = []
    if query:
        results = list(
            WikiPage.objects
            .filter(Q(title__icontains=query) | Q(content_html__icontains=query))
            .select_related('space', 'classification')
            .order_by('title')[:100]
        )
    return render(request, 'wiki/search_results.html', {'query': query, 'results': results})
