from rest_framework import status
from rest_framework.exceptions import APIException

class InvalidCredentials(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = {
        "detail": "Invalid login credentials.",
        "code": "invalid_credentials",
    }

class EmailNotVerified(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = {
        "detail": "Please verify your email first.",
        "code": "email_not_verified",
    }