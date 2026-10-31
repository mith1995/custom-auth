from django.urls import path

from . import views

app_name = "authnest"

urlpatterns = [
    path("register/", views.RegisterView.as_view(), name="register"),
    path("verify-email/", views.VerifyEmailView.as_view(), name="verify-email"),
    path("resend-verification/", views.ResendVerificationView.as_view(), name="resend-verification"),
    path("login/", views.LoginView.as_view(), name="login"),
    path("admin/login/", views.AdminLoginView.as_view(), name="admin-login"),
    path("token/refresh/", views.RefreshView.as_view(), name="token-refresh"),
    path("logout/", views.LogoutView.as_view(), name="logout"),
    path("forgot-password/", views.ForgotPasswordView.as_view(), name="forgot-password"),
    path("reset-password/", views.ResetPasswordView.as_view(), name="reset-password"),
    path("change-password/", views.ChangePasswordView.as_view(), name="change-password"),
    path("profile/", views.ProfileView.as_view(), name="profile"),
    path("profile/picture/", views.ProfilePictureView.as_view(), name="profile-picture"),
    path("email/change/", views.EmailChangeView.as_view(), name="email-change"),
    path("email/change/confirm/", views.ConfirmEmailChangeView.as_view(), name="email-change-confirm"),
    path("account/delete/", views.DeleteAccountView.as_view(), name="account-delete"),
]

