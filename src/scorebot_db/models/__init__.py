#!/usr/bin/false
#
# Scorebotv4 - The Scorebot Project
# iDigitalFlame 2018
# The Scorebotbot / CTF Factory Team
#
# Django Database Models File

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

# EOF
