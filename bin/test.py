#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
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

from sys import path
from django import setup
from os import environ, chdir

chdir("src/scorebot/")
path.insert(0, ".")
environ["DJANGO_SETTINGS_MODULE"] = "scorebot.settings"
environ.setdefault("DJANGO_SETTINGS_MODULE", "scorebot.settings")
setup()


from scorebot_utils.generic import GetManager
from scorebot_utils.score import Correction, Transfer, Event


if __name__ == "__main__":

    m = GetManager("Game").all()
    print(m)
    c = m[0]
    t = m[0].Teams.all()
    print(t)

    a = t[2]
    b = t[3]

    print(a, b)

    print(a, a.GetScore())
    print(b, b.GetScore())

    print(Correction(100, a))

    print(a, a.GetScore())
    print(b, b.GetScore())

    print(Transfer(50, b, a))

    print("%s Scores" % a.Fullname())
    for v in a.GetScore().Stack.all():
        print(v)

    print("%s Scores" % b.Fullname())
    for v in b.GetScore().Stack.all():
        print(v)
