"""
Middleware for MLS context management.

This middleware works with django-crum to maintain current user context
for automatic MLS filtering.
"""

from crum import get_current_request


class MLSMiddleware:
    """
    Middleware that ensures MLS context is available.

    This middleware should be placed AFTER django-crum's middleware
    in the MIDDLEWARE setting.

    Add to settings.py:
        MIDDLEWARE = [
            ...
            'crum.CurrentRequestUserMiddleware',  # django-crum
            'mls_core.middleware.MLSMiddleware',   # This middleware
            ...
        ]
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request
        response = self.get_response(request)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        """
        Called just before Django calls the view.

        This is where we could add additional MLS-specific context
        or validation if needed.
        """
        # Current user is already available via crum.get_current_user()
        # We can add additional MLS context here if needed
        return None
