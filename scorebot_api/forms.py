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
import socket
import random

from django import forms
from django.utils.text import slugify
from scorebot.utils.events import EVENT_HOST
from scorebot.utils import logger, constants
from scorebot_game.models import Game, GameTeam, GameTicket
from scorebot_grid.models import Host, Flag, Service, DNS, Content


class CreateEventForm(forms.Form):
    game = forms.ModelChoiceField(Game.objects.all())
    type = forms.ChoiceField(
        label="Type", choices=constants.CONST_FORM_EVENT_CREATE_CHOICES
    )
    data = forms.CharField(label="Data", widget=forms.Textarea, required=False)

    def save(self):
        import_data = self.clean()
        if import_data:
            event_manager = EVENT_HOST.get_game(import_data.get("game").id)
            data = import_data.get("data")
            try:
                data = json.loads(data)
            except:
                pass
            event_manager.add_event(import_data.get("type"), data)
            return event_manager.game_id


class EventMessageForm(forms.Form):
    game = forms.ModelChoiceField(queryset=Game.objects.all())
    message = forms.CharField(label="Event Game Message", max_length=250)

    def save(self):
        event_data = self.clean()
        if event_data:
            event_manager = EVENT_HOST.get_game(event_data.get("game").id)
            new_message = str(event_data.get("message"))
            if len(new_message) > 0:
                event_manager.message = new_message
            else:
                event_manager.message = constants.CONST_GAME_GAME_MESSAGE
            return event_manager.game_id
        raise Exception("Cannot find Event Manager for Game!")


class Scorebot2ImportForm(forms.Form):
    json_data = forms.CharField(
        label="Game JSON Data", widget=forms.Textarea, required=False
    )

    def save(self, commit=True):
        try:
            import_data = self.clean()
            if import_data.get("json_data") is not None:
                try:
                    game_data = json.loads(import_data.get("json_data"))
                    return Scorebot2ImportForm.convert_game(game_data)
                except json.decoder.JSONDecodeError:
                    raise Exception("Cannot import! Bad JSON format!")
            else:
                raise Exception("Cannot import an empty Game!")
        except Exception as importError:
            logger.error("SBE-CONVERT", "Error importing game! %s" % str(importError))
            raise importError  # Exception('Failure to import Game!')

    @staticmethod
    def convert_game(json_data):
        game = Game()
        game.name = json_data["game_name"]
        game.save()
        red_team = GameTeam()
        red_team.name = "Redcell"
        red_team.offensive = True
        red_team.color = 16711686
        red_team.game = game
        red_team.save()
        for blueteam in json_data["blueteams"]:
            dns = DNS()
            dns.address = blueteam["dns"]
            dns.save()
            blueteam_team = GameTeam()
            blueteam_team.game = game
            blueteam_team.name = blueteam["name"]
            blueteam_team.subnet = blueteam["nets"][0]
            blueteam_team.save()
            blueteam_team.dns.add(dns)
            blueteam_team.save()
            for host in blueteam["hosts"]:
                blue_host = Host()
                blue_host.fqdn = host["hostname"]
                blue_host.team = blueteam_team
                if "ip" in host:
                    blue_host.ip = host["ip"]
                blue_host.save()
                for service in host["services"]:
                    blue_service = Service()
                    try:
                        blue_service.port = int(service["port"])
                    except ValueError:
                        logger.warning(
                            "SBE-CONVERT",
                            'Conversion to port number for port "%s" failed! '
                            "Defaulting to 80." % service["port"],
                        )
                        blue_service.port = 80
                    for (
                        service_protocol
                    ) in constants.CONST_GRID_SERVICE_PROTOCOL_CHOICES:
                        if service_protocol[1].lower() == service["protocol"].lower():
                            blue_service.protocol = service_protocol[0]
                            break
                    try:
                        blue_service.value = int(service["value"])
                    except ValueError:
                        logger.warning(
                            "SBE-CONVERT",
                            'Conversion to value for port "%s" failed! '
                            "Defaulting to 50." % service["port"],
                        )
                    try:
                        blue_service.name = socket.getservbyport(blue_service.port)
                    except OSError:
                        blue_service.name = "http"
                    blue_service.application = blue_service.name
                    blue_service.host = blue_host
                    blue_service.save()
                    if "content" in service:
                        blue_content = Content()
                        blue_content.type = "imported"
                        blue_content.data = json.dumps(service["content"])
                        blue_content.save()
                        blue_service.content = blue_content
                        blue_service.save()
            if "flags" in blueteam:
                for flag_name, flag_data in blueteam["flags"].items():
                    blue_flag = Flag()
                    blue_flag.name = slugify(flag_name)
                    try:
                        blue_flag_check = blueteam_team.flags.all().get(
                            flag=str(flag_data["value"])
                        )
                    except Flag.DoesNotExist:
                        blue_flag_check = None
                    except Flag.MultipleObjectsReturned:
                        blue_flag_check = True
                    if blue_flag_check is not None:
                        blue_flag.flag = "%s-%d" % (
                            flag_data["value"],
                            random.randint(0, 255),
                        )
                    else:
                        blue_flag.flag = flag_data["value"]
                    blue_flag.description = flag_data["answer"]
                    blue_flag.team = blueteam_team
                    blue_flag.host = random.choice(blueteam_team.hosts.all())
                    blue_flag.save()
        if "injects" in json_data:
            for inject in json_data["injects"]:
                for team in game.teams.all():
                    blue_ticket = GameTicket()
                    blue_ticket.ticket_id = random.randint(0, 4096)
                    blue_ticket.name = slugify(inject["inject_name"])
                    if isinstance(inject["inject_body"], list):
                        blue_ticket.description = "\r\n".join(inject["inject_body"])
                    else:
                        blue_ticket.description = str(inject["inject_body"])
                    if inject["category"].lower() != "no category":
                        for category in constants.CONST_GRID_TICKET_CATEGORIES_CHOICES:
                            if category[1].lower() == inject["category"].lower():
                                blue_ticket.type = category[0]
                    blue_ticket.team = team
                    blue_ticket.save()
        return game
