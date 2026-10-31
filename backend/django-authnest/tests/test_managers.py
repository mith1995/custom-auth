import pytest
from django.db import IntegrityError, transaction

from authnest.models import User
from tests.constants import PASSWORD

pytestmark = pytest.mark.django_db


# ---------- create_user ----------

def test_create_user_normalizes_email_and_generates_username():
    user = User.objects.create_user(email="  Test@X.com ", password=PASSWORD)
    assert user.email == "test@x.com"
    assert user.username.startswith("user_")


def test_create_user_normalizes_phone():
    user = User.objects.create_user(phone="+91 98765-43210", password=PASSWORD)
    assert user.phone == "+919876543210"


def test_create_user_stores_blank_email_as_none():
    user = User.objects.create_user(email="   ", phone="+919876543210", password=PASSWORD)
    assert user.email is None


def test_create_user_hashes_password():
    user = User.objects.create_user(email="a@x.com", password=PASSWORD)
    assert user.password != PASSWORD
    assert user.check_password(PASSWORD)


def test_create_user_without_email_and_phone_raises():
    with pytest.raises(ValueError):
        User.objects.create_user(password=PASSWORD)


def test_generated_usernames_are_unique():
    usernames = {
        User.objects.create_user(email=f"u{i}@x.com", password=PASSWORD).username
        for i in range(20)
    }
    assert len(usernames) == 20


def test_duplicate_email_is_rejected_even_with_different_case():
    User.objects.create_user(email="a@x.com", password=PASSWORD)
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(email="A@X.com", password=PASSWORD)


def test_database_constraint_requires_email_or_phone():
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create(username="only-username")


# ---------- create_superuser ----------

def test_create_superuser_sets_flags():
    admin = User.objects.create_superuser(
        username="boss", email="boss@x.com", password=PASSWORD
    )
    assert admin.is_staff and admin.is_superuser and admin.is_email_verified


def test_create_superuser_refuses_wrong_flags():
    with pytest.raises(ValueError):
        User.objects.create_superuser(
            username="boss", email="boss@x.com", password=PASSWORD, is_staff=False
        )


# ---------- model helpers ----------

def test_str_and_full_name():
    user = User.objects.create_user(
        email="a@x.com", password=PASSWORD, first_name="Ravi", last_name="Patel"
    )
    assert str(user) == "a@x.com"
    assert user.full_name == "Ravi Patel"


# ---------- soft delete ----------

def test_soft_delete_marks_user_and_hides_from_objects(user):
    user.delete()
    user.refresh_from_db()  # objects me nahi milega, isliye all_objects se
    assert not User.objects.filter(pk=user.pk).exists()


def test_soft_deleted_user_is_still_in_all_objects(user):
    user.delete()
    deleted = User.all_objects.get(pk=user.pk)
    assert deleted.deleted_at is not None
    assert deleted.is_deleted
    assert deleted.is_active is False


def test_restore_brings_user_back(user):
    user.delete()
    restored = User.all_objects.get(pk=user.pk)
    restored.restore()
    assert User.objects.filter(pk=user.pk).exists()
    assert User.objects.get(pk=user.pk).is_active is True


def test_hard_delete_removes_row(user):
    user.hard_delete()
    assert not User.all_objects.filter(pk=user.pk).exists()


def test_queryset_delete_is_soft_too(user):
    count, _ = User.objects.filter(pk=user.pk).delete()
    assert count == 1
    assert User.all_objects.filter(pk=user.pk).exists()
    assert not User.objects.filter(pk=user.pk).exists()


def test_queryset_hard_delete_and_restore(user):
    User.all_objects.filter(pk=user.pk).delete()
    assert User.all_objects.filter(pk=user.pk).restore() == 1
    assert User.objects.filter(pk=user.pk).exists()

    User.objects.filter(pk=user.pk).hard_delete()
    assert not User.all_objects.filter(pk=user.pk).exists()


@pytest.mark.parametrize("method", ["delete", "hard_delete", "restore"])
def test_destructive_methods_are_not_on_the_manager(method):
    with pytest.raises(AttributeError):
        getattr(User.objects, method)


def test_soft_deleted_email_stays_reserved(user):
    user.delete()
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create_user(email="user@example.com", password=PASSWORD)


def test_email_is_free_again_after_hard_delete(user):
    user.hard_delete()
    again = User.objects.create_user(email="user@example.com", password=PASSWORD)
    assert again.pk


def test_soft_delete_off_makes_delete_permanent(user, settings):
    settings.AUTHNEST = {"SOFT_DELETE": False}
    user.delete()
    assert not User.all_objects.filter(pk=user.pk).exists()


def test_soft_delete_off_makes_queryset_delete_permanent(user, settings):
    settings.AUTHNEST = {"SOFT_DELETE": False}
    User.objects.filter(pk=user.pk).delete()
    assert not User.all_objects.filter(pk=user.pk).exists()

def test_deleting_an_already_soft_deleted_user_makes_it_permanent(user):
    user.delete()
    deleted = User.all_objects.get(pk=user.pk)

    deleted.delete()

    assert not User.all_objects.filter(pk=user.pk).exists()


def test_queryset_delete_on_all_objects_soft_deletes_alive_and_hard_deletes_deleted(user):
    other = User.objects.create_user(email="other@example.com", password=PASSWORD)
    user.delete()

    count, per_model = User.all_objects.filter(pk__in=[user.pk, other.pk]).delete()

    assert not User.all_objects.filter(pk=user.pk).exists()      # pehle se deleted tha, ab permanent
    other_row = User.all_objects.get(pk=other.pk)                # alive tha, ab soft deleted
    assert other_row.is_deleted
    assert count >= 2
    assert per_model["authnest.User"] == 2


def test_objects_manager_never_hard_deletes(user):
    User.objects.filter(pk=user.pk).delete()
    User.objects.filter(pk=user.pk).delete()  # objects ko deleted row dikhti hi nahi

    assert User.all_objects.filter(pk=user.pk).exists()


def test_a_freshly_soft_deleted_row_is_not_hard_deleted_in_the_same_call(user):
    User.all_objects.filter(pk=user.pk).delete()
    assert User.all_objects.filter(pk=user.pk).exists()


def test_two_deletes_free_the_email_again(user):
    user.delete()
    User.all_objects.get(pk=user.pk).delete()

    again = User.objects.create_user(email="user@example.com", password=PASSWORD)
    assert again.pk


def test_soft_delete_off_still_deletes_everything_permanently(user, settings):
    settings.AUTHNEST = {"SOFT_DELETE": False}
    user.delete()
    assert not User.all_objects.filter(pk=user.pk).exists()