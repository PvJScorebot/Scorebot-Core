#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

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
