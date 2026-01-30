from rest_framework.permissions import BasePermission
from django.conf import settings

class HasAPIKey(BasePermission):
    """
    Allows access only if the request contains a valid API key.
    """

    def has_permission(self, request, view):
        # Allow if API_KEY is not set in settings (dev mode or disabled)
        # Or if the view explicitly allows it (though this is a permission class)
        api_key = getattr(settings, 'API_KEY', None)
        if not api_key:
            return True

        # Check for X-API-KEY header
        request_api_key = request.META.get('HTTP_X_API_KEY')
        return request_api_key == api_key
