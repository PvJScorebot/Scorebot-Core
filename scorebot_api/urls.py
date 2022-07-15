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
    re_path(r"^sb2import$", ScorebotAPI.api_import),
    re_path(r"^sb2import/$", ScorebotAPI.api_import, name="sb2import"),
    re_path(r"^scoreboard/(?P<game_id>[0-9]+)$", ScorebotAPI.api_scoreboard),
    re_path(
        r"^event_message/$", ScorebotAPI.api_event_message, name="form_event_message"
    ),
    re_path(
        r"^scoreboard/(?P<game_id>[0-9]+)/$",
        ScorebotAPI.api_scoreboard,
        name="scoreboard",
    ),
    re_path(r"", ScorebotAPI.api_default_page),
]
