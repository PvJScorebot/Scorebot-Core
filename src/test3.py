#!/usr/bin/python3

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