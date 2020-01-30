#!/usr/bin/false
# Scorebot UDP (Universal Development Platform)
#
# Copyright (C) 2020 iDigitalFlame
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published
# by the Free Software Foundation, either version 3 of the License, or
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Affero General Public License for more details.
#
# You should have received a copy of the GNU Affero General Public License
# along with this program.  If not, see <https://www.gnu.org/licenses/>.
#

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
