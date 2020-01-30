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

from random import randint


def new_color():
    return ("#%s" % hex(randint(0, 0xFFFFFF))).replace("0x", "")


# HTTP Methods
HTTP_GET = "GET"
HTTP_PUT = "PUT"
HTTP_POST = "POST"
HTTP_DELETE = "DELETE"

# RestFul Constangts
REST_FUNC_GET = "rest_get"
REST_FUNC_PUT = "rest_put"
REST_FUNC_JSON = "rest_json"
REST_FUNC_POST = "rest_post"
REST_FUNC_DLETE = "rest_delete"
REST_RESULT_KEY = "list"
REST_FUNC_EXPOSES = "__exposes__"
REST_FUNC_PARENTS = "__parents__"

# HTTP Error Messages
ERROR_400 = "sbe-error-invalreq"
ERROR_401 = "sbe-error-unauthed"
ERROR_403 = "sbe-error-forbiddn"
ERROR_404 = "sbe-error-notfound"
ERROR_405 = "sbe-error-nomethod"
ERROR_409 = "sbe-error-conflict"
ERROR_428 = "sbe-error-precondt"
ERROR_500 = "sbe-error-internal"

# HTTP Error Detail Messages
ERROR_401_MESSAGE = "please provide a valid authentication token"
ERROR_403_MESSAGE = "you do not have the permissions required, need '{permissions}'"
ERROR_404_MESSAGE = "model or resource at uri '{requested}' not found"
ERROR_405_MESSAGE = "method {method} is not accepted here"
ERROR_428_MESSAGE = "condition '{condition}' failed"
ERROR_404_MESSAGE_ALT = "requested resource not avaliable"

# Score Constants
HOST_DEFAULT_VALUE = 100
SERVICE_DEFAULT_VALUE = 100
CONTENT_DEFAULT_VALUE = 100

# Model Constants
GAME_MODES = (
    (0, "Red vs Blue"),
    (1, "Blue vs Blue"),
    (2, "King"),
    (4, "High Ground"),
    (5, "Score Attack"),
)
GAME_STATUS = (
    (0, "Not Started"),
    (1, "Running"),
    (2, "Paused"),
    (3, "Completed"),
    (4, "Stopped"),
    (5, "Archivd"),
)
GAME_TEAM_GOLD = "Gold Team"
GAME_TEAM_GRAY = "Gray Team"

CREDIT_TYPES = (
    (0, "Correction"),
    (1, "Transfer"),
    (2, "Purchase"),
    (3, "Payment"),
    (4, "Health"),
    (5, "Beacon"),
    (6, "Flag"),
    (7, "Ticket"),
    (8, "Achivement"),
    (9, "Event"),
)
TRANSFTER_STATUS = ((0, "Pending"), (1, "Approved"), (2, "Rejected"))

PORT_TYPES = ((0, "TCP"), (1, "UDP"), (2, "ICMP"))

SERVICE_STATUS = (
    (0, "Closed"),
    (1, "Open"),
    (2, "Rejected"),
    (3, "Unreachable"),
    (4, "Invalid"),
)

OPTION_DEFAULTS = {
    "host.tolerance": 75,
    "service.bonus.multipler": 2,
    "content.tolerance": 75,
}
