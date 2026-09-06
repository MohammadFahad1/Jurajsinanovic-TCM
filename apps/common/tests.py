from django.test import TestCase
from rest_framework import status, serializers
from rest_framework.exceptions import (
    APIException,
    ValidationError,
    NotFound,
    PermissionDenied,
    NotAuthenticated,
)
from core.exceptions import custom_exception_handler, _format_error_message


class GlobalExceptionHandlerTestCase(TestCase):
    def test_format_error_message_strings_and_lists(self):
        self.assertEqual(_format_error_message("Simple error"), "Simple error")
        self.assertEqual(_format_error_message(["Error 1", "Error 2"]), "Error 1, Error 2")

    def test_format_error_message_dicts(self):
        self.assertEqual(
            _format_error_message({"detail": "Not found."}),
            "Not found."
        )
        self.assertEqual(
            _format_error_message({"message": "Custom error"}),
            "Custom error"
        )
        self.assertEqual(
            _format_error_message({"non_field_errors": ["Invalid credentials."]}),
            "Invalid credentials."
        )
        self.assertEqual(
            _format_error_message({"email": ["Required field."], "password": ["Too short."]}),
            "email: Required field.; password: Too short."
        )

    def test_drf_api_exception_handling(self):
        exc = NotFound("Resource not found")
        response = custom_exception_handler(exc, {})
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertEqual(response.data, {
            "success": False,
            "message": "Resource not found"
        })

    def test_validation_error_dict_handling(self):
        exc = ValidationError({"email": ["This field is required."]})
        response = custom_exception_handler(exc, {})
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data, {
            "success": False,
            "message": "email: This field is required."
        })

    def test_permission_denied_handling(self):
        exc = PermissionDenied("You do not have access")
        response = custom_exception_handler(exc, {})
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
        self.assertEqual(response.data, {
            "success": False,
            "message": "You do not have access"
        })

    def test_unhandled_exception_handling(self):
        exc = ValueError("Something unexpected happened")
        response = custom_exception_handler(exc, {})
        self.assertIsNotNone(response)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data, {
            "success": False,
            "message": "Something unexpected happened"
        })
