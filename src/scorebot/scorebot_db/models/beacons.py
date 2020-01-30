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


class Compromise(Model):
    class Meta:
        db_table = "beacons"
        verbose_name = "Beacon"
        verbose_name_plural = "Beacons"

    ID = AutoField(
        db_column="id",
        verbose_name="Compromise ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    Host = ForeignKey(
        db_column="host",
        verbose_name="Compromise Host",
        null=False,
        on_delete=CASCADE,
        to="scorebot_db.Host",
        related_name="Beacons",
    )
    Owner = ForeignKey(
        db_column="owner",
        verbose_name="Compromise Identifier",
        null=False,
        on_delete=CASCADE,
        to="scorebot_db.Identifier",
        related_name="Beacons",
    )
