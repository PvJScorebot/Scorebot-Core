#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from os.path import join
from django.conf import settings
from scorebot_utils.logging import Logger

LogGame = Logger("GAME", settings.LOG_LEVEL, join(settings.LOG_DIRECTORY, "game.log"))
LogHttp = Logger("HTTP", settings.LOG_LEVEL, join(settings.LOG_DIRECTORY, "http.log"))
LogAuth = Logger("AUTH", settings.LOG_LEVEL, join(settings.LOG_DIRECTORY, "auth.log"))
LogScore = Logger(
    "SCORE", settings.LOG_LEVEL, join(settings.LOG_DIRECTORY, "score.log")
)
LogGeneral = Logger(
    "GENERAL", settings.LOG_LEVEL, join(settings.LOG_DIRECTORY, "general.log")
)
