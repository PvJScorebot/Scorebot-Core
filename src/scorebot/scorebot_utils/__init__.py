#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from os.path import join
from random import randint
from django.conf import settings
from scorebot_utils.logging import Logger

options_cache = dict()

log_game = Logger("GAME", settings.LOG_LEVEL, join(settings.LOG_DIRECTORY, "game.log"))
log_http = Logger("HTTP", settings.LOG_LEVEL, join(settings.LOG_DIRECTORY, "http.log"))
log_auth = Logger("AUTH", settings.LOG_LEVEL, join(settings.LOG_DIRECTORY, "auth.log"))
log_Score = Logger(
    "SCORE", settings.LOG_LEVEL, join(settings.LOG_DIRECTORY, "score.log")
)
log_general = Logger(
    "GENERAL", settings.LOG_LEVEL, join(settings.LOG_DIRECTORY, "general.log")
)


def invalidate_cache(game_id):
    if not settings.CACHE_OPTIONS:
        return None
    if game_id in options_cache:
        del options_cache[game_id]
    return None


def get_cached_option(game_id, name):
    if not settings.CACHE_OPTIONS:
        return None
    if game_id not in options_cache:
        return None
    if name in options_cache[game_id]:
        if randint(0, 100) == 0:
            del options_cache[game_id][name]
            return None
        return options_cache[game_id][name]
    return None


def set_cached_option(game_id, name, value):
    if not settings.CACHE_OPTIONS:
        return None
    if game_id not in options_cache:
        options_cache[game_id] = dict()
    options_cache[game_id][name] = value
    return value
