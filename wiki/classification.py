"""
Helpers for turning a set of chosen SecurityLabel ids into a SecurityClearance.

Mirrors the dedup pattern mls_core.example_wiki_views already uses: reuse an
existing clearance if one exists with the exact same label set, otherwise
create a new one. Kept here so both the page form and the attachment form
share one implementation instead of duplicating the lookup/creation logic.

A user can only ever classify content with labels they themselves hold. Not
just a UI nicety: if you could mark something above your own clearance,
you'd immediately lose the ability to see (or manage) the content you just
created, and more fundamentally nobody should be able to hand out access
requirements they have no visibility into. This is enforced twice - the
picker only ever renders the user's own labels (get_user_labels_grouped),
and get_or_create_clearance() independently intersects against the same set
server-side, so a tampered POST bypassing the rendered picker still can't
grant more than the user actually has.
"""

from mls_core.models import SecurityClearance, SecurityLabel


def get_user_labels_grouped(user):
    """
    Return (levels, categories) querysets restricted to labels `user` is
    actually cleared for - empty querysets if they have no active
    SecurityProfile. Deliberately ignores Django's is_superuser/is_staff:
    those have never granted MLS clearance anywhere else in this app, and
    classifying content is exactly the kind of action that shouldn't get a
    superuser bypass.
    """
    profile = getattr(user, 'security_profile', None)
    if profile is None or not profile.is_active:
        empty = SecurityLabel.objects.none()
        return empty, empty

    allowed = profile.get_all_labels()
    levels = allowed.filter(label_type=SecurityLabel.LabelType.LEVEL).order_by('rank')
    categories = allowed.filter(label_type=SecurityLabel.LabelType.CATEGORY).order_by('short_code')
    return levels, categories


def get_or_create_clearance(label_ids, allowed_label_ids, name_hint=''):
    """
    Find an existing SecurityClearance with exactly this label set, or create
    a new one. `label_ids` is intersected with `allowed_label_ids` (the
    submitting user's own labels) before anything else happens, so this can
    never produce a clearance containing a label the user doesn't hold -
    regardless of what was actually submitted in the request.

    Returns None if nothing valid is left after that intersection (no
    classification chosen, or everything chosen was outside the user's
    clearance).
    """
    label_ids = {int(i) for i in label_ids if str(i).strip()}
    label_ids &= {int(i) for i in allowed_label_ids}
    if not label_ids:
        return None

    for existing in SecurityClearance.objects.all():
        existing_ids = set(existing.securities.values_list('id', flat=True))
        if existing_ids == label_ids:
            return existing

    labels = SecurityLabel.objects.filter(id__in=label_ids)
    name = f"WIKI_{name_hint}_{len(label_ids)}LABELS".strip('_')[:100]
    clearance = SecurityClearance.objects.create(name=name)
    clearance.securities.set(labels)
    return clearance
