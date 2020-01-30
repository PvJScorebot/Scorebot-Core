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


def convert_game(data):
    game = models.Game()
    game.name = data['game_name']
    game.save()
    #
    red = models.PlayerTeam()
    red.name = 'Redcell'
    red.offensive = True
    red.color = 16711686
    red.game = game
    red.save()
    #
    for blue in data['blueteams']:
        #
        blue_dns = models.DNS()
        blue_dns.ip = blue['dns']
        blue_dns.save()
        #
        blue_team = models.PlayerTeam()
        blue_team.game = game
        blue_team.name = blue['name']
        blue_team.save()
        #
        blue_range = models.Range()
        blue_range.subnet = '%s.0/24' % blue['nets'][0]
        blue_range.domain = '%s.com' % blue_team.name.lower().replace(' ', '-')
        blue_range.save()
        blue_range.dns.add(blue_dns)
        blue_range.save()
        #
        del blue_dns
        blue_range.team = blue_team
        blue_range.save()
        blue_team.save()
        #
        for host in blue['hosts']:
            blue_host = models.Host()
            blue_host.fqdn = host['hostname']
            blue_host.ip = '127.0.0.1'
            blue_host.range = blue_range
            blue_host.save()
            #
            for service in host['services']:
                blue_service = models.Service()
                try:
                    blue_service.port = int(service['port'])
                except ValueError:
                    blue_service.port = 80
                for protocol in SERVICE_PROTOCOLS:
                    if protocol[1].lower() == service['protocol'].lower():
                        blue_service.protocol = protocol[0]
                        break
                try:
                    blue_service.value = int(service['value'])
                except ValueError:
                    pass
                try:
                    blue_service.name = getservbyport(blue_service.port)
                except OSError:
                    blue_service.name = 'http'
                blue_service.application = blue_service.name
                blue_service.host = blue_host
                blue_service.save()
                #
                if 'content' in service:
                    blue_content = models.Content()
                    blue_content.format = 'imported'
                    blue_content.data = json.dumps(service['content'])
                    blue_content.save()
                    blue_content.service = blue_service
                    blue_content.save()
            if 'flags' in blue:
                for name, value in blue['flags'].items():
                    blue_flag = models.Flag()
                    blue_flag.name = slugify(name)
                    blue_flag.flag = '%s-%d' % (value['value'], randint(0, 255))
                    blue_flag.description = value['answer']
                    blue_flag.host = choice(blue_range.hosts.all())
                    blue_flag.save()
    return game

if len(argv) > 1:
    try:
        data = open(argv[1], 'r')
        try:
            data_json = loads(data.read())
            game = convert_game(data_json)
            print(game)
            print(dumps(game.json(), indent=4))
        except JSONDecodeError:
            print('Failed to read "%s"!' % argv[1])
        finally:
            data.close()
            del data
    except OSError:
        print('Failed to read "%s"!' % argv[1])
