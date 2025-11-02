"""
API Permissions for admin-only endpoints.
Following spec.md Section 6.1: Hardcoded API Key authentication.
"""

from rest_framework.permissions import BasePermission
from django.conf import settings


class AdminAPIKeyPermission(BasePermission):
    """
    Permission class that validates X-Admin-Key header against hardcoded API key.

    Usage in views:
        permission_classes = [AdminAPIKeyPermission]

    Security notes:
    - API key stored in environment variable ADMIN_API_KEY
    - CSRF not required for API key auth (not session-based)
    - Returns 403 Forbidden if key is invalid or missing
    """

    def has_permission(self, request, view):
        """
        Check if request has valid admin API key in header.

        Args:
            request: DRF Request object
            view: DRF View object

        Returns:
            bool: True if API key is valid, False otherwise
        """
        # Get API key from X-Admin-Key header
        api_key = request.META.get('HTTP_X_ADMIN_KEY')

        # Compare with configured admin key
        expected_key = getattr(settings, 'ADMIN_API_KEY', None)

        if not expected_key:
            # Security: If ADMIN_API_KEY not configured, deny all access
            return False

        return api_key == expected_key
