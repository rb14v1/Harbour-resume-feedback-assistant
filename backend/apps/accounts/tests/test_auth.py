from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User


class AuthTests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="auth-user@example.com", password="pw12345678", role=User.Role.CANDIDATE
        )

    def test_login_with_valid_credentials_returns_tokens(self):
        resp = self.client.post(
            reverse("auth-login"),
            {"email": "auth-user@example.com", "password": "pw12345678"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)
        self.assertIn("refresh", resp.data)

    def test_login_with_invalid_credentials_rejected(self):
        resp = self.client.post(
            reverse("auth-login"),
            {"email": "auth-user@example.com", "password": "wrong-password"},
        )
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_refresh_returns_new_access_token(self):
        login_resp = self.client.post(
            reverse("auth-login"),
            {"email": "auth-user@example.com", "password": "pw12345678"},
        )
        refresh = login_resp.data["refresh"]
        resp = self.client.post(reverse("auth-refresh"), {"refresh": refresh})
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("access", resp.data)

    def test_logout_blacklists_refresh_token(self):
        login_resp = self.client.post(
            reverse("auth-login"),
            {"email": "auth-user@example.com", "password": "pw12345678"},
        )
        refresh = login_resp.data["refresh"]
        self.client.force_authenticate(self.user)
        resp = self.client.post(reverse("auth-logout"), {"refresh": refresh})
        self.assertEqual(resp.status_code, status.HTTP_205_RESET_CONTENT)

        # The blacklisted refresh token can no longer mint a new access token.
        self.client.force_authenticate(None)
        refresh_resp = self.client.post(reverse("auth-refresh"), {"refresh": refresh})
        self.assertEqual(refresh_resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_without_refresh_token_is_bad_request(self):
        self.client.force_authenticate(self.user)
        resp = self.client.post(reverse("auth-logout"), {})
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_me_requires_authentication(self):
        resp = self.client.get(reverse("users-me"))
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user(self):
        self.client.force_authenticate(self.user)
        resp = self.client.get(reverse("users-me"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data["email"], "auth-user@example.com")
        self.assertEqual(resp.data["role"], "candidate")

    def test_register_creates_candidate_user(self):
        resp = self.client.post(
            reverse("auth-register"),
            {
                "email": "new-candidate@example.com",
                "full_name": "New Candidate",
                "password": "pw12345678",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email="new-candidate@example.com")
        self.assertEqual(user.role, "candidate")
        self.assertTrue(user.check_password("pw12345678"))

    def test_user_has_no_username_field(self):
        field_names = {f.name for f in User._meta.get_fields()}
        self.assertNotIn("username", field_names)
        self.assertEqual(User.USERNAME_FIELD, "email")
