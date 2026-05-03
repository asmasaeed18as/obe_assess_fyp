from .settings import *  # noqa: F401,F403


DEBUG = True
SECRET_KEY = "local-dev-secret-key"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": "obe_db",
        "USER": "obe_user",
        "PASSWORD": "obe_password",
        "HOST": "localhost",
        "PORT": "5432",
    }
}

LLM_SERVICE_URL = "http://127.0.0.1:8001"
