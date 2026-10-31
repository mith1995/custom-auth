from rest_framework import status
from rest_framework.exceptions import APIException

class InvalidCredentials(APIException):
    status_code = status.HTTP_401_UNAUTHORIZED
    default_detail = {
        "detail": "Login details galat hain",
        "code": "invalid_credentials",
    }

class EmailNotVerified(APIException):
    status_code = status.HTTP_403_FORBIDDEN
    default_detail = {
        "detail": "Pehle apna email verify karein.",
        "code": "email_not_verified",
    }