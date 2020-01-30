#!/usr/bin/python3
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

from sys import argv
from os import environ
from django import setup
from socket import getservbyport
from random import randint, choice
from django.utils.text import slugify
from json import loads, dumps, JSONDecodeError

environ['DJANGO_SETTINGS_MODULE'] = 'scorebot.settings'
environ.setdefault('DJANGO_SETTINGS_MODULE', 'scorebot.settings')

setup()

from scorebot import Models
from scorebot_db import models
from scorebot.constants import SERVICE_PROTOCOLS


#for t in models.ScoringTeam.objects.all():
#    print('%s\n%s' % (t.get_name(), dumps(t.stack.get_json_stack(), indent=4)))
print(dir(models.Game))

import scorebot_api.urls