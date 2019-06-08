#!/usr/bin/python3

from random import randint
from requests import get, post, put, delete
from json import dumps, loads, JSONDecodeError


def p(m, url, a=None, da=None):
    u = url
    if a is not None:
        u = "%s%s" % (url, a)
    print("%s: %s" % (m.__name__.upper(), u))
    if da is not None:
        print(">>\n%s" % dumps(da, indent=4, sort_keys=True))
        c = m(u, data=dumps(da))
    else:
        c = m(u)
    print("RESP: %d" % c.status_code)
    b = c.content.decode("UTF-8")
    if len(b) > 0:
        try:
            d = loads(b)
            if "stack" in d:
                print("EXCEPTION")
                for l in d["stack"]:
                    print(l)
            else:
                print(dumps(d, indent=4, sort_keys=True))
            return d
        except JSONDecodeError as err:
            print("JSON ERROR (%s)" % err)
            print(b)
    return None


url = "http://localhost:8000/api/"

p(put, url, "game/1/teams/", {"name": "Delta Boss", "color": "0xAF"})

"""
i = p(put, url, "game/", {"name": "New Game (%d)" % randint(0, 500), "start": "now"})
print("Game ID: %s" % i["id"])

p(get, url, "game/%s/" % i["id"])
p(get, url, "game/%s/teams/" % i["id"])

p(delete, url, "game/%s/" % i["id"])
"""
"""
p(
    put,
    url,
    "team/5/score/stack/",
    {"sender": 6, "value": 100, "transaction": {"type": "correction"}},
)

p(
    put,
    url,
    "credit/",
    {"sender": 5, "receiver": 6, "value": 100, "transaction": {"type": "correction"}},
)"""

"""
p(get, url, "ports/")
p(get, url, "game/1/ports/")

p(delete, url, "game/1/ports/4")
p(delete, url, "game/1/ports/3")

p(put, url, "game/1/ports/", {"number": 8080})
p(put, url, "game/1/ports/", {"number": 999, "type": 1})
p(get, url, "game/1/ports/")
"""
