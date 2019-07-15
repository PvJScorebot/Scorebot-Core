import os

from random import choice
from scorebot.utils.logger import log_init
from string import ascii_letters, digits, punctuation

DEBUG = True
USE_TZ = True
USE_I18N = True
USE_L10N = True
TIME_ZONE = "UTC"
DUMP_DATA = True
TWITTER_API = {
    "ENABLED": True,
    "CONSUMER_KEY": "",
    "ACCESS_TOKEN": "",
    "CONSUMER_SECRET": "",
    "ACCESS_TOKEN_SECRET": "",
}
APPEND_SLASH = False
SBE_VERSION = "v3.3.3"
MEDIA_URL = "/upload/"
ALLOWED_HOSTS = ["*"]
LANGUAGE_CODE = "en-us"
STATIC_URL = "/static/"
LOG_DIR = "/tmp/scorebot3"
ROOT_URLCONF = "scorebot.urls"
DUMP_DIR = "/tmp/scorebot3_dumps"
WSGI_APPLICATION = "scorebot.wsgi.application"
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MEDIA_ROOT = os.path.join(BASE_DIR, "scorebot_media")
# Going to use a dynamic key here, as we dont want to hard code it in.
# However, if you want to set a key, edit it here. Randoms are only generated if
# len(SECRET_KEY) == 0
SECRET_KEY = ""
if len(SECRET_KEY) == 0:
    SECRET_KEY = "".join(
        [choice(ascii_letters + digits + punctuation) for n in range(64)]
    )
PLUGIN_DIR = os.path.join(BASE_DIR, "scorebot_assets", "plugins")
DAEMON_DIR = os.path.join(BASE_DIR, "scorebot_assets", "daemons")
log_init(LOG_DIR, "DEBUG")
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "scorebot_core",
    "scorebot_grid",
    "scorebot_game",
    "scorebot_api",
]
MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]
TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [os.path.join(BASE_DIR, "scorebot_html")],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ]
        },
    }
]
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": os.path.join(BASE_DIR, "scorebot_data", "db.sqlite3"),
    }
}
if "SBE_SQLLITE" not in os.environ or os.environ.get("SBE_SQLLITE", default="0") == "0":
    DATABASES["default"] = {
        "ENGINE": "django.db.backends.mysql",
        "NAME": "scorebot_db",
        "HOST": "scorebot-database",
        "USER": "scorebot",
        "PASSWORD": "password",
    }
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"
    },
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]
