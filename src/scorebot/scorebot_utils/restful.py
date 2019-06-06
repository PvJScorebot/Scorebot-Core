#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from sys import exc_info
from django.conf import settings
from django.http import HttpResponse
from traceback import format_exception
from scorebot_utils.generic import GetModel
from scorebot_utils import LogAuth, LogHttp
from json import dumps, loads, JSONDecodeError
from django.views.decorators.csrf import csrf_exempt
from django.db.models import ObjectDoesNotExist, Model
from django.core.exceptions import ValidationError, FieldDoesNotExist
from scorebot_utils.constants import (
    ERROR_400,
    ERROR_401,
    ERROR_403,
    ERROR_404,
    ERROR_405,
    ERROR_428,
    ERROR_500,
    MULTI_RESULT_KEY,
    ERROR_401_MESSAGE,
    ERROR_403_MESSAGE,
    ERROR_404_MESSAGE,
    ERROR_405_MESSAGE,
    ERROR_428_MESSAGE,
    ERROR_404_MESSAGE_ALT,
)


class HttpError(HttpResponse, Exception):
    def __init__(self, message, status=500, code=ERROR_500, cause=None):
        HttpResponse.__init__(
            self,
            content="unspecified server error",
            status=status,
            content_type="application/json",
        )
        Exception.__init__(self, cause)
        if message is not None:
            self.SetContent(message, code, cause)

    def SetContent(self, message, code, cause=None):
        LogHttp.error(
            "HTTP Error '%s': code '%d', message '%s'"
            % (self.__class__.__name__, self.status_code, message),
            cause,
        )
        resp = {"error": code, "message": message, "version": settings.VERSION}
        if settings.DEBUG and isinstance(cause, Exception):
            resp["stack"] = format_exception(*exc_info(), limit=3, chain=True)
        self.content = dumps(resp)


class HttpError400(HttpError):
    def __init__(self, message, cause=None):
        super().__init__(message, 400, ERROR_400, cause)


class HttpError401(HttpError):
    def __init__(self):
        super().__init__(ERROR_401_MESSAGE, 401, ERROR_401)


class HttpError403(HttpError):
    def __init__(self, message):
        super().__init__("", 403)
        if isinstance(message, list):
            self.SetContent(
                ERROR_403_MESSAGE.format(permissions=",".join(message)), ERROR_403
            )
        else:
            self.SetContent(message, ERROR_403)


class HttpError404(HttpError):
    def __init__(self, message=None):
        super().__init__("", 404)
        if message is not None:
            self.SetContent(ERROR_404_MESSAGE.format(requested=message), ERROR_404)
        else:
            self.SetContent(ERROR_404_MESSAGE_ALT, ERROR_404)


class HttpError405(HttpError):
    def __init__(self, method):
        super().__init__(ERROR_405_MESSAGE.format(method=method), 405, ERROR_405)


class HttpError428(HttpError):
    def __init__(self, condition):
        super().__init__(ERROR_428_MESSAGE.format(condition=condition), 428, ERROR_428)


class HttpError500(HttpError):
    def __init__(self, message, cause=None):
        super().__init__(message, 500, ERROR_500, cause)


