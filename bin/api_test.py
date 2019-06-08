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


i = p(put, url, "game/", {"name": "Testing Game", "start": "now"})
assert i is not None and "id" in i

t = [
    p(put, url, "game/%s/team/" % i["id"], {"name": "Alpha", "color": "0xA1"}),
    p(put, url, "game/%s/team/" % i["id"], {"name": "Beta", "color": "0xA2"}),
    p(put, url, "game/%s/team/" % i["id"], {"name": "Delta", "color": "0xA3"}),
    p(put, url, "game/%s/team/" % i["id"], {"name": "Gamma", "color": "0xA4"}),
]
