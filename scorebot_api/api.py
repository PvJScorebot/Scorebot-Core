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

from django.urls import re_path
from scorebot_api.views import ScorebotAPI

urlpatterns = [
    re_path(r"^job$", ScorebotAPI.api_job),
    re_path(r"^job/$", ScorebotAPI.api_job),
    re_path(r"^flag$", ScorebotAPI.api_flag),
    re_path(r"^flag/$", ScorebotAPI.api_flag),
    re_path(r"^beacon$", ScorebotAPI.api_beacon),
    re_path(r"^ticket$", ScorebotAPI.api_ticket),
    re_path(r"^beacon/$", ScorebotAPI.api_beacon),
    re_path(r"^ticket/$", ScorebotAPI.api_ticket),
    re_path(r"^games/$", ScorebotAPI.api_get_games),
    re_path(r"^host/$", ScorebotAPI.api_change_host),
    re_path(r"^register$", ScorebotAPI.api_register),
    re_path(r"^purchase$", ScorebotAPI.api_purchase),
    re_path(r"^transfer$", ScorebotAPI.api_transfer),
    re_path(r"^register/$", ScorebotAPI.api_register),
    re_path(r"^purchase/$", ScorebotAPI.api_purchase),
    re_path(r"^transfer/$", ScorebotAPI.api_transfer),
    re_path(r"^beacon/port$", ScorebotAPI.api_register_port),
    re_path(r"^beacon/port/$", ScorebotAPI.api_register_port),
    re_path(r"^beacon/active$", ScorebotAPI.api_beacon_active),
    re_path(r"^beacon/active/$", ScorebotAPI.api_beacon_active),
    re_path(r"^mapper/(?P<game_id>[0-9]+)$", ScorebotAPI.api_uuid),
    re_path(r"^mapper/(?P<game_id>[0-9]+)/$", ScorebotAPI.api_uuid),
    re_path(r"^host/(?P<host_id>[0-9]+)$", ScorebotAPI.api_change_host),
    re_path(r"^purchase/(?P<team_id>[0-9]+)$", ScorebotAPI.api_purchase),
    re_path(r"^purchase/(?P<team_id>[0-9]+)/$", ScorebotAPI.api_purchase),
    re_path(r"^event/(?P<game_id>[0-9]+)$", ScorebotAPI.api_event_create_cli),
    re_path(r"^event/(?P<game_id>[0-9]+)/$", ScorebotAPI.api_event_create_cli),
    re_path(r"^scoreboard/(?P<game_id>[0-9]+)$", ScorebotAPI.api_scoreboard_json),
    re_path(r"^scoreboard/(?P<game_id>[0-9]+)/$", ScorebotAPI.api_scoreboard_json),
]
