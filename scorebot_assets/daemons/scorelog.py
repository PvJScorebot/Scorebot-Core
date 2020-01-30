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
from scorebot.utils import SCORE_EVENTS
from scorebot.utils.logger import log_info

LOG_NAME = "SCORING"


def init_daemon():
    return DaemonEntry("scorelog", 10, write_score_log, 30)


def write_score_log():
    for score_event in SCORE_EVENTS:
        log_info(LOG_NAME, score_event)
        SCORE_EVENTS.remove(score_event)
