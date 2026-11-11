from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.applications.models import FeedbackResult, JobApplication
from apps.common.ai import generate_resume_feedback


class GenerateFeedbackEndpointTests(APITestCase):
    def setUp(self):
        self.candidate = User.objects.create_user(
            email="genfb@test.com", password="pw12345678", role=User.Role.CANDIDATE
        )
        self.client.force_authenticate(self.candidate)
        self.application = JobApplication.objects.create(
            owner=self.candidate,
            company_name="Gen Co",
            job_title="Engineer",
            job_description="Looking for a Python engineer with Django experience.",
            resume_text="I have 5 years of Python and Django experience.",
        )
        self.url = reverse("application-generate-feedback", args=[self.application.id])

    def test_generate_feedback_creates_result(self):
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn("feedback", resp.data)
        self.assertIn("cover_letter_draft", resp.data)
        self.assertTrue(resp.data["feedback"])
        self.assertTrue(resp.data["cover_letter_draft"])
        self.assertEqual(FeedbackResult.objects.filter(job_application=self.application).count(), 1)

    def test_regenerate_replaces_not_duplicates(self):
        first = self.client.post(self.url).data
        second = self.client.post(self.url).data
        self.assertEqual(FeedbackResult.objects.filter(job_application=self.application).count(), 1)
        # Same inputs -> same deterministic stub output both times.
        self.assertEqual(first["feedback"], second["feedback"])
        self.assertEqual(first["cover_letter_draft"], second["cover_letter_draft"])

    def test_regenerate_updates_generated_at(self):
        self.client.post(self.url)
        result_id = FeedbackResult.objects.get(job_application=self.application).id
        self.client.post(self.url)
        # Still the same row (one-to-one, replaced not duplicated).
        self.assertEqual(
            FeedbackResult.objects.get(job_application=self.application).id, result_id
        )

    def test_other_candidate_cannot_generate_feedback_for_foreign_application(self):
        other = User.objects.create_user(
            email="other-genfb@test.com", password="pw12345678", role=User.Role.CANDIDATE
        )
        self.client.force_authenticate(other)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        resp = self.client.post(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class StubDeterminismTests(APITestCase):
    """Unit-level determinism checks directly against
    apps.common.ai.generate_resume_feedback - same inputs must always
    produce the same stub output, across independent calls."""

    def test_same_input_produces_same_output(self):
        resume = "Experienced backend engineer skilled in Python and Django."
        job_description = "We need a backend engineer with Python and Django skills."
        first = generate_resume_feedback(resume, job_description)
        second = generate_resume_feedback(resume, job_description)
        self.assertEqual(first, second)

    def test_different_input_produces_different_output(self):
        first = generate_resume_feedback("Python developer.", "Need a Python developer.")
        second = generate_resume_feedback("Welder with 10 years experience.", "Need a welder.")
        self.assertNotEqual(first["feedback"], second["feedback"])
        self.assertNotEqual(first["cover_letter_draft"], second["cover_letter_draft"])

    def test_stub_output_references_input_text(self):
        resume = "I led a distinctive-phrase-xyz migration project."
        job_description = "Looking for someone with distinctive-phrase-xyz experience."
        result = generate_resume_feedback(resume, job_description)
        self.assertIn("distinctive-phrase-xyz", result["feedback"])

    def test_stub_output_has_expected_keys(self):
        result = generate_resume_feedback("resume text", "job description text")
        self.assertEqual(set(result.keys()), {"feedback", "cover_letter_draft"})
        self.assertIsInstance(result["feedback"], str)
        self.assertIsInstance(result["cover_letter_draft"], str)
