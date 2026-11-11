from django.shortcuts import get_object_or_404
from rest_framework import permissions, status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.applications.models import FeedbackResult, JobApplication
from apps.applications.serializers import FeedbackResultSerializer, JobApplicationSerializer
from apps.common.ai import generate_resume_feedback


class JobApplicationViewSet(viewsets.ModelViewSet):
    """Queryset scoping (per spec):
    - A candidate sees/edits only their own applications.
    - An admin can additionally LIST all applications across candidates,
      but cannot retrieve/edit/delete another candidate's application -
      those stay scoped to owner=request.user even for an admin, so a
      cross-candidate request 404s before any object-level permission
      check even runs.
    """

    serializer_class = JobApplicationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        qs = JobApplication.objects.select_related("owner", "feedback_result")
        if self.action == "list" and getattr(user, "role", None) == "admin":
            return qs
        return qs.filter(owner=user)

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"], url_path="generate-feedback")
    def generate_feedback(self, request, pk=None):
        """Triggers the single AI chat-completion call and creates/replaces
        the FeedbackResult for this application. Re-running replaces the
        existing result rather than creating a duplicate one-to-one row."""
        application = self.get_object()
        result = generate_resume_feedback(
            resume_text=application.resume_text,
            job_description=application.job_description,
        )
        feedback_result, _created = FeedbackResult.objects.update_or_create(
            job_application=application,
            defaults={
                "feedback": result["feedback"],
                "cover_letter_draft": result["cover_letter_draft"],
            },
        )
        return Response(
            FeedbackResultSerializer(feedback_result).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get"], url_path="feedback")
    def feedback(self, request, pk=None):
        """GET the generated feedback/cover-letter for this application, or
        404 if generate-feedback hasn't been run yet."""
        application = self.get_object()
        feedback_result = get_object_or_404(FeedbackResult, job_application=application)
        return Response(FeedbackResultSerializer(feedback_result).data)
