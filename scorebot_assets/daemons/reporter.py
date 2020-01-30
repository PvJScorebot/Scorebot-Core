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

from django.utils import timezone

from daemon import DaemonEntry
from scorebot_game.models import Game
from scorebot.utils.logger import log_debug
from scorebot.utils.constants import CONST_GAME_GAME_RUNNING


def init_daemon():
    return DaemonEntry("reporter", 60, report_round, 120)


def report_round():
    log_debug("DAEMON", "Reporting on Scores..")
    games = Game.objects.filter(finish__isnull=True, status=CONST_GAME_GAME_RUNNING)
    if games is not None and len(games) > 0:
        check_time = timezone.now()
        for game in games:
            game.reporter_check(check_time)
    del games
