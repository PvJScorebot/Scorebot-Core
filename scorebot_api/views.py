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

import json
import uuid
import random

from datetime import timedelta
from django.utils import timezone
from scorebot.utils import logger
from django.db.transaction import atomic
from scorebot_grid.models import Flag, Host
from django.shortcuts import render, reverse
from scorebot_api.forms import Scorebot2ImportForm, CreateEventForm, EventMessageForm
from django.views.decorators.csrf import csrf_exempt
from netaddr import IPNetwork, IPAddress, AddrFormatError
from scorebot.utils.constants import CONST_GAME_GAME_RUNNING
from scorebot_core.models import Monitor, token_create_new, Token
from django.contrib.admin.views.decorators import staff_member_required
from scorebot.utils.general import authenticate, game_team_from_token, dump_data
from scorebot.utils import (
    api_info,
    api_debug,
    api_error,
    api_warning,
    api_score,
    api_event,
)
from scorebot_game.models import (
    GameMonitor,
    Job,
    Game,
    GamePort,
    GameTeam,
    GameCompromise,
    Purchase,
    GameCompromiseHost,
    GameTicket,
    GameEvent,
)
from django.http import (
    HttpResponseBadRequest,
    HttpResponseForbidden,
    HttpResponse,
    HttpResponseNotFound,
    HttpResponseServerError,
    HttpResponseRedirect,
)


METHOD_GET = "GET"
METHOD_POST = "POST"


