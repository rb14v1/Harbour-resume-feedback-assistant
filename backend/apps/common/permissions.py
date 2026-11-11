"""
Shared role-permission classes.

Combined with queryset-level scoping in apps/applications/views.py (never
serializer-only hiding) - a candidate's own JobApplications are the only
ones ever reachable by id for a candidate; an admin can additionally list
everyone's applications (read-only in that cross-candidate sense) but is
never granted write access to another candidate's application.
"""
from rest_framework.permissions import BasePermission


def user_role(request):
    user = getattr(request, "user", None)
    return getattr(user, "role", None)


class IsCandidate(BasePermission):
    """Any authenticated user (every account can act as a candidate for
    their own applications, admin included)."""

    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)


class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        return bool(
            request.user and request.user.is_authenticated and user_role(request) == "admin"
        )
