from pathlib import Path
import os

from dotenv import load_dotenv




BASE_DIR = Path(__file__).resolve().parent.parent



# ENVIRONMENT VARIABLES


load_dotenv(BASE_DIR / ".env")


# SECURITY


SECRET_KEY = os.getenv(
    "SECRET_KEY",
    "django-insecure-change-this-in-production",
)

DEBUG = os.getenv("DEBUG", "True").lower() == "true"

ALLOWED_HOSTS = [
    h.strip()
    for h in os.getenv("ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")
    if h.strip()
]

# Render sets RENDER_EXTERNAL_HOSTNAME automatically for the deployed
# service — add it so the app works there without manual config.
RENDER_EXTERNAL_HOSTNAME = os.getenv("RENDER_EXTERNAL_HOSTNAME")
if RENDER_EXTERNAL_HOSTNAME:
    ALLOWED_HOSTS.append(RENDER_EXTERNAL_HOSTNAME)

CSRF_TRUSTED_ORIGINS = [
    o.strip()
    for o in os.getenv("CSRF_TRUSTED_ORIGINS", "").split(",")
    if o.strip()
]
if RENDER_EXTERNAL_HOSTNAME:
    CSRF_TRUSTED_ORIGINS.append(f"https://{RENDER_EXTERNAL_HOSTNAME}")

# Production security (only enforced when DEBUG is off — i.e. once
# deployed, not during local development)
if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True


# EMAIL

# Development default: prints emails to the terminal instead of
# sending them, so registration/verification can be tested without
# real SMTP credentials. For production, set these in your .env
# (or hosting provider's environment variables) and switch
# EMAIL_BACKEND to "django.core.mail.backends.smtp.EmailBackend":
#
#   EMAIL_HOST=smtp.gmail.com
#   EMAIL_PORT=587
#   EMAIL_USE_TLS=True
#   EMAIL_HOST_USER=your@gmail.com
#   EMAIL_HOST_PASSWORD=<app password>
#   DEFAULT_FROM_EMAIL=your@gmail.com

EMAIL_BACKEND = os.getenv(
    "EMAIL_BACKEND",
    "django.core.mail.backends.console.EmailBackend",
)
EMAIL_HOST = os.getenv("EMAIL_HOST", "")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", "587"))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS", "True").lower() == "true"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER", "")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD", "")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL", "no-reply@cvdm.local")

ALLOWED_HOSTS = os.getenv(
    "ALLOWED_HOSTS",
    "127.0.0.1,localhost",
).split(",")



# APPLICATIONS


INSTALLED_APPS = [
    # Django
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",

    # Third-party
    "rest_framework",
    "rest_framework.authtoken",

    # Local apps
    "accounts",
    "content",
    "versions",
    "workflow",
    "audit",
    "notifications",
    "ai_review",
    "dashboard",
]


# MIDDLEWARE


MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]



# URL CONFIGURATION


ROOT_URLCONF = "config.urls"

LOGIN_URL = "/dashboard/login/"
LOGIN_REDIRECT_URL = "/dashboard/"


# TEMPLATES


TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]





WSGI_APPLICATION = "config.wsgi.application"
ASGI_APPLICATION = "config.asgi.application"





# DATABASE


import dj_database_url

DATABASES = {
    "default": dj_database_url.config(
        default=f"sqlite:///{BASE_DIR / 'db.sqlite3'}",
        conn_max_age=600,
    )
}



# PASSWORD VALIDATION


AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "UserAttributeSimilarityValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "MinimumLengthValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "CommonPasswordValidator"
        ),
    },
    {
        "NAME": (
            "django.contrib.auth.password_validation."
            "NumericPasswordValidator"
        ),
    },
]


# INTERNATIONALIZATION


LANGUAGE_CODE = "en-us"

TIME_ZONE = "Asia/Kolkata"

USE_I18N = True

USE_TZ = True



# STATIC FILES


STATIC_URL = "static/"

STATICFILES_DIRS = [
    BASE_DIR / "static",
] if (BASE_DIR / "static").exists() else []

STATIC_ROOT = BASE_DIR / "staticfiles"

STORAGES = {
    "staticfiles": {
        "BACKEND": "whitenoise.storage.CompressedManifestStaticFilesStorage",
    },
}


# MEDIA FILES


MEDIA_URL = "media/"

MEDIA_ROOT = BASE_DIR / "media"


# DEFAULT PRIMARY KEY


DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"




REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        "rest_framework.permissions.IsAuthenticated",
    ],
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "rest_framework.authentication.TokenAuthentication",
        "rest_framework.authentication.SessionAuthentication",
    ],
}


# ROLES

CVDM_ROLES = [
    "Author",
    "Reviewer",
    "Editor",
    "Admin",
]

# Roles a user is allowed to self-select at registration time.
# "Admin" is intentionally excluded — admins should be promoted manually
# (e.g. via Django admin or the create_roles + manage command flow),
# not granted by anyone who fills in a signup form.
CVDM_SELF_ASSIGNABLE_ROLES = [
    "Author",
    "Reviewer",
    "Editor",
]