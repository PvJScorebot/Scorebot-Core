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

from os import listdir
from os.path import dirname
from scorebot_db import models
from django.forms import ModelForm
from importlib import import_module
from django.db import InternalError
from scorebot_utils import log_general
from django.db.models.base import ModelBase
from django.contrib.admin import site, ModelAdmin

Models = dict()

try:
    for f in listdir(dirname(models.__file__)):
        if len(f) > 0 and f[0] != "_":
            log_general.debug("MODELS: Attempting to load file '%s'.." % f)
            c = import_module("scorebot_db.models.%s" % f.replace(".py", ""))
            for n, m in c.__dict__.items():
                if (
                    issubclass(m.__class__, ModelBase)
                    and "scorebot_db.models" in m.__module__
                ):
                    Models[n.lower()] = m
                    if hasattr(m, "__hidden__"):
                        if getattr(m, "__hidden__"):
                            log_general.debug(
                                "MODELS: Skipping hidden model '%s'." % m.__name__
                            )
                            continue
                    if hasattr(m, "_meta"):
                        u = getattr(m, "_meta")
                        if hasattr(u, "abstract"):
                            if getattr(u, "abstract"):
                                log_general.debug(
                                    "MODELS: Skipping abstract model '%s'." % m.__name__
                                )
                                continue
                    x = None
                    v = None
                    a = None
                    if hasattr(m, "Form"):
                        a = getattr(m, "Form")
                    if hasattr(m, ("%sForm" % m.__name__)):
                        a = getattr(m, ("%sForm" % m.__name__))
                    if hasattr(m, "Admin"):
                        v = getattr(m, "Admin")
                    if hasattr(m, ("%sAdmin" % m.__name__)):
                        v = getattr(m, ("%sAdmin" % m.__name__))
                    if a is not None and issubclass(a, ModelForm):
                        x = type(
                            "%sAdmin" % m.__name__,
                            (ModelAdmin,),
                            {"form": a, "model": m},
                        )
                    elif v is not None and issubclass(v, ModelAdmin):
                        x = v
                    if x is not None:
                        log_general.debug(
                            "MODELS: Registering model '%s' with Admin plugin."
                            % m.__name__
                        )
                    else:
                        log_general.debug(
                            "MODELS: Registering model '%s'." % m.__name__
                        )
                    site.register(m, admin_class=x)
except Exception as err:
    log_general.error("MODELS: Model registration error!", err=err)
    raise InternalError(err)
