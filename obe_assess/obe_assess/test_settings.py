from .settings import *  # noqa: F401,F403

import os


DEBUG = True
PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": ":memory:",
    }
}

MEDIA_ROOT = str(BASE_DIR / ".test_media")
os.makedirs(MEDIA_ROOT, exist_ok=True)
LLM_SERVICE_URL = "http://testserver-llm"