@csrf_exempt
def Api(request, path):
    LogHttp.debug("RestFul request %s for '%s'." % (request.method, path))
    nodes = path.split("/")
    if len(nodes) == 0:
        return HttpError404()
    if path[len(path) - 1] == "/":
        nodes.pop()
    base = GetModel(nodes[0])
    if base is None:
        return HttpError404(nodes[0])
    name = None
    parent = None
    manager = None
    working = None
    attribute = None
    if len(nodes) > 1:
        try:
            working = base.objects.get(pk=nodes[1])
        except (ValueError, ValidationError):
            return HttpError400(
                "invalid id value '%s' for model '%s'" % (nodes[1], nodes[0])
            )
        except ObjectDoesNotExist:
            return HttpError404()
        if working is None:
            return HttpError404()
        for x in range(2, len(nodes)):
            if manager is not None:
                try:
                    working = manager.all().get(pk=nodes[x])
                except ValueError:
                    return HttpError400("invalid id value '%s'" % nodes[x])
                except ObjectDoesNotExist:
                    return HttpError404()
                if working is not None:
                    manager = None
                    continue
                return HttpError404(nodes[x])
            name = None
            attribute, has = getAttr(working, nodes[x], request.method == "PUT")
            if not has:
                return HttpError404(nodes[x])
            if callable(attribute):
                attribute = attribute()
                LogHttp.debug(
                    "Created a new (pre) working object type '%s'."
                    % attribute.__class__.__name__
                )
            if isinstance(attribute, Model):
                parent = working
                working = attribute
                attribute = None
            elif "many_to_" in str(attribute.__class__):
                manager = attribute
                parent = working
                working = None
            else:
                if x + 1 != len(nodes):
                    return HttpError400("invalid uri paramaters after attribute")
                name = nodes[x]
    LogHttp.debug(
        "RestFul routing complete (pending remix), working '%s', parent '%s', name '%s', attribute '%s'."
        % (working, parent, name, attribute)
    )
    if request.method == "PUT":
        if working is None:
            if attribute is not None and hasattr(attribute, "model"):
                working = attribute.model()
            else:
                working = base()
        LogHttp.debug(
            "Created a new (post) working object type '%s'" % working.__class__.__name__
        )
    elif request.method == "GET" and working is None:
        if attribute is None:
            attribute = base.objects
        result = list()
        for obj in attribute.all():
            try:
                r = restFunc(request, obj, request.method, name, parent)
                if r is not None:
                    if isinstance(r, HttpError):
                        return r
                    result.append(r)
            except HttpError as err:
                return err
            except Exception as err:
                return HttpError500("error calling 'restFunc'", err)
        return Response({MULTI_RESULT_KEY: result})
    LogHttp.debug(
        "RestFul routing complete (remix complete), working '%s', parent '%s', name '%s', attribute '%s'."
        % (working, parent, name, attribute)
    )
    if working is None:
        if request.method == "GET":
            if attribute is None:
                attribute = base.objects
            content = list()
            for obj in attribute.all():
                item = restFunc(request, obj, request.method, name, parent)
                content.append(item)
        else:
            attribute = base
    if working is None and request.method == "POST":
        return HttpError400("cannot create an object via POST")
    if working is None and request.method == "DELETE":
        return HttpError400("cannot delete an object without an identifier")
    try:
        response = restFunc(request, working, request.method, name, parent)
        if isinstance(response, HttpError):
            return response
        status = 200
        if request.method == "PUT":
            status = 201
        return Response(response, status=status)
    except HttpError as err:
        return err


def getAttr(obj, name, use_meta=False):
    if len(name) == 0 or name is None:
        return None, False
    if hasattr(obj, name):
        r = getattr(obj, name)
        if r is None and use_meta:
            try:
                r = obj._meta.get_field(name).model
            except (AttributeError, FieldDoesNotExist):
                pass
        return r, True
    tname = name.title()
    if hasattr(obj, tname):
        r = getattr(obj, tname)
        if r is None and use_meta:
            try:
                r = obj._meta.get_field(tname).related_model
            except (AttributeError, FieldDoesNotExist):
                pass
        return r, True
    lname = name.lower()
    if hasattr(obj, lname):
        r = getattr(obj, lname)
        if r is None and use_meta:
            try:
                r = obj._meta.get_field(lname).model
            except (AttributeError, FieldDoesNotExist):
                pass
        return r, True
    tname = lname.title()
    if hasattr(obj, lname.title()):
        r = getattr(obj, tname)
        if r is None and use_meta:
            try:
                r = obj._meta.get_field(tname).model
            except (AttributeError, FieldDoesNotExist):
                pass
        return r, True
    if lname[len(lname) - 1] != "s":
        sname = "%ss" % lname
        if hasattr(obj, sname):
            r = getattr(obj, sname)
            if r is None and use_meta:
                try:
                    r = obj._meta.get_field(sname).model
                except (AttributeError, FieldDoesNotExist):
                    pass
            return r, True
        if hasattr(obj, sname.title()):
            r = getattr(obj, sname.title())
            if r is None and use_meta:
                try:
                    r = obj._meta.get_field(sname.title()).model
                except (AttributeError, FieldDoesNotExist):
                    pass
            return r, True
    uname = name.upper()
    if hasattr(obj, uname):
        r = getattr(obj, uname)
        if r is None and use_meta:
            try:
                r = obj._meta.get_field(uname).model()
            except (AttributeError, FieldDoesNotExist):
                pass
        return r, True
    return None, False


