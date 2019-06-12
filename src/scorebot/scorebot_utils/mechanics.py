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
