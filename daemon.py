#!/usr/bin/python3
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

import os
import sys
import django

os.environ["DJANGO_SETTINGS_MODULE"] = "scorebot.settings"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "scorebot.settings")

from scorebot.utils.daemons import DaemonEntry, start_daemon


if __name__ == "__main__":
    django.setup()
    start_daemon()
    sys.exit(0)
