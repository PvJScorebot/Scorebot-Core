#!/usr/bin/false
# Django Database Models File
# Scorebot v4 - The Scorebot Project
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

from django.forms import ModelForm
from importlib import import_module
from scorebot import Models, General
from inspect import getmembers, isclass
from django.db.models.base import ModelBase
from django.contrib.admin import site, ModelAdmin

# Scorebot DB Imports
from scorebot_db.models.auth import *
from scorebot_db.models.game import *
from scorebot_db.models.team import *
from scorebot_db.models.score import *
from scorebot_db.models.store import *
from scorebot_db.models.range import *
from scorebot_db.models.player import *

for member in getmembers(import_module(__name__), isclass):
    if isinstance(member[1], ModelBase) and 'scorebot_db.' in member[1].__module__:
        admin = None
        hidden = False
        Models[member[0].lower()] = member[1]
        try:
            hidden = bool(getattr(member[1], 'hidden'))
        except AttributeError:
            hidden = False
        if not hidden:
            try:
                form = getattr(member[1], 'form')
                if issubclass(form, ModelForm):
                    admin = type('%sAdmin' % member[0], (ModelAdmin,), {'form': form, 'model': member[1]})
                del form
            except AttributeError:
                pass
            try:
                settings = getattr(member[1], 'Admin')

            except AttributeError:
                pass
        if not member[1]._meta.abstract and not hidden:
            site.register(member[1], admin_class=admin)
            General.debug('Scorebot Model "%s" loaded with Administrative Options.' % member[0])
        else:
            General.debug('Scorebot Model "%s" loaded.' % member[0])
        del admin
        del hidden
