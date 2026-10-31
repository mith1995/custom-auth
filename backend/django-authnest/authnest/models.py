from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.core.validators import RegexValidator
from django.db.models import Q
from django.utils import timezone
from .conf import authnest_settings
from .managers import AllUsersManager, UserManager

phone_validator = RegexValidator(
    regex=r"^\+[1-9]\d{7,14}$",
    message="Phone number must be international format, like +919876543210"
)

class User(AbstractBaseUser, PermissionsMixin):
    # --- Identity (login ke liye) ---
    email = models.EmailField(
        max_length=255,
        unique=True,
        null=True,
        blank=True
    )
    phone = models.CharField(
        max_length=16,
        unique=True,
        null=True,
        blank=True,
        validators=[phone_validator]
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        null=True,
        blank=True
    )

    # --- Profile ---
    first_name = models.CharField(max_length=150, blank=True)
    last_name = models.CharField(max_length=150, blank=True)
    dob = models.DateField(null=True, blank=True)
    profile_picture = models.ImageField(
        upload_to="authnest/profiles/",
        null=True,
        blank=True
    )
    
    # --- Status ---
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_email_verified = models.BooleanField(default=False)
    is_phone_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(default=timezone.now)

    # --- Soft delete ---
    deleted_at = models.DateTimeField(null=True, blank=True)

    objects = UserManager()
    all_objects = AllUsersManager()

    USERNAME_FIELD = "username"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = ["email"]

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        constraints = [
            models.CheckConstraint(
                condition=Q(email__isnull=False) | Q(phone__isnull=False),
                name="authnest_user_email_or_phone_required"
            )
        ]

    def __str__(self):
        return self.email or self.phone or self.username or f"User {self.pk}"

    @property
    def is_deleted(self):
        return self.deleted_at is not None

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def delete(self, using=None, keep_parents=False):
        if not authnest_settings.SOFT_DELETE or self.is_deleted:
            return self.hard_delete(using=using, keep_parents=keep_parents)


        self.deleted_at = timezone.now()
        self.is_active = False
        self.save(update_fields=["deleted_at", "is_active"])

    def restore(self):
        self.deleted_at = None
        self.is_active = True
        self.save(update_fields=["deleted_at", "is_active"])

    def hard_delete(self, using=None, keep_parents=False):
        # Asli delete, jo Django ka original delete() chalata hai
        return super().delete(using=using, keep_parents=keep_parents)