def checkFunc(obj, name):
    func = None
    if hasattr(obj, name):
        func = getattr(obj, name)
    if callable(func):
        return func
    lname = name.lower()
    if hasattr(obj, lname):
        func = getattr(obj, name)
    if callable(func):
        return func
    return None


def Response(content, status=200):
    if not isinstance(content, dict):
        return HttpResponse(content=content, status=status)
    if "version" not in content:
        content["version"] = settings.VERSION
    return HttpResponse(
        content=dumps(content), status=status, content_type="application/json"
    )


def restFunc(request, obj, method, name, parent):
    # check perms here
    LogAuth.debug(
        "Checking RestFul auth now for model '%s' and method %s.."
        % (obj.__class__.__name__, method)
    )
    if method == "GET":
        func = checkFunc(obj, "RestGet")
        if func is not None:
            try:
                response = func(parent, name.lower() if name is not None else name)
                if response is not None:
                    return response
            except TypeError:
                pass
        if name is not None:
            value, has = getAttr(obj, name.lower())
            if has:
                if value is None:
                    return str()
                return value
            return HttpError404(name)
        func = checkFunc(obj, "RestJSON")
        if func is not None:
            try:
                return func()
            except TypeError:
                pass
        return HttpError403(
            "object '%s' does not define any GET or JSON functions"
            % obj.__class__.__name__
        )
    elif method == "DELETE":
        func = checkFunc(obj, "RestDelete")
        if func is not None:
            try:
                response = func(parent, name.lower() if name is not None else name)
                if response is not None:
                    return response
                return {"status": "success"}
            except TypeError:
                pass
            except Exception as err:
                return HttpError500("error occured during RestDelete", err)
        return HttpError405(method)
    secondary = None
    try:
        content = request.body.decode("UTF-8")
    except UnicodeDecodeError:
        return HttpError400("invalid UTF-8 data")
    if content is None or (name is None and len(content) == 0):
        return HttpError400("invalid or empty data content")
    if name is None:
        try:
            data = loads(content)
        except JSONDecodeError as err:
            return HttpError400("invalid JSON syantax", cause=err)
        if data is None or len(data) == 0:
            return HttpError400("invalid or empty data content")
        if len(data) == 1 and method == "PUT":
            if "uuid" in data:
                try:
                    secondary = GetModel(obj.__class__.__name__).objects.get(
                        pk=data["uuid"]
                    )
                except ObjectDoesNotExist:
                    pass
                else:
                    LogHttp.debug(
                        "Found a PUT request with just an PK as data, loading that object '%s' with POST"
                        % secondary
                    )
            elif "id" in data:
                try:
                    secondary = GetModel(obj.__class__.__name__).objects.get(
                        pk=data["id"]
                    )
                except ObjectDoesNotExist:
                    pass
                else:
                    LogHttp.debug(
                        "Found a PUT request with just an PK as data, loading that object '%s' with POST"
                        % secondary
                    )
    else:
        data = content
    if method == "POST" or secondary is not None:
        if secondary is not None:
            obj = secondary
        func = checkFunc(obj, "RestPost")
        if func is not None:
            try:
                response = func(
                    parent, name.lower() if name is not None else name, data
                )
                if response is not None:
                    return response
            except TypeError:
                pass
            except Exception as err:
                return HttpError500("error occured during RestDelete", err)
    elif method == "PUT":
        func = checkFunc(obj, "RestPut")
        if func is not None:
            try:
                response = func(
                    parent, name.lower() if name is not None else name, data
                )
                if response is not None:
                    return response
            except TypeError:
                pass
            except Exception as err:
                return HttpError500("error occured during RestDelete", err)
    return HttpError405(method)
