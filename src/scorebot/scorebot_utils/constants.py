#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019


from random import randint


def NewColor():
    return ("#%s" % hex(randint(0, 0xFFFFFF))).replace("0x", "")


MULTI_RESULT_KEY = "list"

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
