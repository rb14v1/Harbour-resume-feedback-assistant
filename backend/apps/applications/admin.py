from django.contrib import admin

from apps.applications.models import FeedbackResult, JobApplication


@admin.register(JobApplication)
class JobApplicationAdmin(admin.ModelAdmin):
    list_display = ["id", "owner", "company_name", "job_title", "created_at"]
    search_fields = ["company_name", "job_title", "owner__email"]
    list_filter = ["company_name"]


@admin.register(FeedbackResult)
class FeedbackResultAdmin(admin.ModelAdmin):
    list_display = ["id", "job_application", "generated_at"]
