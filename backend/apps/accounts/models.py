from django.contrib.auth.models import AbstractUser
from django.db import models

from apps.accounts.managers import UserManager


class User(AbstractUser):
    """Custom user, email login, no username field.

    This is a personal tool, not multi-tenant - roles are kept simple.
    `candidate` is the normal end user managing their own job applications;
    `admin` exists mainly so there is a role distinction to test
    permissions against (e.g. an admin can list all applications across
    candidates, a candidate only ever sees their own).
    """

    class Role(models.TextChoices):
        CANDIDATE = "candidate", "Candidate"
        ADMIN = "admin", "Admin"

    username = None
    email = models.EmailField(unique=True)
    full_name = models.CharField(max_length=255, blank=True, default="")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.CANDIDATE)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    objects = UserManager()

    class Meta:
        ordering = ["email"]

    def __str__(self):
        return f"{self.email} ({self.role})"

    @property
    def is_admin(self):
        return self.role == self.Role.ADMIN
