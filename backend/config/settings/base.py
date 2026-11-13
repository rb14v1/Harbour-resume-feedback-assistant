"""
Base settings shared by all environments.
"""
from datetime import timedelta
from pathlib import Path

from decouple import Csv, config

BASE_DIR = Path(__file__).resolve().parent.parent.parent

SECRET_KEY = config("DJANGO_SECRET_KEY", default="dev-insecure-secret-key-change-me")
DEBUG = config("DJANGO_DEBUG", default=False, cast=bool)
ALLOWED_HOSTS = config("DJANGO_ALLOWED_HOSTS", default="localhost,127.0.0.1", cast=Csv())

AUTH_USER_MODEL = "accounts.User"

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    # third party
    "rest_framework",
    "rest_framework_simplejwt",
    "rest_framework_simplejwt.token_blacklist",
    "corsheaders",
    # local apps
    "apps.accounts",
    "apps.applications",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "corsheaders.middleware.CorsMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"

# ---------------------------------------------------------------------------
# Database
#
# Real deployments (docker-compose / prod) use Postgres - plain postgres:16,
# no extensions (this app has no vector/embedding search, unlike some
# sibling AI apps).
#
# DEV-ONLY OVERRIDE: when USE_SQLITE=True is set in the environment, we fall
# back to SQLite so `manage.py check`, `makemigrations` and `test` can run on
# a machine with no local Postgres/Docker available. Same documented pattern
# as the sibling leave-attendance / perf-okr-platform apps.
# ---------------------------------------------------------------------------
USE_SQLITE = config("USE_SQLITE", default=True, cast=bool)

if USE_SQLITE:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "dev-sqlite.db",
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": config("POSTGRES_DB", default="resume_feedback_assistant"),
            "USER": config("POSTGRES_USER", default="resume_feedback_assistant"),
            "PASSWORD": config("POSTGRES_PASSWORD", default="resume_feedback_assistant"),
            "HOST": config("POSTGRES_HOST", default="localhost"),
            "PORT": config("POSTGRES_PORT", default="5432"),
        }
    }

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]

LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "TEST_REQUEST_DEFAULT_FORMAT": "json",
}

SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=30),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
}

CORS_ALLOWED_ORIGINS = config(
    "CORS_ALLOWED_ORIGINS",
    default="http://localhost:5173,http://127.0.0.1:5173",
    cast=Csv(),
)
CORS_ALLOW_CREDENTIALS = True

# ---------------------------------------------------------------------------
# AI (single chat-completion call) - see apps/common/ai.py for the dual-path
# (real OpenAI call vs. deterministic offline stub) implementation.
#
# IMPORTANT: this app's default chat model is gpt-5.4-mini, deliberately
# different from the gpt-5.6-sol default used by several sibling AI apps
# (per the batch's intent to exercise different model names across apps).
# ---------------------------------------------------------------------------
OPENAI_CHAT_MODEL = config("OPENAI_CHAT_MODEL", default="gpt-5.4-mini")
OPENAI_API_KEY = config("OPENAI_API_KEY", default="")

# Where the OpenAI-compatible API lives. Empty means api.openai.com, which is
# the stock client's own default and what this app used before.
#
# Set it to point the same client at an Azure OpenAI resource instead: Azure
# serves an OpenAI-compatible surface at <resource-endpoint>/openai/v1/, which
# the stock `openai` package accepts with the resource key as its api_key. No
# separate AzureOpenAI client and no code branch is needed.
#
# A deployment platform that provisions Azure OpenAI fills this in for us -
# OPENAI_BASE_URL is a name such platforms recognise and rewrite to their own
# resource. Declared empty here so it is visibly part of this app's contract:
# without it, a platform-supplied Azure key is sent to api.openai.com and is
# rejected.
OPENAI_BASE_URL = config("OPENAI_BASE_URL", default="")
