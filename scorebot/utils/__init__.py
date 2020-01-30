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

from scorebot.utils.logger import log_debug, log_error, log_info, log_warning

SCORE_EVENTS = []


def api_event(game_id, event_message):
    try:
        from scorebot_game.models import game_event_create

        game_event_create(game_id, event_message)
    except Exception as eventError:
        log_error("EVENT", str(eventError))


def api_info(api_name, message, request=None):
    if request is not None:
        client = get_ip(request)
        log_info("API", "%s (%s): %s" % (api_name.upper(), client, message))
        del client
    else:
        log_info("API", "%s (NO-IP): %s" % (api_name.upper(), message))


def api_error(api_name, message, request=None):
    if request is not None:
        client = get_ip(request)
        log_error("API", "%s (%s): %s" % (api_name.upper(), client, message))
        del client
    else:
        log_error("API", "%s (NO-IP): %s" % (api_name.upper(), message))


def api_debug(api_name, message, request=None):
    if request is not None:
        client = get_ip(request)
        log_debug("API", "%s (%s): %s" % (api_name.upper(), client, message))
        del client
    else:
        log_debug("API", "%s (NO-IP): %s" % (api_name.upper(), message))


def api_warning(api_name, message, request=None):
    if request is not None:
        client = get_ip(request)
        log_warning("API", "%s (%s): %s" % (api_name.upper(), client, message))
        del client
    else:
        log_warning("API", "%s (NO-IP): %s" % (api_name.upper(), message))


def api_score(score_id, score_type, score_name, score_value, score_data=None):
    SCORE_EVENTS.append(
        "%s,%s,%s,%s,%s" % (score_id, score_type, score_name, score_value, score_data)
    )
