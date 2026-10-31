from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin

from django import forms
from django.contrib.auth.forms import BaseUserCreationForm

from .conf import authnest_settings

from .models import User
from .utils import normalize_email, normalize_phone


class DeletedFilter(admin.SimpleListFilter):
    title = "account status"
    parameter_name = "account"

    def lookups(self, request, model_admin):
        return [("alive", "Alive"), ("deleted", "Soft deleted")]

    def queryset(self, request, queryset):
        if self.value() == "alive":
            return queryset.alive()
        if self.value() == "deleted":
            return queryset.deleted()
        return queryset

class AdminUserCreationForm(BaseUserCreationForm):
    class Meta(BaseUserCreationForm.Meta):
        model = User
        fields = ("username", "email", "phone")

    def clean_email(self):
        email = normalize_email(self.cleaned_data.get("email"))
        # all_objects: soft-deleted user ki email bhi reserved hai
        if email and User.all_objects.filter(email__iexact=email).exists():
            raise forms.ValidationError("Is email se account pehle se maujood hai.")
        return email

    def clean_phone(self):
        phone = normalize_phone(self.cleaned_data.get("phone"))
        if phone and User.all_objects.filter(phone=phone).exists():
            raise forms.ValidationError("Is phone number se account pehle se maujood hai.")
        return phone

    def clean(self):
        cleaned = super().clean()
        if not cleaned.get("email") and not cleaned.get("phone"):
            raise forms.ValidationError(
                "Email ya phone mein se kam se kam ek dena zaroori hai."
            )
        return cleaned

@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    list_display = (
        "identifier", "email", "phone", "is_staff", "is_active",
        "is_email_verified", "status", "date_joined",
    )
    list_filter = (DeletedFilter, "is_staff", "is_active", "is_email_verified")
    search_fields = ("email", "phone", "username", "first_name", "last_name")
    ordering = ("-date_joined",)
    readonly_fields = ("last_login", "date_joined", "deleted_at")
    filter_horizontal = ("groups", "user_permissions")
    actions = ["restore_users"]

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("Identity", {"fields": ("email", "phone", "is_email_verified", "is_phone_verified")}),
        ("Profile", {"fields": ("first_name", "last_name", "dob", "profile_picture")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
        ("Dates", {"fields": ("last_login", "date_joined", "deleted_at")}),
    )

    def get_queryset(self, request):
        # Soft delete on ho to all_objects (deleted bhi dikhein), off ho to sirf alive
        manager = (
            self.model.all_objects
            if authnest_settings.SOFT_DELETE
            else self.model.objects
        )
        queryset = manager.all()
        ordering = self.get_ordering(request)
        return queryset.order_by(*ordering) if ordering else queryset

    def get_list_display(self, request):
        if authnest_settings.SOFT_DELETE:
            return self.list_display
        return [column for column in self.list_display if column != "status"]

    def get_list_filter(self, request):
        if authnest_settings.SOFT_DELETE:
            return self.list_filter
        return [item for item in self.list_filter if item is not DeletedFilter]

    def get_actions(self, request):
        actions = super().get_actions(request)
        if not authnest_settings.SOFT_DELETE:
            actions.pop("restore_users", None)
            actions.pop("hard_delete_users", None)
        return actions

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj is None or authnest_settings.SOFT_DELETE:
            return fieldsets
        return [
            (
                name,
                {
                    **options,
                    "fields": tuple(f for f in options["fields"] if f != "deleted_at"),
                },
            )
            for name, options in fieldsets
        ]

    def has_add_permission(self, request):
        # Users registration ya createsuperuser se bante hain, admin me nahi
        return False

    add_form = AdminUserCreationForm
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("username", "email", "phone", "password1", "password2"),
            },
        ),
    )

    @admin.display(description="User")
    def identifier(self, obj):
        return str(obj)

    @admin.display(description="Status")
    def status(self, obj):
        return "Deleted" if obj.is_deleted else "Alive"

    @admin.action(description="Restore selected users")
    def restore_users(self, request, queryset):
        count = queryset.deleted().restore()
        self.message_user(request, f"{count} user restore ho gaye.", messages.SUCCESS)
