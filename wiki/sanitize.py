"""
Server-side sanitization for rich-text page content.

The editor (Quill) runs in the browser and produces HTML client-side, which
means the HTML posted to the server must never be trusted as-is - a stored,
sanitized-on-save copy is the only thing ever persisted or rendered back.
Only tags/attributes Quill's toolbar can actually produce are allowlisted;
everything else (including all inline `style` attributes and `<script>`,
event handlers, `javascript:` URLs, etc.) is stripped.
"""

import bleach

ALLOWED_TAGS = frozenset({
    'p', 'br', 'hr',
    'strong', 'em', 'u', 's', 'sub', 'sup',
    'h1', 'h2', 'h3', 'h4',
    'blockquote', 'pre', 'code',
    'ol', 'ul', 'li',
    'a', 'img',
    'table', 'thead', 'tbody', 'tr', 'th', 'td',
})

ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'target', 'rel'],
    'img': ['src', 'alt', 'width', 'height'],
}

ALLOWED_PROTOCOLS = frozenset({'http', 'https', 'mailto'})


def sanitize_page_html(raw_html):
    """Clean editor-submitted HTML down to the allowlisted tag/attribute set."""
    return bleach.clean(
        raw_html or '',
        tags=ALLOWED_TAGS,
        attributes=ALLOWED_ATTRIBUTES,
        protocols=ALLOWED_PROTOCOLS,
        strip=True,
    )
