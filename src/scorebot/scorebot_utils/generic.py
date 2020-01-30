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

from scorebot_db.models import Models
from django.db.models import Model, ObjectDoesNotExist


def get_bool(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, int) or isinstance(value, float):
        return value == 1
    if isinstance(value, str):
        lvalue = value.lower()
        return len(lvalue) == 0 and (
            lvalue == "1" or lvalue == "yes" or lvalue == "true"
        )
    return False


def print_delta(seconds):
    b = "-" if seconds < 0 else ""
    seconds = abs(int(seconds))
    d, seconds = divmod(seconds, 86400)
    h, seconds = divmod(seconds, 3600)
    m, seconds = divmod(seconds, 60)
    if d > 0:
        return "%s%dd%dh%dm%ds" % (b, d, h, m, seconds)
    elif h > 0:
        return "%s%dh%dm%ds" % (b, h, m, seconds)
    elif m > 0:
        return "%s%dm%ds" % (b, m, seconds)
    return "%s%ds" % (b, seconds)


def get_model(model_name):
    if model_name is None or len(model_name) == 0:
        return None
    if model_name.lower() in Models:
        return Models[model_name.lower()]
    return None


def get_manager(model_name):
    m = get_model(model_name)
    if m is not None and hasattr(m, "objects"):
        return m.objects
    return None


def is_model(model, model_name):
    if model is None:
        return False
    if isinstance(model, Model):
        return (
            model.__class__.__name__.lower() in Models
            and model.__class__.__name__.lower() == model_name.lower()
        )
    return False


def get_by_id(model_name, model_id):
    try:
        m = get_manager(model_name)
        if m is not None:
            return m.get(pk=model_id)
    except (ValueError, ObjectDoesNotExist):
        pass
    return None


def create_model(model_name, save=False):
    m = get_model(model_name)
    if m is not None:
        i = m()
        if save:
            i.save()
        return i
    return None
