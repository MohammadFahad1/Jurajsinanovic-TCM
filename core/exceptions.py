import logging
from rest_framework.views import exception_handler
from rest_framework.response import Response
from rest_framework import status

logger = logging.getLogger(__name__)


def _format_error_message(data):
    """
    Recursively format error messages from strings, lists, or dicts into a single clean string.
    """
    if data is None:
        return ""
    if isinstance(data, str):
        return data
    if isinstance(data, list):
        return ", ".join([_format_error_message(item) for item in data if item is not None])
    if isinstance(data, dict):
        if "message" in data:
            return _format_error_message(data["message"])
        if "detail" in data:
            return _format_error_message(data["detail"])
        if "non_field_errors" in data and len(data) == 1:
            return _format_error_message(data["non_field_errors"])

        messages = []
        for key, val in data.items():
            formatted_val = _format_error_message(val)
            if key == "non_field_errors":
                messages.append(formatted_val)
            else:
                messages.append(f"{key}: {formatted_val}")
        return "; ".join(messages)
    return str(data)


def custom_exception_handler(exc, context):
    """
    Global exception handler for Django REST Framework.
    Formats all exceptions to return:
    {
        "success": False,
        "message": "Error message ..."
    }
    """
    # Call REST framework's default exception handler first to get the standard response
    response = exception_handler(exc, context)

    if response is not None:
        message = _format_error_message(response.data)
        if not message:
            message = "An error occurred."
        response.data = {
            "success": False,
            "message": message
        }
    else:
        logger.error(f"Unhandled exception: {exc}", exc_info=True)
        message = str(exc) if str(exc) else "Internal server error"
        response = Response(
            {
                "success": False,
                "message": message
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )

    return response
