#!/usr/bin/false
#
# Scorebotv4 - The Scorebot Project
# 2018 iDigitalFlame / The Scorebot / CTF Factory Team
#
# Djano WSGI Application

from os import environ
from django.core.wsgi import get_wsgi_application

environ.setdefault("DJANGO_SETTINGS_MODULE", "scorebot.settings")
application = get_wsgi_application()

# EOF
