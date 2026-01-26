"""
LRS Authentication

Custom authentication classes for xAPI LRS endpoints.
Supports Basic Auth using LRSCredential model.
"""

import base64
import logging

from django.utils import timezone
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

from .models import LRSCredential

logger = logging.getLogger(__name__)


class LRSBasicAuthentication(BaseAuthentication):
    """
    HTTP Basic authentication for LRS xAPI endpoints.

    Uses LRSCredential model for key/secret validation.
    Updates last_used_at on successful authentication.

    Usage:
        Authorization: Basic base64(key:secret)

    Example:
        key = "abc123"
        secret = "secretpassword"
        header = f"Basic {base64.b64encode(b'abc123:secretpassword').decode()}"
    """

    def authenticate(self, request):
        """
        Authenticate the request and return a tuple of (user, credential).

        Returns None if Basic auth header not present (allows other auths).
        Raises AuthenticationFailed if credentials are invalid.
        """
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')

        if not auth_header.startswith('Basic '):
            return None

        try:
            # Decode Basic auth credentials
            encoded_credentials = auth_header.split(' ', 1)[1]
            decoded_credentials = base64.b64decode(encoded_credentials).decode('utf-8')
            key, secret = decoded_credentials.split(':', 1)
        except (ValueError, UnicodeDecodeError, IndexError) as e:
            logger.warning(f"Invalid Basic auth header format: {e}")
            raise AuthenticationFailed('Invalid Basic auth header format')

        # Look up credential by key
        try:
            credential = LRSCredential.objects.get(key=key)
        except LRSCredential.DoesNotExist:
            logger.warning(f"LRS credential not found: {key}")
            raise AuthenticationFailed('Invalid credentials')

        # Check if credential is active
        if not credential.is_active:
            logger.warning(f"LRS credential is inactive: {key}")
            raise AuthenticationFailed('Credential is inactive')

        # Verify secret
        if not credential.check_secret(secret):
            logger.warning(f"Invalid secret for LRS credential: {key}")
            raise AuthenticationFailed('Invalid credentials')

        # Update last used timestamp
        credential.update_last_used()

        logger.debug(f"LRS authentication successful: {credential.name}")

        # Return (user, auth) - user is the created_by user, auth is the credential
        return (credential.created_by, credential)

    def authenticate_header(self, request):
        """
        Return the WWW-Authenticate header value for 401 responses.
        """
        return 'Basic realm="LRS"'


class LRSCredentialPermission:
    """
    Permission helper for checking LRS credential permissions.

    Usage in views:
        credential = request.auth
        if not LRSCredentialPermission.has_permission(credential, 'write'):
            raise PermissionDenied('Write permission required')
    """

    @staticmethod
    def has_permission(credential: LRSCredential, permission: str) -> bool:
        """
        Check if the credential has the specified permission.

        Args:
            credential: LRSCredential instance (from request.auth)
            permission: Permission to check ('read', 'write', 'delete')

        Returns:
            True if permission granted, False otherwise
        """
        if not credential:
            return False

        if not isinstance(credential, LRSCredential):
            return False

        return credential.has_permission(permission)

    @staticmethod
    def require_permission(credential: LRSCredential, permission: str):
        """
        Require the credential to have the specified permission.

        Raises PermissionDenied if permission not granted.
        """
        from rest_framework.exceptions import PermissionDenied

        if not LRSCredentialPermission.has_permission(credential, permission):
            raise PermissionDenied(f'{permission.capitalize()} permission required')


class IsLRSAuthenticated:
    """
    DRF Permission class for LRS-authenticated requests.

    Ensures request is authenticated via LRS credentials.
    """

    def has_permission(self, request, view):
        """Check if request has valid LRS authentication."""
        return (
            request.auth is not None and
            isinstance(request.auth, LRSCredential)
        )


class HasLRSReadPermission:
    """
    DRF Permission class for LRS read operations.
    """

    def has_permission(self, request, view):
        """Check if request has LRS read permission."""
        if not isinstance(request.auth, LRSCredential):
            return False
        return request.auth.has_permission('read')


class HasLRSWritePermission:
    """
    DRF Permission class for LRS write operations.
    """

    def has_permission(self, request, view):
        """Check if request has LRS write permission."""
        if not isinstance(request.auth, LRSCredential):
            return False
        return request.auth.has_permission('write')


class HasLRSDeletePermission:
    """
    DRF Permission class for LRS delete operations.
    """

    def has_permission(self, request, view):
        """Check if request has LRS delete permission."""
        if not isinstance(request.auth, LRSCredential):
            return False
        return request.auth.has_permission('delete')
