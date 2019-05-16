#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from scorebot_db.models import Models


def PrintDelta(seconds):
    b = "-" if seconds < 0 else ""
    seconds = abs(int(seconds))
    d, seconds = divmod(seconds, 86400)
    h, seconds = divmod(seconds, 3600)
    m, seconds = divmod(seconds, 60)
    if d > 0:
        return "%s%dd%dh%dm%ds" % (b, d, h, m, seconds)
    elif h > 0:
        return "%s%dh%dm%ds" % (b, h, m, seconds)
    elif m > 0:
        return "%s%dm%ds" % (b, m, seconds)
    return "%s%ds" % (b, seconds)


def GetModel(model_name):
    if model_name is None or len(model_name) == 0:
        return None
    if model_name.lower() in Models:
        return Models[model_name.lower()]
    return None


def GetManager(model_name):
    m = GetModel(model_name)
    if m is not None and hasattr(m, "objects"):
        return m.objects
    return None


def CreateModel(model_name, save=False):
    m = GetModel(model_name)
    if m is not None:
        i = m()
        if save:
            i.save()
        return i
    return None
