"""
API Response Utilities
Standard response format for all API endpoints
"""
from rest_framework.response import Response
from rest_framework import status


class APIResponse:
    """Standardized API response builder"""

    @staticmethod
    def success(message, data=None, status_code=status.HTTP_200_OK):
        """
        Success response

        Args:
            message (str): Success message
            data (dict): Response data
            status_code (int): HTTP status code

        Returns:
            Response: DRF Response object
        """
        return Response({
            'success': True,
            'message': message,
            'data': data
        }, status=status_code)

    @staticmethod
    def error(message, data=None, status_code=status.HTTP_400_BAD_REQUEST, error_code=None):
        """
        Error response

        Args:
            message (str): Error message
            data (dict): Additional error data
            status_code (int): HTTP status code
            error_code (str): Error code for frontend

        Returns:
            Response: DRF Response object
        """
        response_data = {
            'success': False,
            'message': message,
            'data': data or {}
        }

        if error_code:
            response_data['data']['error_code'] = error_code

        return Response(response_data, status=status_code)

    @staticmethod
    def validation_error(errors, message='Validation failed'):
        """
        Validation error response

        Args:
            errors (dict): Validation errors from serializer
            message (str): Error message

        Returns:
            Response: DRF Response object
        """
        return Response({
            'success': False,
            'message': message,
            'data': {
                'errors': errors
            }
        }, status=status.HTTP_400_BAD_REQUEST)


# Error codes
class ErrorCode:
    """Standard error codes for the application"""

    # Authentication errors
    INVALID_TOKEN = 'INVALID_TOKEN'
    TOKEN_EXPIRED = 'TOKEN_EXPIRED'
    TOKEN_ALREADY_USED = 'TOKEN_ALREADY_USED'
    INVALID_AUDIENCE = 'INVALID_AUDIENCE'
    INVALID_ISSUER = 'INVALID_ISSUER'
    EMAIL_NOT_VERIFIED = 'EMAIL_NOT_VERIFIED'
    UNAUTHORIZED = 'UNAUTHORIZED'
    TOO_MANY_REQUESTS = 'TOO_MANY_REQUESTS'

    # Profile errors
    PROFILE_NOT_FOUND = 'PROFILE_NOT_FOUND'
    PROFILE_ALREADY_EXISTS = 'PROFILE_ALREADY_EXISTS'
    DUPLICATE_NICKNAME = 'DUPLICATE_NICKNAME'

    # Validation errors
    VALIDATION_ERROR = 'VALIDATION_ERROR'
    INVALID_INPUT = 'INVALID_INPUT'

    # Server errors
    INTERNAL_ERROR = 'INTERNAL_ERROR'
    AUTHENTICATION_FAILED = 'AUTHENTICATION_FAILED'
