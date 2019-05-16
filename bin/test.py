#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

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
