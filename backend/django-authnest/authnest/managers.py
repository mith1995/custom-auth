import uuid

from django.contrib.auth.models import BaseUserManager
from django.db import models
from django.utils import timezone
from .utils import normalize_email, normalize_phone
from .conf import authnest_settings

class UserQuerySet(models.QuerySet):
    def alive(self):
        return self.filter(deleted_at__isnull=True)

    def deleted(self):
        return self.filter(deleted_at__isnull=False)

    def delete(self):
        if not authnest_settings.SOFT_DELETE:
            return self.hard_delete()

        # Jo rows pehle se soft-deleted hain unke pk abhi nikalo (update se pehle)
        already_deleted_pks = list(self.deleted().values_list("pk", flat=True))

        # Alive rows soft delete
        soft_count = self.alive().update(deleted_at=timezone.now(), is_active=False)

        # Pehle se soft-deleted rows asli me delete
        total, per_model = 0, {}
        if already_deleted_pks:
            total, per_model = self.model.all_objects.filter(
                pk__in=already_deleted_pks
            ).hard_delete()

        per_model = dict(per_model)
        if soft_count:
            label = self.model._meta.label
            per_model[label] = per_model.get(label, 0) + soft_count
        return total + soft_count, per_model
    delete.alters_data = True
    delete.queryset_only = True

    def hard_delete(self):
        return super().delete()
    hard_delete.alters_data = True
    hard_delete.queryset_only = True

    def restore(self):
        return self.update(deleted_at=None, is_active=True)
    restore.queryset_only = True
    restore.alters_data = True

class UserManager(BaseUserManager.from_queryset(UserQuerySet)):
    """objects: sirf alive users. Normal app code isi se kaam karega."""

    use_in_migrations = True

    def get_queryset(self):
        return super().get_queryset().alive()

    # ---------- helpers ----------
    def _generate_username(self):
        while True:
            username = f"user_{uuid.uuid4().hex[:12]}"
            if not self.model._base_manager.filter(username=username).exists():
                return username

    # ---------- creation ----------
    def create_user(self, email=None, phone=None, password=None, username=None, **extra_fields):
        email = normalize_email(email)
        phone = normalize_phone(phone)
        if not email and not phone:
            raise ValueError("Email ya phone mein se kam se kam ek zaroori hai")

        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)

        user = self.model(
            email=email,
            phone=phone,
            username=username or self._generate_username(),
            **extra_fields,
        )

        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_email_verified", True)

        if extra_fields["is_staff"] is not True:
            raise ValueError("Superuser ke liye is_staff=True zaroori hai.")
        if extra_fields["is_superuser"] is not True:
            raise ValueError("Superuser ke liye is_superuser=True zaroori hai.")

        return self.create_user(email=email, password=password, username=username, **extra_fields)

class AllUsersManager(models.Manager.from_queryset(UserQuerySet)):
    """all_objects: deleted users bhi. Registration check, restore aur admin ke liye."""