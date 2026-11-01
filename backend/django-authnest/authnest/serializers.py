import logging
from datetime import date

from django.contrib.auth import authenticate
from .exceptions import EmailNotVerified, InvalidCredentials

from django.contrib.auth.password_validation import validate_password
from django.core import signing
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import IntegrityError, transaction
from rest_framework import serializers

from .conf import authnest_settings
from .models import User, phone_validator
from .services.emails import send_verification_email
from .services.tokens import (
    read_email_verification_token,
    password_fingerprint,
    read_password_reset_token,
    read_email_change_token,
)
from .utils import normalize_email, normalize_phone

logger = logging.getLogger(__name__)

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField(required=False, allow_null=True, allow_blank=True)
    phone = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    first_name = serializers.CharField(required=False, allow_blank=True, max_length=150)
    last_name = serializers.CharField(required=False, allow_blank=True, max_length=150)

    def validate_email(self, value):
        email = normalize_email(value)
        # all_objects: Email addresses of soft-deleted users are also reserved.
        if email and User.all_objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email

    def validate_phone(self, value):
        phone = normalize_phone(value)
        if phone:
            try:
                phone_validator(phone)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.messages)
            if User.all_objects.filter(phone=phone).exists():
                raise serializers.ValidationError("An account with this phone number already exists.")
        return phone

    def validate(self, attrs):
        methods = list(authnest_settings.USER_LOGIN_METHODS)

        # Identifiers not enabled for login are not allowed during registration.
        for field in ("email", "phone"):
            if field not in methods and attrs.get(field):
                raise serializers.ValidationError(
                    {field: f"The {field} is not allowed during registration."}
                )

        if len(methods) == 1:
            field = methods[0]
            if not attrs.get(field):
                raise serializers.ValidationError({field: "This field is required."})
        elif not (attrs.get("email") or attrs.get("phone")):
            raise serializers.ValidationError(
                "At least one of the email or phone number is required."
            )

        # Django ke password validators, user ki info ke saath (similarity check ke liye)
        candidate = User(
            email = attrs.get("email"),
            phone = attrs.get("phone"),
            first_name = attrs.get("first_name", ""),
            last_name = attrs.get("last_name", ""),
        )

        try:
            validate_password(attrs["password"],user=candidate)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})

        return attrs

    def create(self, validated_data):
        try: 
            with transaction.atomic():
                user = User.objects.create_user(
                    email=validated_data.get("email"),
                    phone=validated_data.get("phone"),
                    password=validated_data.get("password"),
                    first_name=validated_data.get("first_name", ""),
                    last_name=validated_data.get("last_name", ""),
                )
        except IntegrityError:
            # If two requests arrive simultaneously, the check may fail to catch it, but the database constraint will prevent duplicates.
            raise serializers.ValidationError("An account with this email or phone number already exists.")

        if user.email and authnest_settings.REQUIRE_EMAIL_VERIFICATION:
            try:
                send_verification_email(user)
            except Exception:
                # Even if the email fails, the user account is still created. You can resend the verification link using the resend endpoint.
                logger.exception("Verification email failed (user ID=%s).", user.pk)

        return user

class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, attrs):
        invalid = serializers.ValidationError({"token": "The link is invalid or has expired."})

        try:
            payload = read_email_verification_token(attrs["token"])
        except signing.BadSignature: #SignatureExpired is also covered by this.
            raise invalid

        user = User.objects.filter(pk=payload.get("uid")).first()
        # The old link will no longer work if the email address has changed or the user has been deleted.
        if user is None or user.email != payload.get("email"):
            raise invalid

        attrs["user"] = user
        return attrs

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

class LoginSerializer(serializers.Serializer):
    scope = "user" # It's a class attribute, not a field (the admin will modify it).

    identifier = serializers.CharField()
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, trim_whitespace=False
    )

    def validate(self, attrs):
        user = authenticate(
            self.context.get("request"),
            username=attrs["identifier"],
            password=attrs["password"],
            scope=self.scope,
        )
        if user is None:
            raise InvalidCredentials()

        if (
            self.scope == "user"
            and authnest_settings.REQUIRE_EMAIL_VERIFICATION
            and user.email
            and not user.is_email_verified
        ):
            raise EmailNotVerified()

        attrs["user"] = user
        return attrs

