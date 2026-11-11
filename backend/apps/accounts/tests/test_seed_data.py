from django.test import TestCase

from apps.accounts.models import User
from apps.applications.models import FeedbackResult, JobApplication


class SeedDataTests(TestCase):
    """Assertions about the idempotent data migration
    (apps/applications/migrations/0002_seed_demo_data.py), which runs as
    part of every `migrate` (including the one that sets up the test
    database)."""

    def test_demo_users_exist_with_expected_roles(self):
        candidate = User.objects.get(email="candidate@example.com")
        admin = User.objects.get(email="admin@example.com")
        self.assertEqual(candidate.role, "candidate")
        self.assertEqual(admin.role, "admin")

    def test_demo_users_password_is_demo12345(self):
        candidate = User.objects.get(email="candidate@example.com")
        self.assertTrue(candidate.check_password("demo12345"))

    def test_user_count(self):
        self.assertEqual(User.objects.count(), 2)

    def test_seeded_application_count_in_expected_range(self):
        count = JobApplication.objects.filter(owner__email="candidate@example.com").count()
        self.assertGreaterEqual(count, 8)
        self.assertLessEqual(count, 10)

    def test_most_seeded_applications_have_feedback(self):
        total = JobApplication.objects.count()
        with_feedback = FeedbackResult.objects.count()
        self.assertGreater(with_feedback, 0)
        self.assertGreaterEqual(with_feedback, total - 3)

    def test_seeded_applications_have_varied_companies(self):
        companies = set(
            JobApplication.objects.values_list("company_name", flat=True)
        )
        self.assertGreater(len(companies), 5)

    def test_seeded_feedback_references_input_text(self):
        """The stub feedback for each seeded application should be clearly
        derived from that application's own text, not boilerplate shared
        across all applications."""
        feedback_results = list(FeedbackResult.objects.select_related("job_application"))
        self.assertTrue(feedback_results)
        feedback_bodies = {fr.feedback for fr in feedback_results}
        # Each seeded application's resume/job text is distinct, so the
        # feedback text (which quotes snippets of it) should be distinct too.
        self.assertEqual(len(feedback_bodies), len(feedback_results))
