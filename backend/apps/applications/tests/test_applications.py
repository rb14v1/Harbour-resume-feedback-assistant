from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from apps.applications.models import JobApplication


def make_user(email, role=User.Role.CANDIDATE):
    return User.objects.create_user(email=email, password="pw12345678", role=role)


class JobApplicationCRUDTests(APITestCase):
    def setUp(self):
        self.candidate = make_user("candidate-a@test.com")
        self.client.force_authenticate(self.candidate)
        self.list_url = reverse("application-list")

    def test_create_application(self):
        resp = self.client.post(
            self.list_url,
            {
                "company_name": "Acme Corp",
                "job_title": "Engineer",
                "job_description": "Build things.",
                "resume_text": "I build things.",
            },
        )
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertEqual(resp.data["owner"], self.candidate.id)
        self.assertEqual(resp.data["has_feedback"], False)
        self.assertTrue(JobApplication.objects.filter(owner=self.candidate).exists())

    def test_list_returns_only_own_applications(self):
        JobApplication.objects.create(
            owner=self.candidate,
            company_name="Own Co",
            job_title="Role",
            job_description="jd",
            resume_text="resume",
        )
        other = make_user("candidate-b@test.com")
        JobApplication.objects.create(
            owner=other,
            company_name="Other Co",
            job_title="Role",
            job_description="jd",
            resume_text="resume",
        )
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        companies = {row["company_name"] for row in resp.data}
        self.assertEqual(companies, {"Own Co"})

    def test_update_own_application(self):
        application = JobApplication.objects.create(
            owner=self.candidate,
            company_name="Old Co",
            job_title="Role",
            job_description="jd",
            resume_text="resume",
        )
        resp = self.client.patch(
            reverse("application-detail", args=[application.id]),
            {"company_name": "New Co"},
        )
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        application.refresh_from_db()
        self.assertEqual(application.company_name, "New Co")

    def test_delete_own_application(self):
        application = JobApplication.objects.create(
            owner=self.candidate,
            company_name="Delete Co",
            job_title="Role",
            job_description="jd",
            resume_text="resume",
        )
        resp = self.client.delete(reverse("application-detail", args=[application.id]))
        self.assertEqual(resp.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(JobApplication.objects.filter(id=application.id).exists())

    def test_requires_authentication(self):
        self.client.force_authenticate(None)
        resp = self.client.get(self.list_url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


class JobApplicationOwnershipTests(APITestCase):
    """Cross-candidate ownership: a candidate must never be able to
    read/edit/delete another candidate's application - the queryset scoping
    makes it invisible (404) before any object-level permission check."""

    def setUp(self):
        self.candidate_a = make_user("owner-a@test.com")
        self.candidate_b = make_user("owner-b@test.com")
        self.application_a = JobApplication.objects.create(
            owner=self.candidate_a,
            company_name="A Co",
            job_title="Role A",
            job_description="jd a",
            resume_text="resume a",
        )

    def test_other_candidate_gets_404_on_retrieve(self):
        self.client.force_authenticate(self.candidate_b)
        resp = self.client.get(reverse("application-detail", args=[self.application_a.id]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)

    def test_other_candidate_gets_404_on_update(self):
        self.client.force_authenticate(self.candidate_b)
        resp = self.client.patch(
            reverse("application-detail", args=[self.application_a.id]),
            {"company_name": "Hijacked"},
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.application_a.refresh_from_db()
        self.assertEqual(self.application_a.company_name, "A Co")

    def test_other_candidate_gets_404_on_delete(self):
        self.client.force_authenticate(self.candidate_b)
        resp = self.client.delete(reverse("application-detail", args=[self.application_a.id]))
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.assertTrue(JobApplication.objects.filter(id=self.application_a.id).exists())

    def test_other_candidate_not_in_list(self):
        self.client.force_authenticate(self.candidate_b)
        resp = self.client.get(reverse("application-list"))
        ids = {row["id"] for row in resp.data}
        self.assertNotIn(self.application_a.id, ids)


class JobApplicationAdminScopingTests(APITestCase):
    """An admin can list all applications across candidates, but cannot
    edit someone else's application."""

    def setUp(self):
        self.admin = make_user("admin-scope@test.com", role=User.Role.ADMIN)
        self.candidate_a = make_user("scope-a@test.com")
        self.candidate_b = make_user("scope-b@test.com")
        self.application_a = JobApplication.objects.create(
            owner=self.candidate_a,
            company_name="Scope A Co",
            job_title="Role A",
            job_description="jd a",
            resume_text="resume a",
        )
        self.application_b = JobApplication.objects.create(
            owner=self.candidate_b,
            company_name="Scope B Co",
            job_title="Role B",
            job_description="jd b",
            resume_text="resume b",
        )

    def test_admin_can_list_all_applications(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.get(reverse("application-list"))
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        ids = {row["id"] for row in resp.data}
        self.assertIn(self.application_a.id, ids)
        self.assertIn(self.application_b.id, ids)

    def test_admin_cannot_edit_other_candidates_application(self):
        self.client.force_authenticate(self.admin)
        resp = self.client.patch(
            reverse("application-detail", args=[self.application_a.id]),
            {"company_name": "Admin Hijack"},
        )
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)
        self.application_a.refresh_from_db()
        self.assertEqual(self.application_a.company_name, "Scope A Co")

    def test_candidate_does_not_see_other_candidates_in_list(self):
        self.client.force_authenticate(self.candidate_a)
        resp = self.client.get(reverse("application-list"))
        ids = {row["id"] for row in resp.data}
        self.assertIn(self.application_a.id, ids)
        self.assertNotIn(self.application_b.id, ids)
