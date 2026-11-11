# Demo-data seed migration.
#
# Creates two demo users (a candidate and an admin) and ~9 JobApplication
# rows for the demo candidate spanning different roles/companies, most with
# a generated FeedbackResult, so the app has something realistic to look at
# immediately after `migrate` - no separate fixtures/management command
# needed.
#
# Idempotent via get_or_create: running `migrate` again (or in CI) never
# creates duplicate users or applications.
#
# This calls the real apps.common.ai.generate_resume_feedback() function
# (not a hardcoded string) so the seeded feedback/cover-letters are exactly
# what a fresh `manage.py migrate` run produces for anyone - at migrate time
# there is no OPENAI_API_KEY configured, so this runs in the deterministic
# stub path (see apps/common/ai.py).
from django.db import migrations

DEMO_PASSWORD = "demo12345"

APPLICATIONS = [
    {
        "company_name": "Initech Software",
        "job_title": "Backend Software Engineer",
        "job_description": (
            "We are looking for a Backend Software Engineer with strong Python "
            "and Django experience to build and scale our REST APIs. You will "
            "work with PostgreSQL, design database schemas, write automated "
            "tests, and collaborate with frontend engineers on API contracts. "
            "3+ years of experience with Python, Django or Flask, and SQL "
            "databases required. Experience with Docker and CI/CD pipelines "
            "is a strong plus."
        ),
        "resume_text": (
            "Software engineer with 4 years of experience building REST APIs "
            "in Python using Django and Flask. Designed PostgreSQL schemas for "
            "a multi-tenant SaaS product, wrote unit and integration tests "
            "with pytest, and set up GitHub Actions CI pipelines. Comfortable "
            "with Docker-based local development and deployment."
        ),
        "generate": True,
    },
    {
        "company_name": "Global Retail Co",
        "job_title": "Data Analyst",
        "job_description": (
            "Seeking a Data Analyst to own weekly sales reporting, build "
            "dashboards in SQL and Tableau, and partner with merchandising "
            "teams to identify trends. Strong SQL skills and experience with "
            "Excel or BI tools required. Experience with Python/pandas is a "
            "plus for ad-hoc analysis."
        ),
        "resume_text": (
            "Analyst with 2 years of experience writing complex SQL queries "
            "against a retail data warehouse, building recurring reports in "
            "Excel, and presenting findings to merchandising stakeholders. "
            "Learning Tableau and Python/pandas for ad-hoc analysis projects."
        ),
        "generate": True,
    },
    {
        "company_name": "Fintech Horizon",
        "job_title": "Product Manager",
        "job_description": (
            "Product Manager needed to own the roadmap for our payments "
            "platform. Responsibilities include writing PRDs, running "
            "discovery interviews with merchants, prioritizing the backlog "
            "with engineering, and tracking adoption metrics. 3+ years of B2B "
            "product management experience required, fintech/payments domain "
            "experience strongly preferred."
        ),
        "resume_text": (
            "Product manager with 3 years of experience shipping B2B SaaS "
            "features. Ran customer discovery interviews, wrote PRDs, and "
            "worked closely with engineering on sprint prioritization. No "
            "direct payments industry experience but strong track record in "
            "subscription billing features."
        ),
        "generate": True,
    },
    {
        "company_name": "CloudScale Systems",
        "job_title": "DevOps Engineer",
        "job_description": (
            "DevOps Engineer to manage Kubernetes clusters, build Terraform "
            "infrastructure-as-code, and improve CI/CD pipeline reliability "
            "across AWS environments. Required: Kubernetes, Terraform, AWS, "
            "and strong scripting (Python or Bash). Experience with "
            "observability tooling (Prometheus/Grafana) is a plus."
        ),
        "resume_text": (
            "Systems engineer with 5 years managing AWS infrastructure. "
            "Deep Terraform experience provisioning VPCs, EC2 and RDS. "
            "Built Jenkins and GitHub Actions pipelines for a dozen "
            "microservices. Limited hands-on Kubernetes exposure so far, "
            "mostly ECS-based deployments. Comfortable scripting in Bash and "
            "Python."
        ),
        "generate": True,
    },
    {
        "company_name": "Designly Studio",
        "job_title": "UX Designer",
        "job_description": (
            "UX Designer to lead end-to-end design for our mobile app, "
            "including user research, wireframing, prototyping in Figma, and "
            "running usability tests. 2+ years of mobile product design "
            "experience and a strong portfolio required."
        ),
        "resume_text": (
            "Product designer with 2 years of experience designing responsive "
            "web applications in Figma, running moderated usability tests, "
            "and collaborating with PMs on user flows. Limited native mobile "
            "app design experience but strong fundamentals in interaction "
            "design and design systems."
        ),
        "generate": True,
    },
    {
        "company_name": "BrightAds Media",
        "job_title": "Marketing Manager",
        "job_description": (
            "Marketing Manager to lead paid acquisition campaigns across "
            "Google and Meta ads, own the marketing budget, and report on "
            "CAC/LTV to leadership. Required: 3+ years running paid digital "
            "campaigns, strong analytical skills, and experience with "
            "marketing analytics tools."
        ),
        "resume_text": (
            "Marketing specialist with 3 years running Google Ads and Meta "
            "Ads campaigns for e-commerce clients, tracking CAC and LTV in "
            "spreadsheets and Google Analytics, and presenting monthly "
            "performance reviews to clients."
        ),
        "generate": True,
    },
    {
        "company_name": "StartupX Labs",
        "job_title": "Full-Stack Developer",
        "job_description": (
            "Full-stack developer to build features across our React "
            "frontend and Node.js/Express backend, working in a small, "
            "fast-moving team. Required: React, TypeScript, Node.js, and "
            "comfort working directly with product and design."
        ),
        "resume_text": (
            "Developer with 3 years of experience building React/TypeScript "
            "frontends and Express backends for early-stage startups. "
            "Comfortable owning features end-to-end from design handoff to "
            "deployment, and working directly with founders on product "
            "decisions."
        ),
        "generate": True,
    },
    {
        "company_name": "BuildCo Construction",
        "job_title": "Project Coordinator",
        "job_description": (
            "Project Coordinator to support scheduling, vendor communication, "
            "and budget tracking for residential construction projects. "
            "Experience with MS Project or similar scheduling tools and "
            "strong organizational skills required."
        ),
        "resume_text": (
            "Administrative coordinator with 1 year of experience tracking "
            "project timelines in spreadsheets, communicating with vendors, "
            "and supporting budget reconciliation for a small events company. "
            "No direct construction industry experience."
        ),
        # Intentionally left without generated feedback yet, so the seed
        # data also demonstrates the "not yet generated" state.
        "generate": False,
    },
    {
        "company_name": "SaaSHub Inc",
        "job_title": "Customer Success Manager",
        "job_description": (
            "Customer Success Manager to own onboarding and renewals for a "
            "portfolio of mid-market SaaS accounts, running quarterly "
            "business reviews and identifying expansion opportunities. 2+ "
            "years of SaaS customer success or account management experience "
            "required."
        ),
        "resume_text": (
            "Account manager with 2 years supporting mid-market SaaS "
            "customers through onboarding, quarterly business reviews, and "
            "renewal conversations. Tracked account health scores and "
            "flagged expansion opportunities to the sales team."
        ),
        # Also left without generated feedback yet.
        "generate": False,
    },
]


