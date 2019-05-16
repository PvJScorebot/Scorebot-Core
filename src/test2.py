#!/usr/bin/python3

import json
import requests

a = requests.session()
a.headers['SBE-AUTH'] = '0909c234-732e-4d31-af61-6816bf9fb242'
"""

v = {"token": "9d1761be-b8c6-46f8-bbf7-aaf3a689fe79", "port": "4501"}

r = a.post('https://prosvjoes.com/api/beacon/port/', data=json.dumps(v))
print(r, r.status_code, r.content)

r = a.get('https://prosvjoes.com/api/beacon/port/') #, data=json.dumps(v))
print(r, r.status_code, r.content)


r = a.get('https://prosvjoes.com/api/mapper/1') #, data=json.dumps(v))
print(r, r.status_code, r.content)


"""
b = a.get('http://localhost:8000/api/job/')
try:
    c = b.content.decode('UTF-8')
except UnicodeDecodeError:
    c - str(b.content)

print('GOT: %d' % b.status_code)
d = None
try:
    d = json.loads(c)
    print(d)
    e = json.dumps(d, indent=4)
    print(e)
except json.JSONDecodeError:
    print(c)


if b.status_code == 201:
    d['host']['ping_sent'] = 10
    d['host']['ping_respond'] = 10
    e = json.dumps(d, indent=4)
    f = a.post('http://localhost:8000/api/job/',data=e)
    print(f.status_code, f.content)
