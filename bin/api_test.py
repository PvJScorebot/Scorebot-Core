#!/usr/bin/python3

from random import randint
from requests import get, post, put, delete
from json import dumps, loads, JSONDecodeError


def p(m, url, a=None, da=None):
    u = url
    if a is not None:
        u = "%s%s" % (url, a)
    print("URL: %s" % u)
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

p(get, url, "team/1/token/")

i = p(put, url, "token/", da={"name": "new-whatever-%d" % randint(0, 5000)})
if "uuid" in i:
    print("New UUID is '%s'" % i["uuid"])

    p(get, url, "token/%s" % i["uuid"])

    p(put, url, "team/1/token/", da={"uuid": i["uuid"]})

p(get, url, "team/1/token/")