def seed_demo_data(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    JobApplication = apps.get_model("applications", "JobApplication")
    FeedbackResult = apps.get_model("applications", "FeedbackResult")

    from django.contrib.auth.hashers import make_password

    # Historical models don't expose set_password()/the custom manager, so
    # hash the shared demo password manually with Django's hasher - this
    # stays migration-safe.
    hashed_password = make_password(DEMO_PASSWORD)

    candidate, _ = User.objects.get_or_create(
        email="candidate@example.com",
        defaults={
            "full_name": "Jordan Candidate",
            "role": "candidate",
            "password": hashed_password,
            "is_active": True,
        },
    )
    User.objects.get_or_create(
        email="admin@example.com",
        defaults={
            "full_name": "Avery Admin",
            "role": "admin",
            "password": hashed_password,
            "is_active": True,
            "is_staff": True,
        },
    )

    # Import lazily, after Django app registry is available, and call the
    # real dual-path AI function - at migrate time there is no
    # OPENAI_API_KEY, so this runs in deterministic stub mode.
    from apps.common.ai import generate_resume_feedback

    for entry in APPLICATIONS:
        application, created = JobApplication.objects.get_or_create(
            owner=candidate,
            company_name=entry["company_name"],
            job_title=entry["job_title"],
            defaults={
                "job_description": entry["job_description"],
                "resume_text": entry["resume_text"],
            },
        )
        if not entry["generate"]:
            continue
        if FeedbackResult.objects.filter(job_application=application).exists():
            continue
        result = generate_resume_feedback(
            resume_text=application.resume_text,
            job_description=application.job_description,
        )
        FeedbackResult.objects.create(
            job_application=application,
            feedback=result["feedback"],
            cover_letter_draft=result["cover_letter_draft"],
        )


def unseed_demo_data(apps, schema_editor):
    User = apps.get_model("accounts", "User")
    User.objects.filter(
        email__in=["candidate@example.com", "admin@example.com"]
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("accounts", "0001_initial"),
        ("applications", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_demo_data, unseed_demo_data),
    ]
