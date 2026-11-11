from django.conf import settings
from django.db import models


class JobApplication(models.Model):
    """A candidate's record of one job they're applying to: the job
    description and their own resume text, both kept as plain text (no
    file upload needed for this tool)."""

    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="job_applications",
    )
    company_name = models.CharField(max_length=255)
    job_title = models.CharField(max_length=255)
    job_description = models.TextField()
    resume_text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.job_title} @ {self.company_name} ({self.owner_id})"


class FeedbackResult(models.Model):
    """AI-generated feedback + cover letter draft for a JobApplication.
    One-to-one: regenerating replaces the existing result rather than
    creating a new row (see apps/applications/views.py generate-feedback)."""

    job_application = models.OneToOneField(
        JobApplication,
        on_delete=models.CASCADE,
        related_name="feedback_result",
    )
    feedback = models.TextField()
    cover_letter_draft = models.TextField()
    generated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Feedback for application {self.job_application_id}"
