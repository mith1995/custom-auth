from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend

from .conf import authnest_settings
from .utils import normalize_phone, normalize_email

class AuthnestBackend(ModelBackend):
    """Email / phone / username se login. Allowed methods settings se aate hain."""

    def authenticate(self, request, username = None, password = None, scope="admin", **kwargs):
        
        if scope not in ("user", "admin") or not username or password is None:
            return None
        
        UserModel = get_user_model()
        user = self._find_user(UserModel, username.strip(), scope)
        
        if user is None:
            # User na mile tab bhi hash chalao, taaki response time se pata na chale
            UserModel().set_password(password)
            return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user

        return None

    def _find_user(self, UserModel, identifier, scope):
        if scope == "user":
            allowed = authnest_settings.USER_LOGIN_METHODS
        else:
            allowed = authnest_settings.ADMIN_LOGIN_METHODS

        lookups = []
        if "email" in allowed and "@" in identifier:
            lookups.append({"email__iexact": normalize_email(identifier)})
        if "phone" in allowed and "@" not in identifier:
            lookups.append({"phone": normalize_phone(identifier)})
        if "username" in allowed:
            lookups.append({"username": identifier})

        for lookup in lookups:
            user = UserModel._default_manager.filter(**lookup).first()
            if user is not None and user.is_staff == (scope == "admin"):
                return user
        return None