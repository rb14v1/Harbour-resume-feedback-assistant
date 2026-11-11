from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.applications.models import FeedbackResult, JobApplication


class FeedbackFetchEndpointTests(APITestCase):
    def setUp(self):
        self.candidate = User.objects.create_user(
            email="fetchfb@test.com", password="pw12345678", role=User.Role.CANDIDATE
        )
        self.client.force_authenticate(self.candidate)
        self.application = JobApplication.objects.create(
            owner=self.candidate,
            company_name="Fetch Co",
            job_title="Engineer",
            job_description="jd",
            resume_text="resume",
        )
        self.url = reverse("application-feedback", args=[self.application.id])

    def test_404_before_generation(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_200_after_generation(self):
        self.client.post(reverse("application-generate-feedback", args=[self.application.id]))
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("feedback", resp.data)
        self.assertIn("cover_letter_draft", resp.data)
        self.assertIn("generated_at", resp.data)

    def test_fetch_matches_stored_result(self):
        self.client.post(reverse("application-generate-feedback", args=[self.application.id]))
        stored = FeedbackResult.objects.get(job_application=self.application)
        resp = self.client.get(self.url)
        self.assertEqual(resp.data["feedback"], stored.feedback)
        self.assertEqual(resp.data["cover_letter_draft"], stored.cover_letter_draft)

    def test_other_candidate_cannot_fetch_foreign_feedback(self):
        self.client.post(reverse("application-generate-feedback", args=[self.application.id]))
        other = User.objects.create_user(
            email="other-fetchfb@test.com", password="pw12345678", role=User.Role.CANDIDATE
        )
        self.client.force_authenticate(other)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
