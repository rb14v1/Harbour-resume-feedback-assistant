from django.urls import path

from apps.accounts.views import LogoutView, MeView, RegisterView

urlpatterns = [
    path("auth/logout/", LogoutView.as_view(), name="auth-logout"),
    path("auth/register/", RegisterView.as_view(), name="auth-register"),
    path("users/me/", MeView.as_view(), name="users-me"),
]
