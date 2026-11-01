import logging

from django.db import transaction
from django.db import IntegrityError

from rest_framework import status, generics
from rest_framework.parsers import FormParser, JSONParser, MultiPartParser
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from .conf import authnest_settings
from .models import User

from .utils import normalize_email

from django.contrib.auth.models import update_last_login

from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.settings import api_settings

from .serializers import (
    RegisterSerializer,
    ResendVerificationSerializer,
    VerifyEmailSerializer,
    AdminLoginSerializer, 
    LoginSerializer,
    ChangePasswordSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
    ProfileSerializer,
    ConfirmEmailChangeSerializer,
    EmailChangeSerializer,
    DeleteAccountSerializer,
)

from .services.cookies import (
    build_token_response,
    read_refresh_token,
    delete_refresh_cookie,
)

from .services.emails import (
    send_verification_email,
    send_password_changed_email,
    send_password_reset_email,
    send_email_change_email,
    send_email_changed_notice,
    send_account_deleted_email,
)

from .services.tokens import (
    AuthnestRefreshToken, 
    issue_tokens, 
    make_access_token,
    blacklist_all_tokens,
)

logger = logging.getLogger(__name__)

def user_payload(user):
    return {
        "id": user.pk,
        "email": user.email,
        "phone": user.phone,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_email_verified": user.is_email_verified,
        "is_staff": user.is_staff,   
    }

class RegisterView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        message = "Your account has been created successfully."
        if user.email and authnest_settings.REQUIRE_EMAIL_VERIFICATION:
            message += "A verification link has been sent to your email address."

        return Response(
            {"detail":  message, "user": {"id": user.pk, "email": user.email, "phone": user.phone}},
            status=status.HTTP_201_CREATED
        )

class VerifyEmailView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        if not user.is_email_verified:
            user.is_email_verified = True
            user.save(update_fields=["is_email_verified"])

        return Response({"detail": "Your email address has been verified successfully."})

class ResendVerificationView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ResendVerificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = normalize_email(serializer.validated_data["email"])
        user = User.objects.filter(email__iexact=email, is_email_verified=False).first()
        if user is not None:
            try:
                send_verification_email(user)
            except Exception:
                logger.exception("Failed to resend verification email (user ID=%s).", user.pk)

        # Email exist kare ya na kare, response hamesha same
        return Response(
            {"detail": "If this email address is registered and has not been verified, a new verification link has been sent."}
        )

class LoginView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]

        # 2FA ka check Step 7 me yahan aayega

        update_last_login(None, user)
        tokens = issue_tokens(user)
        return build_token_response(tokens, extra={"user": user_payload(user)})

class AdminLoginView(LoginView):
    serializer_class = AdminLoginSerializer

class RefreshView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def _invalid(self):
        response = Response(
            {"detail": "Your session has expired. Please log in again.", "code": "token_invalid"},
            status=status.HTTP_401_UNAUTHORIZED
        )
        if authnest_settings.REFRESH_TOKEN_IN_COOKIE:
            delete_refresh_cookie(response)
        return response

    def post(self, request):
        raw = read_refresh_token(request)
        if not raw:
            return self._invalid()

        try:
            refresh = AuthnestRefreshToken(raw)
        except TokenError:
            return self._invalid()

        # objects alive-only hai, to soft-deleted user ka token yahin ruk jata hai
        user = User.objects.filter(
            pk=refresh[api_settings.USER_ID_CLAIM], is_active=True
        ).first()
        if user is None:
            return self._invalid()

        if authnest_settings.REFRESH_TOKEN_ROTATION:
            refresh.blacklist()
            tokens = issue_tokens(user)
        else:
            tokens = {"access": str(make_access_token(refresh)), "refresh": raw}

        return build_token_response(tokens)

