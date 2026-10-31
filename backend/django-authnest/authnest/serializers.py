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
        # all_objects: soft-deleted users ka email bhi reserved hai
        if email and User.all_objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Is email se account pehle se maujood hai")
        return email

    def validate_phone(self, value):
        phone = normalize_phone(value)
        if phone:
            try:
                phone_validator(phone)
            except DjangoValidationError as exc:
                raise serializers.ValidationError(exc.messages)
            if User.all_objects.filter(phone=phone).exists():
                raise serializers.ValidationError("Is phone number se account pehle se maujood hai")
        return phone

    def validate(self, attrs):
        methods = list(authnest_settings.USER_LOGIN_METHODS)

        # Jo identifier login method me nahi hai, use register me allow nahi
        for field in ("email", "phone"):
            if field not in methods and attrs.get(field):
                raise serializers.ValidationError(
                    {field: f"Registration me {field} allowed nahi hai."}
                )

        if len(methods) == 1:
            field = methods[0]
            if not attrs.get(field):
                raise serializers.ValidationError({field: "Ye field zaroori hai."})
        elif not (attrs.get("email") or attrs.get("phone")):
            raise serializers.ValidationError(
                "Email ya phone mein se kam se kam ek dena zaroori hai."
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
            # Do requests ek saath aayi to check chook sakta hai, DB constraint pakad leta hai
            raise serializers.ValidationError("Is email ya phone se account pehle se maujood hai.")

        if user.email and authnest_settings.REQUIRE_EMAIL_VERIFICATION:
            try:
                send_verification_email(user)
            except Exception:
                # Email fail ho to bhi user ban chuka hai, resend endpoint se link mil jayega
                logger.exception("Verification email fail hua (user id=%s)", user.pk)

        return user

class VerifyEmailSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, attrs):
        invalid = serializers.ValidationError({"token": "Link invalid ya expire ho gaya hai."})

        try:
            payload = read_email_verification_token(attrs["token"])
        except signing.BadSignature: #SignatureExpired bhi isi me aata hai
            raise invalid

        user = User.objects.filter(pk=payload.get("uid")).first()
        # Email badal gayi ho (ya user delete ho gaya ho) to purana link kaam nahi karega
        if user is None or user.email != payload.get("email"):
            raise invalid

        attrs["user"] = user
        return attrs

class ResendVerificationSerializer(serializers.Serializer):
    email = serializers.EmailField()

class LoginSerializer(serializers.Serializer):
    scope = "user" # field nahi, class attribute hai (admin wala isko badlega)

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
        invalid = serializers.ValidationError({"token": "Link invalid ya expire ho gaya hai."})

        try:
            payload = read_password_reset_token(attrs["token"])
        except signing.BadSignature:  # SignatureExpired bhi isi me aata hai
            raise invalid

        user = User.objects.filter(pk=payload.get("uid"), is_active=True).first()
        # Password badal chuka ho to fingerprint alag hoga, yani link pehle use ho chuka hai
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
            raise serializers.ValidationError("Purana password galat hai.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user

        if attrs["old_password"] == attrs["new_password"]:
            raise serializers.ValidationError(
                {"new_password": "Naya password purane password jaisa nahi ho sakta."}
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
                "Janam tithi future ki nahi ho sakti"
            )
        if today.year - value.year > 120:
            raise serializers.ValidationError("janam tithi sahi nahi lag rahi.")
        return value

    def validate_profile_picture(self, value):
        if value is None:
            return value
        max_size = authnest_settings.PROFILE_PICTURE_MAX_SIZE
        if value.size > max_size:
            raise serializers.ValidationError(
                f"Image {max_size / (1024 * 1024):g} MB se badi nahi ho sakti."
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
            raise serializers.ValidationError("Password galat hai.")
        return value

    def validate_new_email(self, value):
        email = normalize_email(value)
        user = self.context["request"].user
        if email == user.email:
            raise serializers.ValidationError("Ye aapki current email hi hai.")
        # all_objects: soft-deleted users ki email bhi reserved hai
        if User.all_objects.filter(email__iexact=email).exists():
            raise serializers.ValidationError("Is email se account pehle se maujood hai.")
        return email


class ConfirmEmailChangeSerializer(serializers.Serializer):
    token = serializers.CharField()

    def validate(self, attrs):
        invalid = serializers.ValidationError({"token": "Link invalid ya expire ho gaya hai."})

        try:
            payload = read_email_change_token(attrs["token"])
        except signing.BadSignature:  # SignatureExpired bhi isi me aata hai
            raise invalid

        user = User.objects.filter(pk=payload.get("uid"), is_active=True).first()
        # Email pehle hi badal chuki ho to purana link kaam nahi karega
        if user is None or user.email != payload.get("old"):
            raise invalid

        new_email = payload["new"]
        if User.all_objects.filter(email__iexact=new_email).exclude(pk=user.pk).exists():
            raise serializers.ValidationError(
                {"token": "Ye email ab kisi aur account me use ho rahi hai."}
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
            raise serializers.ValidationError("Password galat hai.")
        return value

    def validate(self, attrs):
        user = self.context["request"].user
        if user.is_superuser:
            other_superusers = User.objects.filter(
                is_superuser=True, is_active=True
            ).exclude(pk=user.pk)
            if not other_superusers.exists():
                raise serializers.ValidationError(
                    "Aap akhri superuser hain, isliye account delete nahi kar sakte."
                )
        return attrs