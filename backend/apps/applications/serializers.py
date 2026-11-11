from rest_framework import serializers

from apps.applications.models import FeedbackResult, JobApplication


class JobApplicationSerializer(serializers.ModelSerializer):
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    has_feedback = serializers.SerializerMethodField()

    class Meta:
        model = JobApplication
        fields = [
            "id",
            "owner",
            "owner_email",
            "company_name",
            "job_title",
            "job_description",
            "resume_text",
            "created_at",
            "has_feedback",
        ]
        read_only_fields = ["id", "owner", "owner_email", "created_at", "has_feedback"]

    def get_has_feedback(self, obj):
        return hasattr(obj, "feedback_result")


class FeedbackResultSerializer(serializers.ModelSerializer):
    class Meta:
        model = FeedbackResult
        fields = ["id", "job_application", "feedback", "cover_letter_draft", "generated_at"]
        read_only_fields = fields