class AdminLoginSerializer(LoginSerializer):
    scope = "admin"

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

class ResetPasswordSerializer(serializers.Serializer):
    token = serializers.CharField()
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, trim_whitespace=False
    )

    def validate(self, attrs):
        invalid = serializers.ValidationError({"token": "The link is invalid or has expired."})

        try:
            payload = read_password_reset_token(attrs["token"])
        except signing.BadSignature:  # SignatureExpired is also handled by this.
            raise invalid

        user = User.objects.filter(pk=payload.get("uid"), is_active=True).first()
        # If the password has changed, the fingerprint will be different, indicating that the link has already been used.
        if user is None or payload.get("pwd") != password_fingerprint(user):
            raise invalid

        try:
            validate_password(attrs["password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"password": list(exc.messages)})

        attrs["user"] = user
        return attrs


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, trim_whitespace=False
    )
    new_password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, trim_whitespace=False
    )

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("The current password is incorrect.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user

        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "The new password cannot be the same as the current password."}
            )

        try:
            validate_password(attrs["new_password"], user=user)
        except DjangoValidationError as exc:
            raise serializers.ValidationError({"new_password": list(exc.messages)})

        return attrs

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id', 'email', 'phone', 'first_name', 'last_name', 'dob', 
            'profile_picture', 'is_email_verified', 'is_phone_verified', 'date_joined'
        ]
        read_only_fields = [
            'id', 'email', 'phone', 'is_email_verified', 'is_phone_verified', 'date_joined'
        ]

    def validate_dob(self, value):
        if value is None:
            return value
        today = date.today()
        if value > today:
            raise serializers.ValidationError(
                "Date of birth cannot be in the future."
            )
        if today.year - value.year > 120:
            raise serializers.ValidationError("Invalid date of birth.")
        return value

    def validate_profile_picture(self, value):
        if value is None:
            return value
        max_size = authnest_settings.PROFILE_PICTURE_MAX_SIZE
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Image size cannot exceed {max_size / (1024 * 1024):g} MB"
            )
        return value

    def update(self, instance, validated_data):
        old_name = instance.profile_picture.name if instance.profile_picture else None

        instance = super().update(instance, validated_data)

        new_name = instance.profile_picture.name if instance.profile_picture else None
        if old_name and old_name != new_name:
            storage = instance._meta.get_field("profile_picture").storage
            storage.delete(old_name)
        return instance

class EmailChangeSerializer(serializers.Serializer):
    new_email = serializers.EmailField()
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, trim_whitespace=False
    )

    def validate_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Incorrect password.")
        return value

    def validate_new_email(self, value):
        email = normalize_email(value)
        user = self.context["request"].user
        if email == user.email:
            raise serializers.ValidationError("This is already your current email address.")
        # all_objects: Email addresses of soft-deleted users are also reserved.
        if User.all_objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return email


class ConfirmEmailChangeSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, attrs):
        invalid = serializers.ValidationError({"token": "The link is invalid or has expired."})

        try:
            payload = read_email_change_token(attrs["token"])
        except signing.BadSignature:  # SignatureExpired is also included in this.
            raise invalid

        user = User.objects.filter(pk=payload.get("uid"), is_active=True).first()
        # The old link will no longer work if the email address has already been changed.
        if user is None or user.email != payload.get("old"):
            raise invalid

        new_email = payload["new"]
        if User.all_objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
            raise serializers.ValidationError(
                {"token": "This email address is already being used by another account."}
            )

        attrs["user"] = user
        attrs["new_email"] = new_email
        return attrs

class DeleteAccountSerializer(serializers.Serializer):
    password = serializers.CharField(
        write_only=True, style={"input_type": "password"}, trim_whitespace=False
    )

    def validate_password(self, value):
        if not self.context["request"].user.check_password(value):
            raise serializers.ValidationError("Incorrect password.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        if user.is_superuser:
            other_superusers = User.objects.filter(
                is_superuser=True, is_active=True
            ).exclude(pk=user.pk)
            if not other_superusers.exists():
                raise serializers.ValidationError(
                    "You are the last remaining superuser, so your account cannot be deleted."
                )
        return attrs