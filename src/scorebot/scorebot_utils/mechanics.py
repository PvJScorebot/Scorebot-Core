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

from math import floor
from django.db.transaction import atomic
from django.core.exceptions import ValidationError
from scorebot_utils.restful import HttpError428, HttpError404
from scorebot_utils.constants import CREDIT_TYPES, TRANSFTER_STATUS
from scorebot_utils.generic import is_model, create_model, get_by_id
from django.db.models import (
    Model,
    CharField,
    AutoField,
    ForeignKey,
    DateTimeField,
    IntegerField,
    OneToOneField,
    BigIntegerField,
    PositiveSmallIntegerField,
    CASCADE,
    SET_NULL,
)


def host_compromise(attacker, host, token):
    pass


def flag_capture(team, flag):
    pass


def job_start(monitor):
    pass


def job_finish(monitor, job):
    pass


def token_register(team):
    pass


def token_trash(team):
    pass


def item_purchase(team, item):
    pass
