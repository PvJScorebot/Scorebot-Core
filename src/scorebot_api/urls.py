#!/usr/bin/false
# Django URLS File
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

from django.urls import path
from django.conf.urls import url
from django.contrib.admin import site
from scorebot import unrest, Models
#from scorebot_api.views import job, flag, beacon, ports, register, mapper, scoreboard

urlpatterns = [
    path('admin/', site.urls),
#    url(r'^api/job$', job, name='job'),
#    url(r'^api/job/$', job, name='job'),
#    url(r'^api/flag/$', flag, name='flag'),
#    url(r'^api/beacon/$', beacon, name='beacon'),
#    url(r'^api/beacon/port/$', ports, name='ports'),
#    url(r'^api/register/$', register, name='register'),
#    url(r'^api/mapper/(?P<gid>[0-9]+)$', mapper, name='mapper'),
#    url(r'^api/mapper/(?P<gid>[0-9]+)/$', mapper, name='mapper'),
#    url(r'^api/scoreboard/(?P<gid>[0-9]+)/$', scoreboard, name='scoreboard'),
]

unrest.init(Models.values(), urlpatterns, '/models/', debug=True)
