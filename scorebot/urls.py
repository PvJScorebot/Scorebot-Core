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

from django.contrib import admin
from django.urls import re_path, include

urlpatterns = [
    re_path(r"^admin/", admin.site.urls),
    re_path(
        r"^api/",
        include(("scorebot_api.api", "scorebot3_api"), namespace="scorebot3_api"),
    ),
    re_path(r"^", include(("scorebot_api.urls", "scorebot3"), namespace="scorebot3")),
]
