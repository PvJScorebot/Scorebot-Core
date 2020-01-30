#!/usr/bin/false
# Django API Views Utilities
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

from random import choice
from json import dumps  # , loads
from scorebot.util import authenticate, ip
from django.views.decorators.csrf import csrf_exempt
from scorebot import General, Authentication, Jobs, HTTP_GET, HTTP_POST
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from scorebot_db.models import AssignedMonitor, Job, PlayerTeam, Flag, Host, Port, Game
from scorebot.constants import JOB_MESSAGE_NO_HOSTS, MESSAGE_INVALID_METHOD, MESSAGE_MISSING_FIELD, \
                               FLAG_MESSAGE_STOLEN, FLAG_MESSAGE_NOT_EXIST, FLAG_MESSAGE_HINT, TEAM_MESSAGE_TOKEN, \
                               TEAM_MESSAGE_PORT_LIST, GAME_RUNNING
from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponse, HttpResponseNotFound, \
                        HttpResponseServerError, HttpResponseRedirect

from scorebot_db.models import Monitor


@csrf_exempt
@authenticate(perms='__SYS_MONITOR', methods=[HTTP_GET, HTTP_POST])
def job(request):
    if request.method == HTTP_GET:
        return Monitor.objects.create_job(request)
    client = ip(request)
    games, monitor, err = AssignedMonitor.objects.get_montiors(client, request.auth)
    if err is not None:
        return err
    if request.method == HTTP_GET:
        Authentication.debug('[%s] AssignedMonitor "%s" connected to request a Job, assigned to "%d" running Games.' % (
            client, monitor.name, len(games)
        ))
        General.info('[%s] AssignedMonitor "%s" connected to request a Job, assigned to "%d" running Games.' % (
            client, monitor.name, len(games)
        ))
        Jobs.debug('[%s] AssignedMonitor "%s": Connected and will attempt to pick "%d" times for a valid Job.' % (
            client, monitor.name, len(games)
        ))
        for game_num in range(0, len(games)):
            game = choice(games)
            Jobs.debug('[%s] AssignedMonitor "%s": Selection round "%s" selected Game "%s".' % (
                client, monitor.name, game_num, game.game.name
            ))
            job = Job.objects.new_job(game)
            if job is not None:
                Jobs.info('[%s] AssignedMonitor "%s": Job ID "%d" created for Host "%s"!' % (
                    client, monitor.name, job.id, job.host.path()
                ))
                return HttpResponse(status=201, content=dumps(job.json(), indent=4))
            del game
        del games
        Jobs.debug('[%s] AssignedMonitor "%s": Has no valid hosts to choose from!' % (client, monitor.name))
        return HttpResponse(status=204, content=JOB_MESSAGE_NO_HOSTS)
    elif request.method == HTTP_POST:
        return Job.objects.get_job(monitor, request)
    return HttpResponseBadRequest(content=MESSAGE_INVALID_METHOD)


@csrf_exempt
@authenticate()
def flag(request):
    if request.method == HTTP_POST:
        team, data, _, err = PlayerTeam.objects.get_team_json(request, field='token', offensive=True)
        if err is not None:
            return err
        client = ip(request)
        if 'flag' not in data:
            General.error('[%s] Client attempted to submit a Flag without the "flag" value!' % client)
            return HttpResponseBadRequest(content=MESSAGE_MISSING_FIELD.format(field='flag'))
        flag = Flag.objects.get_flag_query(team, data['flag'])
        del data
        if flag is None:
            General.error('[%s] Team "%s" attempted to submit a Flag that does not exist!' % (
                client, team.get_path()
            ))
            return HttpResponseNotFound(content=FLAG_MESSAGE_NOT_EXIST)
        if flag.stolen is not None:
            General.error('[%s] Team "%s" attempted to submit a Flag "%s" that was already captured!' % (
                client, team.get_path(), flag.get_path()
            ))
            return HttpResponse(status=204, content=FLAG_MESSAGE_STOLEN)
        hint, captured = flag.capture(team)
        if not captured:
            General.error('[%s] Team "%s" attempted to submit a Flag "%s" that was already captured!' % (
                client, team.get_path(), flag.get_path()
            ))
            return HttpResponse(status=204, content=FLAG_MESSAGE_STOLEN)
        return HttpResponse(status=200, content=FLAG_MESSAGE_HINT.format(hint=str(hint)))
    return HttpResponseBadRequest(content=MESSAGE_INVALID_METHOD)


@csrf_exempt
@authenticate()
def beacon(request):
    if request.method == HTTP_POST:
        team, data, token, err = PlayerTeam.objects.get_team_json(request, field='token', offensive=True, beacon=True)
        if err is not None:
            return err
        client = ip(request)
        if 'address' not in data:
            General.error('[%s] Client attempted to submit a Beacon without the "address" value!' % client)
            return HttpResponseBadRequest(content=MESSAGE_MISSING_FIELD.format(field='address'))
        return Host.objects.get_beacon(team, token, data['address'])
    return HttpResponseBadRequest(content=MESSAGE_INVALID_METHOD)


@csrf_exempt
@authenticate()
def register(request):
    if request.method == HTTP_POST:
        team, _, _, err = PlayerTeam.objects.get_team_json(request, field='token', offensive=True)
        if err is not None:
            return err
        General.debug('[%s] Client requested a Beacon Token for "%s".' % (ip(request), team.get_path()))
        return HttpResponse(status=201, content=TEAM_MESSAGE_TOKEN.format(token=str(team.add_beacon_token().uid)))
    return HttpResponseBadRequest(content=MESSAGE_INVALID_METHOD)


@csrf_exempt
@authenticate()
def ports(request):
    if request.method == HTTP_GET:
        return HttpResponse(content=TEAM_MESSAGE_PORT_LIST.format(list=','.join(Port.objects.get_list())))
    elif request.method == HTTP_POST:
        team, data, _, err = PlayerTeam.objects.get_team_json(request, field='token', offensive=True)
        if err is not None:
            return err
        if 'port' not in data:
            General.error('[%s] Client attempted to open a Beacon Port without the "port" value!!' % ip(request))
            return HttpResponseBadRequest(content=MESSAGE_MISSING_FIELD.format(field='port'))
        return Port.objects.get_port(team, data['port'])
    return HttpResponseBadRequest(content=MESSAGE_INVALID_METHOD)


@authenticate()
def mapper(request, gid):
    if request.method == HTTP_GET:
        General.debug('[%s] Client is request UUID mappings for Game ID "%s"!' % (ip(request), gid))
        try:
            game = Game.objects.get(id=int(gid), status=GAME_RUNNING)
        except (ObjectDoesNotExist, MultipleObjectsReturned, ValueError):
            return HttpResponseNotFound()
        return HttpResponse(status=200, content=dumps(game.get_team_list()))
    return HttpResponseBadRequest(content=MESSAGE_INVALID_METHOD)


def purchase(request):
    pass


def transfer(request):
    pass


def scoreboard(request, gid):
    if request.method == HTTP_GET:
        try:
            game = Game.objects.get(id=int(gid), status=GAME_RUNNING)
        except (ObjectDoesNotExist, MultipleObjectsReturned, ValueError):
            return HttpResponseNotFound()
        return HttpResponse(status=200, content=dumps(game.get_scoreboard(True)))
    return HttpResponseBadRequest(content=MESSAGE_INVALID_METHOD)
