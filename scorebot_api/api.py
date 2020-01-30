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

from django.conf.urls import url
from scorebot_api.views import ScorebotAPI

urlpatterns = [
    url(r"^job$", ScorebotAPI.api_job),
    url(r"^job/$", ScorebotAPI.api_job),
    url(r"^flag$", ScorebotAPI.api_flag),
    url(r"^flag/$", ScorebotAPI.api_flag),
    url(r"^beacon$", ScorebotAPI.api_beacon),
    url(r"^ticket$", ScorebotAPI.api_ticket),
    url(r"^beacon/$", ScorebotAPI.api_beacon),
    url(r"^ticket/$", ScorebotAPI.api_ticket),
    url(r"^games/$", ScorebotAPI.api_get_games),
    url(r"^host/$", ScorebotAPI.api_change_host),
    url(r"^register$", ScorebotAPI.api_register),
    url(r"^purchase$", ScorebotAPI.api_purchase),
    url(r"^transfer$", ScorebotAPI.api_transfer),
    url(r"^register/$", ScorebotAPI.api_register),
    url(r"^purchase/$", ScorebotAPI.api_purchase),
    url(r"^transfer/$", ScorebotAPI.api_transfer),
    url(r"^beacon/port$", ScorebotAPI.api_register_port),
    url(r"^beacon/port/$", ScorebotAPI.api_register_port),
    url(r"^beacon/active$", ScorebotAPI.api_beacon_active),
    url(r"^beacon/active/$", ScorebotAPI.api_beacon_active),
    url(r"^mapper/(?P<game_id>[0-9]+)$", ScorebotAPI.api_uuid),
    url(r"^mapper/(?P<game_id>[0-9]+)/$", ScorebotAPI.api_uuid),
    url(r"^host/(?P<host_id>[0-9]+)$", ScorebotAPI.api_change_host),
    url(r"^purchase/(?P<team_id>[0-9]+)$", ScorebotAPI.api_purchase),
    url(r"^purchase/(?P<team_id>[0-9]+)/$", ScorebotAPI.api_purchase),
    url(r"^event/(?P<game_id>[0-9]+)$", ScorebotAPI.api_event_create_cli),
    url(r"^event/(?P<game_id>[0-9]+)/$", ScorebotAPI.api_event_create_cli),
    url(r"^scoreboard/(?P<game_id>[0-9]+)$", ScorebotAPI.api_scoreboard_json),
    url(r"^scoreboard/(?P<game_id>[0-9]+)/$", ScorebotAPI.api_scoreboard_json),
]