class ScorebotAPI:
    @staticmethod
    @csrf_exempt
    @authenticate()
    def api_job(request):
        try:
            monitor = Monitor.objects.get(access=request.authentication)
        except Monitor.DoesNotExist:
            api_error(
                "JOB",
                "Attempted to request a Job without Monitor permissions!",
                request,
            )
            return HttpResponseForbidden(
                '{"message": "SBE API: Only registered Monitors may request Jobs!"}'
            )
        game_monitors = GameMonitor.objects.filter(
            monitor=monitor, game__status=CONST_GAME_GAME_RUNNING
        )
        if len(game_monitors) == 0:
            api_error(
                "JOB",
                'Monitor "%s" attempted to request a Job but is not registered in any Games!'
                % monitor.name,
                request,
            )
            return HttpResponseForbidden(
                '{"message": "SBE API: Not registered with any running Games!"}'
            )
        if request.method == METHOD_GET:
            games_max = len(game_monitors)
            api_debug(
                "JOB",
                'Monitor "%s" is requesting a Job and has "%d" Games to choose from!'
                % (monitor.name, games_max),
                request,
            )
            for game_round in range(0, games_max):
                game_monitor = random.choice(game_monitors)
                api_debug(
                    "JOB",
                    'Monitor "%s" has picked game "%s"!'
                    % (monitor.name, game_monitor.game.name),
                    request,
                )
                job_data = game_monitor.create_job()
                if job_data:
                    dump_data("job-%s" % game_monitor.monitor.name, job_data)
                    del game_monitor
                    return HttpResponse(status=201, content=job_data)
                del game_monitor
            del monitor
            del games_max
            del game_monitors
            return HttpResponse(
                status=204,
                content='{"message": "SBE API: No Hosts available! Try later."}',
            )
        elif request.method == METHOD_POST:
            api_debug(
                "JOB", 'Monitor "%s" is submitting a Job!' % monitor.name, request
            )
            try:
                decoded_data = request.body.decode("UTF-8")
            except UnicodeDecodeError:
                api_error(
                    "JOB",
                    'Job submitted by Monitor "%s" is not encoded properly!'
                    % monitor.name,
                    request,
                )
                return HttpResponseBadRequest(
                    '{"message": "SBE API: Incorrect encoding, please use UTF-8!"}'
                )
            try:
                job_json = json.loads(decoded_data)
                del decoded_data
            except json.decoder.JSONDecodeError:
                api_debug(
                    "JOB",
                    'Job submitted by Monitor "%s" is not in a valid JSON format!'
                    % monitor.name,
                    request,
                )
                return HttpResponseBadRequest(
                    '{"message": "SBE API: Not in a valid JSON format!"}'
                )
            try:
                job = Job.objects.get(id=int(job_json["id"]))
                if job.finish is not None:
                    logger.warning(
                        "SBE-JOB",
                        'Monitor "%s" returned a completed Job!' % monitor.name,
                    )
                    return HttpResponseBadRequest(
                        '{"message": "SBE API: Job already completed!"}'
                    )
            except KeyError:
                api_error(
                    "JOB",
                    'Job submitted by Monitor "%s" is not in a correct JSON format!'
                    % monitor.name,
                    request,
                )
                return HttpResponseBadRequest(
                    '{"message": "SBE API: Not in a valid JSON format!"}'
                )
            except ValueError:
                api_error(
                    "JOB",
                    'Monitor "%s" returned a Job with an invalid ID!' % monitor.name,
                    request,
                )
                return HttpResponseBadRequest('{"message": "SBE API: Invalid Job ID!"}')
            except TypeError:
                api_error(
                    "JOB",
                    'Job submitted by Monitor "%s" is not in correct JSON format!'
                    % monitor.name,
                    request,
                )
                return HttpResponseBadRequest(
                    '{"message": "SBE API: Not in valid JSON format!"}'
                )
            except Job.DoesNotExist:
                api_error(
                    "JOB",
                    'Monitor "%s" returned a Job with an non-existent ID "%d" !'
                    % (monitor.name, job_json["id"]),
                    request,
                )
                return HttpResponseBadRequest(
                    '{"message:", "SBE API: Job with ID \'%d\' does not exist!"}'
                    % job_json["id"]
                )
            dump_data("job-%s" % monitor.name, job_json)
            status, message = job.monitor.score_job(monitor, job, job_json)
            del job
            del monitor
            del game_monitors
            if status:
                return HttpResponse(
                    status=202, content='{"message": "SBE API: Job Accepted"}'
                )
            return HttpResponseBadRequest(
                content='{"message": "SBE API: %s"}' % message
            )
        return HttpResponseBadRequest(
            content='{"message": "SBE API: Not a supported method type!"}'
        )

    @staticmethod
    @csrf_exempt
    @authenticate("__SYS_FLAG")
    def api_flag(request):
        if request.method == METHOD_POST:
            team, token, data, exception = game_team_from_token(
                request, "Flag", "token", fields=["flag"]
            )
            del token
            if exception is not None:
                return exception
            try:
                flag = Flag.objects.exclude(team=team).get(
                    host__team__game=team.game, flag__exact=data["flag"], enabled=True
                )
            except Flag.DoesNotExist:
                api_error(
                    "FLAG",
                    'Flag submitted by Team "%s" was not found!'
                    % team.get_canonical_name(),
                    request,
                )
                return HttpResponseNotFound(
                    content='{"message": "SBE API: Flag not valid!"}'
                )
            except Flag.MultipleObjectsReturned:
                api_error(
                    "FLAG",
                    'Flag submitted by Team "%s" returned multiple flags!'
                    % team.get_canonical_name(),
                    request,
                )
                return HttpResponseNotFound(
                    content='{"message": "SBE API: Flag not valid!"}'
                )
            if flag.captured is not None:
                api_error(
                    "FLAG",
                    'Flag "%s" submitted by Team "%s" was already captured!'
                    % (flag.get_canonical_name(), team.get_canonical_name()),
                    request,
                )
                return HttpResponse(
                    status=204, content='{"message": "SBE API: Flag already captured!"}'
                )
            flag.capture(team)
            api_info(
                "FLAG",
                'Flag "%s" was captured by team "%s"!'
                % (flag.get_canonical_name(), team.get_canonical_name()),
                request,
            )
            try:
                api_debug(
                    "FLAG",
                    "Attempting to get another non-captured flag for a hint..",
                    request,
                )
                flag_next = random.choice(
                    Flag.objects.filter(
                        enabled=True, team=flag.team, captured__isnull=True
                    )
                )
                del flag
                if flag_next is not None:
                    api_debug(
                        "FLAG",
                        'Got Flag "%s", sending hint!' % flag_next.get_canonical_name(),
                        request,
                    )
                    return HttpResponse(
                        status=200, content='{"message": "%s"}' % flag_next.description
                    )
            except IndexError:
                return HttpResponse(status=200)
            except Flag.DoesNotExist:
                return HttpResponse(status=200)
        return HttpResponseBadRequest(
            content='{"message": "SBE API: Not a supported method type!"}'
        )

    @staticmethod
    @csrf_exempt
    @authenticate("__SYS_TICKET")
    def api_ticket(request):
        if request.method == METHOD_POST:
            try:
                decoded_data = request.body.decode("UTF-8")
            except UnicodeDecodeError:
                api_error("TICKET", "Data submitted is not encoded properly!", request)
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Incorrect encoding, please use UTF-8!"}'
                )
            try:
                json_data = json.loads(decoded_data)
                del decoded_data
            except json.decoder.JSONDecodeError:
                api_error(
                    "TICKET", "Data submitted is not in correct JSON format!", request
                )
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Not in a valid JSON format!"]'
                )
            if "tickets" not in json_data:
                api_error("TICKET", "Data submitted is missing JSON fields!", request)
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Not in a valid JSON format!"}'
                )
            if not isinstance(json_data["tickets"], list):
                api_error("TICKET", "Data submitted is missing JSON fields!", request)
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Not in a valid JSON format!"}'
                )
            for ticket in json_data["tickets"]:
                ticket, exception = GameTicket.grab_ticket_json(request, ticket)
                if exception:
                    return HttpResponseBadRequest(
                        '{"message": "SBE API: d%s"}' % exception
                    )
                del ticket
            return HttpResponse(status=200, content='{"message": "Accepted"}')
        return HttpResponseBadRequest(
            content='{"message": "SBE API: Not a supported method type!"}'
        )

    @staticmethod
    @csrf_exempt
    @authenticate("__SYS_BEACON")
    def api_beacon(request):
        if request.method == METHOD_POST:
            team, token, data, exception = game_team_from_token(
                request, "CLI", "token", beacon=True, fields=["address"]
            )
            if exception is not None:
                return exception
            address_raw = data["address"]
            try:
                address = IPAddress(address_raw)
            except AddrFormatError:
                api_error(
                    "BEACON",
                    'IP Reported by Team "%s" is invalid!' % team.get_canonical_name(),
                    request,
                )
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Invalid IP Address!"}'
                )
            target_team = None
            for sel_target_team in team.game.teams.all():
                try:
                    target_subnet = IPNetwork(sel_target_team.subnet)
                except AddrFormatError:
                    api_warning(
                        "BEACON",
                        'Team "%s" subnet is invalid, skipping Team!'
                        % team.get_canonical_name(),
                        request,
                    )
                    continue
                if address in target_subnet:
                    api_debug(
                        "BEACON",
                        'Beacon from Team "%s" to Team "%s"\'s subnet!'
                        % (
                            team.get_canonical_name(),
                            sel_target_team.get_canonical_name(),
                        ),
                        request,
                    )
                    target_team = sel_target_team
                    del target_subnet
                    break
                del target_subnet
            del address
            try:
                host = Host.objects.get(
                    ip=address_raw, team__game__status=CONST_GAME_GAME_RUNNING
                )
                if host.team.game.id != team.game.id:
                    api_error(
                        "BEACON",
                        'Host accessed by Team "%s" is not in the same game as "%s"!'
                        % (team.get_canonical_name(), host.team.get_canonical_name()),
                        request,
                    )
                    return HttpResponseForbidden(
                        '{"message": "SBE API: Host is not in the same Game!"}'
                    )
                try:
                    beacon = host.beacons.get(
                        beacon__finish__isnull=True,
                        beacon__attacker=team,
                        beacon__token=token,
                    )
                    beacon.checkin = timezone.now()
                    beacon.save()
                    api_info(
                        "BEACON",
                        'Team "%s" updated the Beacon on Host "%s"!'
                        % (team.get_canonical_name(), host.get_canonical_name()),
                        request,
                    )
                    return HttpResponse()
                except GameCompromiseHost.MultipleObjectsReturned:
                    api_warning(
                        "BEACON",
                        'Team "%s" attempted to create multiple Beacons on a Host "%s"!'
                        % (team.get_canonical_name(), host.get_canonical_name()),
                        request,
                    )
                    del host
                    del address_raw
                    return HttpResponseForbidden(
                        '{"message": "SBE API: Already a Beacon on that Host!"}'
                    )
                except GameCompromiseHost.DoesNotExist:
                    if host.beacons.filter(beacon__finish__isnull=True).count() > 1:
                        api_warning(
                            "BEACON",
                            'Team "%s" attempted to create multiple Beacons on a Host "%s"!'
                            % (team.get_canonical_name(), host.get_canonical_name()),
                            request,
                        )
                        del host
                        del address_raw
                        return HttpResponseForbidden(
                            '{"message": "SBE API: Already a Beacon on that Host!"}'
                        )
                    with atomic():
                        beacon = GameCompromise()
                        beacon_host = GameCompromiseHost()
                        beacon_host.ip = address_raw
                        beacon_host.team = host.team
                        beacon_host.host = host
                        beacon.token = token
                        beacon.attacker = team
                        beacon.save()
                        beacon_host.beacon = beacon
                        beacon_host.save()
                        api_event(
                            team.game,
                            "A Host on %s's network was compromised by %s!"
                            % (host.team.name, team.name),
                        )
                        beacon_value = int(team.game.get_option("beacon_value"))
                        team.set_beacons(beacon_value)
                        api_info(
                            "SCORING-ASYNC",
                            'Beacon score was applied to Team "%s"!'
                            % team.get_canonical_name(),
                            request,
                        )
                        api_score(
                            beacon.id,
                            "BEACON-ATTACKER",
                            team.get_canonical_name(),
                            beacon_value,
                            beacon_host.get_fqdn(),
                        )
                        del beacon_value
                        del beacon
                        del beacon_host
                        del address_raw
                        api_info(
                            "BEACON",
                            'Team "%s" added a Beacon to Host "%s"!'
                            % (team.get_canonical_name(), host.get_canonical_name()),
                            request,
                        )
                    return HttpResponse(status=201)
            except Host.DoesNotExist:
                if target_team is not None:
                    api_info(
                        "BEACON",
                        'Host accessed by Team "%s" does not exist! Attempting to create a faux Host!'
                        % team.get_canonical_name(),
                        request,
                    )
                    if (
                        GameCompromiseHost.objects.filter(
                            ip=address_raw, beacon__finish__isnull=True
                        ).count()
                        > 0
                    ):
                        api_warning(
                            "BEACON",
                            'Team "%s" attempted to create multiple Beacons on a Host "%s"!'
                            % (team.get_canonical_name(), address_raw),
                            request,
                        )
                        del address_raw
                        return HttpResponseForbidden(
                            '{"message": "SBE API: Already a Beacon on that Host!"}'
                        )
                    with atomic():
                        beacon_host = GameCompromiseHost()
                        beacon_host.ip = address_raw
                        beacon_host.team = target_team
                        beacon = GameCompromise()
                        beacon.token = token
                        beacon.attacker = team
                        beacon.save()
                        beacon_host.beacon = beacon
                        beacon_host.save()
                        api_event(
                            team.game,
                            "A Host on %s's network was compromised by %s!"
                            % (target_team.name, team.name),
                        )
                        beacon_value = int(team.game.get_option("beacon_value"))
                        team.set_beacons(beacon_value)
                        api_info(
                            "SCORING-ASYNC",
                            'Beacon score was applied to Team "%s"!'
                            % team.get_canonical_name(),
                            request,
                        )
                        api_score(
                            beacon.id,
                            "BEACON-ATTACKER",
                            team.get_canonical_name(),
                            beacon_value,
                            beacon_host.get_fqdn(),
                        )
                        del beacon_value
                        del beacon
                        del beacon_host
                        api_info(
                            "BEACON",
                            'Team "%s" added a Beacon to Host "%s"!'
                            % (team.get_canonical_name(), address_raw),
                            request,
                        )
                        del address_raw
                    return HttpResponse(status=201)
                del address_raw
                api_error(
                    "BEACON",
                    'Host accessed by Team "%s" does not exist and a hosting team cannot be found!'
                    % team.get_canonical_name(),
                    request,
                )
                return HttpResponseNotFound(
                    '{"message": "SBE API: Host does not exist!"}'
                )
            except Host.MultipleObjectsReturned:
                api_error(
                    "BEACON",
                    'Host accessed by Team "%s" returned multiple Hosts, invalid!'
                    % team.get_canonical_name(),
                    request,
                )
                return HttpResponseNotFound(
                    '{"message": "SBE API: Host does not exist!"}'
                )
        return HttpResponseBadRequest(
            content='{"message": "SBE API: Not a supported method type!"}'
        )

    @staticmethod
    @staff_member_required
    def api_import(request):
        if request.method == "GET":
            import_form = Scorebot2ImportForm()
            return render(
                request,
                "scorebot2_import.html",
                {"import_form": import_form.as_table()},
            )
        elif request.method == "POST":
            import_form = Scorebot2ImportForm(request.POST)
            if import_form.is_valid():
                if import_form:
                    import_game = import_form.save()
                    if import_game is None:
                        return HttpResponseServerError(
                            "Error importing Game! Game is None!"
                        )
                    return HttpResponseRedirect(
                        reverse("scorebot3:scoreboard", args=(import_game.id,))
                    )
                # except Exception as importError:
                #    return HttpResponseServerError(str(importError))
            return render(
                request,
                "scorebot2_import.html",
                {"import_form": import_form.as_table()},
            )
        return HttpResponseBadRequest(content="SBE API: Not a supported method type!")

    @staticmethod
    @csrf_exempt
    @authenticate("__SYS_STORE")
    def api_transfer(request):
        if request.method == METHOD_POST:
            try:
                decoded_data = request.body.decode("UTF-8")
            except UnicodeDecodeError:
                api_error(
                    "TRANSFER", "Data submitted is not encoded properly!", request
                )
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Incorrect encoding, please use UTF-8!"}'
                )
            try:
                json_data = json.loads(decoded_data)
                del decoded_data
            except json.decoder.JSONDecodeError:
                api_error(
                    "TRANSFER", "Data submitted is not in correct JSON format!", request
                )
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Not in a valid JSON format!"]'
                )
            if (
                "target" not in json_data
                or "dest" not in json_data
                or "amount" not in json_data
            ):
                api_error("TRANSFER", "Data submitted is missing JSON fields!", request)
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Not in a valid JSON format!"}'
                )
            if json_data["target"] is None and json_data["dest"] is None:
                api_error("TRANSFER", "Cannot transfer from Gold to Gold!", request)
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Cannot transfer from Gold to Gold!"}'
                )
            team_to = None
            team_from = None
            try:
                amount = int(json_data["amount"])
            except ValueError:
                api_error("TRANSFER", "Amount submitted is is invalid!", request)
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Invalid amount!"}'
                )
            if amount <= 0:
                api_error("TRANSFER", "Amount submitted is is invalid!", request)
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Invalid amount!"}'
                )
            if json_data["dest"] is not None:
                try:
                    team_token = Token.objects.get(uuid=uuid.UUID(json_data["dest"]))
                    team_to = GameTeam.objects.get(token=team_token)
                    del team_token
                except ValueError:
                    api_error(
                        "TRANSFER", "Token given for Destination is invalid!", request
                    )
                    return HttpResponseBadRequest(
                        content='{"message": "SBE API: Invalid Destination Token!"}'
                    )
                except Token.DoesNotExist:
                    api_error(
                        "TRANSFER", "Token given for Destination is invalid!", request
                    )
                    return HttpResponseBadRequest(
                        content='{"message": "SBE API: Invalid Destination Token!"}'
                    )
                except GameTeam.DoesNotExist:
                    api_error(
                        "TRANSFER",
                        "Team given for Destination does not exist!",
                        request,
                    )
                    return HttpResponseBadRequest(
                        content='{"message": "SBE API: Destination Team does not exist!"}'
                    )
            if json_data["target"] is not None:
                try:
                    team_token = Token.objects.get(uuid=uuid.UUID(json_data["target"]))
                    team_from = GameTeam.objects.get(token=team_token)
                    del team_token
                except ValueError:
                    api_error("TRANSFER", "Token given for Source is invalid!", request)
                    return HttpResponseBadRequest(
                        content='{"message": "SBE API: Invalid Source Token!"}'
                    )
                except Token.DoesNotExist:
                    api_error("TRANSFER", "Token given for Source is invalid!", request)
                    return HttpResponseBadRequest(
                        content='{"message": "SBE API: Invalid Source Token!"}'
                    )
                except GameTeam.DoesNotExist:
                    api_error(
                        "TRANSFER", "Team given for Source does not exist!", request
                    )
                    return HttpResponseBadRequest(
                        content='{"message": "SBE API: Source Team does not exist!"}'
                    )
            if team_to is not None and team_to.game.status != CONST_GAME_GAME_RUNNING:
                api_error(
                    "TRANSFER",
                    'Game "%s" submitted is not Running!' % team_to.gane.name,
                    request,
                )
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Team Game ius not running!"}'
                )
            if (
                team_from is not None
                and team_from.game.status != CONST_GAME_GAME_RUNNING
            ):
                api_error(
                    "TRANSFER",
                    'Game "%s" submitted is not Running!' % team_from.gane.name,
                    request,
                )
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Team Game ius not running!"}'
                )
            if (
                team_to is not None
                and team_from is not None
                and team_to.game.id != team_from.game.id
            ):
                api_error(
                    "TRANSFER", "Transfer teams are not in the same Game!", request
                )
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Teams are not in the same Game!"}'
                )
            with atomic():
                if team_from is not None:
                    team_from.set_uptime(-1 * amount)
                    api_score(
                        team_from.id,
                        "TRANSFER",
                        team_from.get_canonical_name(),
                        -1 * amount,
                        (
                            "GoldTeam"
                            if team_to is None
                            else team_to.get_canonical_name(),
                        ),
                    )
                if team_to is not None:
                    team_to.set_uptime(amount)
                    api_score(
                        team_to.id,
                        "TRANSFER",
                        team_to.get_canonical_name(),
                        amount,
                        (
                            "GoldTeam"
                            if team_from is None
                            else team_from.get_canonical_name(),
                        ),
                    )
            return HttpResponse(status=200, content='{"message": "transferred"}')
        return HttpResponseBadRequest(
            content='{"message": "SBE API: Not a supported method type!"}'
        )

    @staticmethod
    @csrf_exempt
    @authenticate("__SYS_CLI")
    def api_register(request):
        if request.method == METHOD_POST:
            team, token, data, exception = game_team_from_token(request, "CLI", "token")
            del token
            if exception is not None:
                return exception
            beacon = token_create_new(30)
            team.beacons.add(beacon)
            team.save()
            api_info(
                "CLI",
                'Team "%s" requested a new Beacon token!' % team.get_canonical_name(),
                request,
            )
            del team
            return HttpResponse(
                status=201, content='{"token": "%s"}' % str(beacon.uuid)
            )
        return HttpResponseBadRequest(
            content='{"message": "SBE API: Not a supported method type!"}'
        )

    @staticmethod
    @csrf_exempt
    @authenticate("__SYS_CLI")
    def api_register_port(request):
        if request.method == METHOD_GET:
            port_list = []
            for game in Game.objects.filter(status=CONST_GAME_GAME_RUNNING):
                for port in game.ports.all():
                    if port not in port_list:
                        port_list.append(port.port)
            return HttpResponse(
                content='{"ports": [%s]}' % ",".join([str(i) for i in port_list])
            )
        if request.method == METHOD_POST:
            team, token, data, exception = game_team_from_token(
                request, "CLI", "token", fields=["port"]
            )
            del token
            if exception is not None:
                return exception
            try:
                port = int(data["port"])
            except ValueError:
                api_error(
                    "CLI",
                    'Port submitted by Team "%s" is not an Integer!'
                    % team.get_canonical_name(),
                    request,
                )
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Port is not an Integer!"}'
                )
            del data
            api_info(
                "CLI",
                'Team "%s" requested a new Beacon port "%d/tcp"!'
                % (team.get_canonical_name(), port),
                request,
            )
            try:
                team.game.ports.all().get(port=port)
                api_debug(
                    "CLI",
                    'Port requested by Team "%s" is already open!'
                    % team.get_canonical_name(),
                    request,
                )
                del team
                return HttpResponse(status=418)
            except GamePort.DoesNotExist:
                game_port = GamePort()
                game_port.port = port
                game_port.save()
                team.game.ports.add(game_port)
                team.game.save()
                api_debug(
                    "CLI",
                    'Port "%d" requested by Team "%s" was opened!'
                    % (port, team.get_canonical_name()),
                    request,
                )
                del team
                del game_port
                return HttpResponse(status=201)
        return HttpResponseBadRequest(
            content='{"message": "SBE API: Not a supported method type!"}'
        )

    @staticmethod
    @authenticate()
    def api_uuid(request, game_id):
        if request.method == METHOD_GET:
            try:
                game = Game.objects.get(id=int(game_id))
            except ValueError:
                api_error(
                    "MAPPER",
                    'Attempted to get non-existent Game "%d"!' % game_id,
                    request,
                )
                return HttpResponseNotFound()
            except Game.DoesNotExist:
                api_error(
                    "MAPPER",
                    'Attempted to get non-existent Game "%d"!' % game_id,
                    request,
                )
                return HttpResponseNotFound()
            except Game.MultipleObjectsReturned:
                api_error(
                    "MAPPER",
                    'Attempted to get non-existent Game "%d"!' % game_id,
                    request,
                )
                return HttpResponseNotFound()
            if game.status != CONST_GAME_GAME_RUNNING:
                api_error(
                    "MAPPER",
                    'Attempted to get a non-running Game "%s"!' % game.name,
                    request,
                )
                return HttpResponseForbidden(
                    content='{"message": "SBE API: Game "%s" is not Running!"}'
                    % game.name
                )
            api_info(
                "MAPPER", 'Returned UUID mappings for Game "%s"!' % game.name, request
            )
            json_data = {"teams": [t.get_json_mapper() for t in game.teams.all()]}
            return HttpResponse(status=200, content=json.dumps(json_data))
        return HttpResponseBadRequest(
            content='{"message": "SBE API: Not a supported method type!"}'
        )

    @staticmethod
    @csrf_exempt
    @authenticate("__SYS_STORE")
    def api_purchase(request, team_id=None):
        if request.method == METHOD_GET:
            api_debug(
                "STORE", 'Requesting the exchange rate for Team "%s"' % team_id, request
            )
            if team_id is None:
                api_error("STORE", "Attempted to use Null Team ID!", request)
                return HttpResponseNotFound(
                    '{"message": "SBE API: Team could not be found!"}'
                )
            try:
                team = GameTeam.objects.get(
                    store=int(team_id), game__status=CONST_GAME_GAME_RUNNING
                )
            except ValueError:
                api_error(
                    "STORE",
                    'Attempted to use an invalid Team ID "%s"!' % str(team_id),
                    request,
                )
                return HttpResponseNotFound('{"message": "SBE API: Invalid Team ID!"}')
            except GameTeam.DoesNotExist:
                api_error(
                    "STORE",
                    'Attempted to use an non-existent Team ID "%s"!' % str(team_id),
                    request,
                )
                return HttpResponseNotFound(
                    '{"message": "SBE API: Team could not be found!"}'
                )
            except GameTeam.MultipleObjectsReturned:
                api_error(
                    "STORE",
                    "Attempted to use a Team ID which returned multiple Teams!",
                    request,
                )
                return HttpResponseNotFound(
                    '{"message": "SBE API: Team could not be found!"}'
                )
            rate = float(team.game.get_option("score_exchange_rate")) / 100.0
            api_debug(
                "STORE",
                'The exchange rate for Team "%s" is "%.2f"!'
                % (team.get_canonical_name(), rate),
                request,
            )
            return HttpResponse(status=200, content='{"rate": %.2f}' % rate)
        if request.method == METHOD_POST:
            try:
                decoded_data = request.body.decode("UTF-8")
            except UnicodeDecodeError:
                api_error("STORE", "Data submitted is not encoded properly!", request)
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Incorrect encoding, please use UTF-8!"}'
                )
            try:
                json_data = json.loads(decoded_data)
                del decoded_data
            except json.decoder.JSONDecodeError:
                api_error(
                    "STORE", "Data submitted is not in correct JSON format!", request
                )
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Not in a valid JSON format!"]'
                )
            if "team" not in json_data or "order" not in json_data:
                api_error("STORE", "Data submitted is missing JSON fields!", request)
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Not in a valid JSON format!"}'
                )
            try:
                team = GameTeam.objects.get(
                    store=int(json_data["team"]), game__status=CONST_GAME_GAME_RUNNING
                )
            except ValueError:
                api_error(
                    "STORE",
                    'Attempted to use an invalid Team ID "%s"!' % str(team_id),
                    request,
                )
                return HttpResponseNotFound('{"message": "SBE API: Invalid Team ID!"}')
            except GameTeam.DoesNotExist:
                api_error(
                    "STORE",
                    'Attempted to use an non-existent Team ID "%s"!' % str(team_id),
                    request,
                )
                return HttpResponseNotFound(
                    '{"message": "SBE API: Team could not be found!"}'
                )
            except GameTeam.MultipleObjectsReturned:
                api_error(
                    "STORE",
                    "Attempted to use a Team ID which returned multiple Teams!",
                    request,
                )
                return HttpResponseNotFound(
                    '{"message": "SBE API: Team could not be found!"}'
                )
            api_info(
                "STORE",
                'Attempting to add Purchase records for Team "%s".'
                % team.get_canonical_name(),
                request,
            )
            if not isinstance(json_data["order"], list):
                api_error(
                    "STORE", 'Data submitted is missing the "oreer" array!', request
                )
                return HttpResponseBadRequest(
                    content='{"message": "SBE API: Not in valid JSON format!"}'
                )
            for order in json_data["order"]:
                if "item" in order and "price" in order:
                    try:
                        with atomic():
                            purchase = Purchase()
                            purchase.team = team
                            purchase.amount = int(
                                float(order["price"])
                                * (
                                    float(team.game.get_option("score_exchange_rate"))
                                    / 100.0
                                )
                            )
                            purchase.item = (
                                order["item"]
                                if len(order["item"]) < 150
                                else order["item"][:150]
                            )
                            team.set_uptime(-1 * purchase.amount)
                            purchase.save()
                            api_score(
                                team.id,
                                "PURCHASE",
                                team.get_canonical_name(),
                                purchase.amount,
                                purchase.item,
                            )
                            api_debug(
                                "STORE",
                                'Processed order of "%s" "%d" for team "%s"!'
                                % (
                                    purchase.item,
                                    purchase.amount,
                                    team.get_canonical_name(),
                                ),
                                request,
                            )
                            del purchase
                    except ValueError:
                        api_warning(
                            "STORE",
                            'Order "%s" has invalid integers for amount!!' % str(order),
                            request,
                        )
                else:
                    api_warning(
                        "STORE",
                        'Order "%s" does not have the correct format!' % str(order),
                        request,
                    )
            return HttpResponse(status=200, content='{"message": "processed"}')
        return HttpResponseBadRequest(
            content='{"message": "SBE API: Not a supported method type!"}'
        )

    @staticmethod
    def api_scoreboard(request, game_id):
        return HttpResponseBadRequest(
            "The old Scoreboard is deprecated. Please use the new Scoreboard"
        )

    @staticmethod
    def api_scoreboard_json(request, game_id):
        if request.method == METHOD_GET:
            try:
                return HttpResponse(
                    content=Game.objects.get(id=int(game_id)).get_json_scoreboard()
                )
            except Game.DoesNotExist:
                return HttpResponseNotFound()
        return HttpResponseBadRequest()

    @staticmethod
    @staff_member_required
    def api_event_create(request):
        if request.method == "GET":
            event_form = CreateEventForm()
            return render(
                request, "event_form.html", {"eventcreate": event_form.as_table()}
            )
        elif request.method == "POST":
            event_form = CreateEventForm(request.POST)
            if event_form.is_valid():
                if event_form:
                    # try:
                    event = event_form.save()
                    # if import_game is None:
                    #    return HttpResponseServerError('Error importing Game! Game is None!')
                    return HttpResponseRedirect(
                        reverse("scorebot3:scoreboard", args=(event,))
                    )
                # except Exception as importError:
                #    return HttpResponseServerError(str(importError))
        return HttpResponseBadRequest(content="SBE API: Not a supported method type!")

    @staticmethod
    @staff_member_required
    def api_event_message(request):
        if request.method == "GET":
            event_message_form = EventMessageForm()
            return render(
                request,
                "sbe_event_message.html",
                {"form_event_message": event_message_form.as_p()},
            )
        elif request.method == "POST":
            event_message_form = EventMessageForm(request.POST)
            if event_message_form.is_valid():
                if event_message_form:
                    event_message_form.save()
                    return HttpResponseRedirect(reverse("scorebot3:form_event_message"))
        return HttpResponseBadRequest(content="SBE API: Not a supported method type!")

    @staticmethod
    def api_default_page(request):
        g = Game.objects.filter(
            status=1, start__isnull=False, finish__isnull=True
        ).first()
        if g is not None:
            return HttpResponseRedirect("/scoreboard/%d/" % g.pk)
        return HttpResponseRedirect("/scoreboard/1/")

    @staticmethod
    @csrf_exempt
    @authenticate("__SYS_CLI")
    def api_change_host(request, host_id=None):
        if (
            request.method != "DELETE" or request.method != "POST"
        ) and host_id is not None:
            return HttpResponseBadRequest(
                "Cannot specify a host ID with a non POST/DELETE request!"
            )
        try:
            json_text = request.body.decode("UTF-8")
        except UnicodeTranslateError:
            return HttpResponseBadRequest("Invalid Unicode!")
        try:
            data = json.loads(json_text)
        except json.decoder.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON!")
        if host_id is not None and request.method != "GET":
            try:
                host = Host.objects.get(id=host_id)
            except Exception:
                return HttpResponseNotFound("No host %s found!" % host_id)
            if request.method == "DELETE":
                host.team = None
                host.save()
                return HttpResponse()
        else:
            host = Host()
        if "team" not in data:
            return HttpResponseBadRequest("Missing 'team' item!")
        if "ip" not in data:
            return HttpResponseBadRequest("Missing 'ip' item!")
        if "dns" not in data:
            return HttpResponseBadRequest("Missing 'dns' item!")
        try:
            token = Token.objects.get(uuid=uuid.UUID(data["team"]))
            team = GameTeam.objects.get(token=token)
        except Exception:
            return HttpResponseNotFound("team with uuid %s not found" % data["team"])
        host.team = team
        try:
            result = host.update_from_json(data)
            if result is not None:
                return HttpResponseServerError("AN error occured %s!" % str(result))
            host.save()
        except Exception as err:
            return HttpResponseServerError("An error occured %s!" % str(err))
        return HttpResponse(json.dumps({"id": host.pk}))

    @staticmethod
    def api_get_games(request):
        return HttpResponse(
            content=json.dumps(
                [g.get_list_json() for g in Game.objects.all().order_by("start")]
            ),
            content_type="application/json",
        )

    @staticmethod
    @csrf_exempt
    @authenticate()
    def api_beacon_active(request):
        if request.method == METHOD_GET:
            try:
                t = GameTeam.objects.get(token=request.authentication.token)
            except GameTeam.DoesNotExist:
                return HttpResponseBadRequest(content='{"message": "Invalid Token"}')
            all_beacons = GameCompromise.objects.filter(finish__isnull=True, attacker=t)
            beacon_list = list()
            for beacon in all_beacons:
                beacon_info = dict()
                beacon_info["host"] = str(beacon.host)
                beacon_info["token"] = str(beacon.token)
                beacon_info["attacker"] = str(beacon.attacker)
                beacon_info["start"] = str(beacon.start)
                beacon_info["finish"] = str(beacon.finish)
                beacon_list.append(beacon_info)
            return HttpResponse(content=json.dumps(beacon_list))
        else:
            return HttpResponseBadRequest(
                content='{"message": "SBE API: Not a supported method type!"}'
            )

    @staticmethod
    @csrf_exempt
    @authenticate("__SYS_CLI")
    def api_event_create_cli(request, game_id):
        if request.method != "POST":
            return HttpResponseForbidden()
        try:
            json_text = request.body.decode("UTF-8")
        except UnicodeTranslateError:
            return HttpResponseBadRequest("Invalid Unicode!")
        try:
            data = json.loads(json_text)
        except json.decoder.JSONDecodeError:
            return HttpResponseBadRequest("Invalid JSON!")
        if "data" not in data or not isinstance(data["data"], dict):
            return HttpResponseBadRequest("Bad JSON!")
        e = GameEvent()
        try:
            e.game = Game.objects.get(pk=game_id)
        except Game.DoesNotExist:
            return HttpResponseNotFound()
        e.data = json.dumps(data["data"])
        try:
            e.type = data.get("type", 0)
            if e.type < 0 or e.type > 4:
                return HttpResponseBadRequest("Bad Type Value!")
        except ValueError:
            return HttpResponseBadRequest("Bad Type Value!")
        try:
            t = data.get("timeout", 30)
            if t <= 0:
                return HttpResponseBadRequest("Bad Timeout Value!")
            e.timeout = timezone.now() + timedelta(seconds=t)
        except ValueError:
            return HttpResponseBadRequest("Bad Timeout Value!")
        try:
            e.save()
        except Exception as err:
            return HttpResponseServerError(str(err))
        return HttpResponse(status=201)