class LogoutView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        raw = read_refresh_token(request)
        if raw:
            try:
                AuthnestRefreshToken(raw).blacklist()
            except TokenError:
                pass # The token is already invalid, so there is nothing to do during logout.

        response = Response({"detail": "Logout ho gaya."})
        if authnest_settings.REFRESH_TOKEN_IN_COOKIE:
            delete_refresh_cookie(response)
        return response

class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        email = normalize_email(serializer.validated_data["email"])
        user = User.objects.filter(email__iexact=email, is_active=True).first()
        if user is not None:
            try:
                send_password_reset_email(user)
            except Exception:
                logger.exception("Failed to send password reset email (user ID=%s).", user.pk)

        # Email exist kare ya na kare, response hamesha same
        return Response(
            {"detail": "If this email address is registered, a password reset link has been sent."}
        )


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        with transaction.atomic():
            user.set_password(serializer.validated_data["password"])
            user.save(update_fields=["password"])
            blacklist_all_tokens(user)

        try:
            send_password_changed_email(user)
        except Exception:
            logger.exception("Failed to send password change notification email (user ID=%s).", user.pk)

        # Auto-login nahi, sirf message
        return Response({"detail": "Your password has been reset successfully. Please log in with your new password."})


class ChangePasswordView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        with transaction.atomic():
            user.set_password(serializer.validated_data["new_password"])
            user.save(update_fields=["password"])
            blacklist_all_tokens(user)

        try:

            send_password_changed_email(user)
        except Exception:
            logger.exception("Failed to send password change notification email (user ID=%s).", user.pk)

        response = Response(
            {"detail": "Your password has been changed successfully. Please log in again."}
        )
        if authnest_settings.REFRESH_TOKEN_IN_COOKIE:
            delete_refresh_cookie(response)
        return response

class ProfileView(generics.RetrieveUpdateAPIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    serializer_class = ProfileSerializer
    http_method_names = ["get", "patch", "head", "options"]

    def get_object(self):
        return self.request.user

class ProfilePictureView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        if user.profile_picture:
            user.profile_picture.delete(save=False)
            user.save(update_fields=["profile_picture"])
        return Response(status=status.HTTP_204_NO_CONTENT)

class EmailChangeView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = EmailChangeSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        try:
            send_email_change_email(request.user, serializer.validated_data["new_email"])
        except Exception:
            logger.exception("Failed to send email change confirmation link (user ID=%s).", request.user.pk)
            return Response(
                {"detail": "Unable to send the email. Please try again later."},
                status=status.HTTP_503_SERVICE_UNAVAILABLE,
            )

        return Response(
            {"detail": "A confirmation link has been sent to your new email address. Your email address will be changed only after you open the link."}
        )


class ConfirmEmailChangeView(APIView):
    permission_classes = [AllowAny]
    authentication_classes = []

    def post(self, request):
        serializer = ConfirmEmailChangeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        new_email = serializer.validated_data["new_email"]
        old_email = user.email

        try:
            with transaction.atomic():
                user.email = new_email
                user.is_email_verified = True
                user.save(update_fields=["email", "is_email_verified"])
        except IntegrityError:
            raise ValidationError({"token": "This email address is already in use by another account."})

        if old_email:
            try:
                send_email_changed_notice(user, old_email, new_email)
            except Exception:
                logger.exception("Failed to send email change notification (user ID=%s).", user.pk)

        return Response({"detail": "Your email address has been changed successfully.", "email": user.email})

class DeleteAccountView(APIView):
    authentication_classes = [JWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = DeleteAccountSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        user = request.user
        email = user.email

        with transaction.atomic():
            blacklist_all_tokens(user)
            user.delete()

        if email:
            try:
                send_account_deleted_email(user, email)
            except Exception:
                logger.exception("Failed to send account deletion notification email (email=%s).", email)

        response = Response({"detail": "Your account has been deleted successfully."})
        if authnest_settings.REFRESH_TOKEN_IN_COOKIE:
            delete_refresh_cookie(response)
        return response