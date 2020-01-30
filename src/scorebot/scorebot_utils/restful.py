#!/usr/bin/false
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

from sys import exc_info
from django.conf import settings
from django.http import HttpResponse
from traceback import format_exception
from scorebot_utils import log_auth, log_http
from json import dumps, loads, JSONDecodeError
from django.views.decorators.csrf import csrf_exempt
from django.db.models import ObjectDoesNotExist, Model
from scorebot_utils.generic import get_model, is_model, get_by_id
from django.core.exceptions import ValidationError, FieldDoesNotExist
from scorebot_utils.constants import (
    ERROR_400,
    ERROR_401,
    ERROR_403,
    ERROR_404,
    ERROR_405,
    ERROR_428,
    ERROR_500,
    ERROR_401_MESSAGE,
    ERROR_403_MESSAGE,
    ERROR_404_MESSAGE,
    ERROR_405_MESSAGE,
    ERROR_428_MESSAGE,
    ERROR_404_MESSAGE_ALT,
    REST_FUNC_GET,
    REST_FUNC_PUT,
    REST_FUNC_JSON,
    REST_FUNC_POST,
    REST_FUNC_DLETE,
    REST_FUNC_EXPOSES,
    REST_FUNC_PARENTS,
    REST_RESULT_KEY,
    HTTP_GET,
    HTTP_PUT,
    HTTP_POST,
    HTTP_DELETE,
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
            self.set_content(message, code, cause)

    def set_content(self, message, code, cause=None):
        log_http.error(
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
            self.set_content(
                ERROR_403_MESSAGE.format(permissions=",".join(message)), ERROR_403
            )
        else:
            self.set_content(message, ERROR_403)


class HttpError404(HttpError):
    def __init__(self, message=None):
        super().__init__("", 404)
        if message is not None:
            self.set_content(ERROR_404_MESSAGE.format(requested=message), ERROR_404)
        else:
            self.set_content(ERROR_404_MESSAGE_ALT, ERROR_404)


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
def rest(request, path):
    log_http.debug("RESTFul: Request %s for '%s'." % (request.method, path))
    nodes = path.split("/")
    if len(nodes) == 0:
        return HttpError400("invalid nodes")
    if path[len(path) - 1] == "/":
        nodes.pop()
    base = get_model(nodes[0])
    if base is None:
        return HttpError404(nodes[0])
    if getattr(base._meta, "abstract") and base._meta.abstract:
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
                    return HttpError404("id value '%s' does not exist" % nodes[x])
                if working is not None:
                    manager = None
                    name = None
                    continue
                return HttpError404(nodes[x])
            name = None
            attribute, has = get_attr(working, nodes[x], request.method == HTTP_PUT)
            if not has:
                return HttpError404(nodes[x])
            if "many_to_" in str(attribute.__class__):
                manager = attribute
                parent = working
                working = None
            elif callable(attribute):
                attribute = attribute()
                log_http.debug(
                    "RESTFul: Created a new (pre) working object type '%s'."
                    % attribute.__class__.__name__
                )
            if isinstance(attribute, Model):
                parent = working
                working = attribute
                attribute = None
            elif manager is None:
                if x + 1 != len(nodes):
                    return HttpError400("invalid uri paramaters after attribute")
                name = nodes[x]
    log_http.debug(
        "RESTFul: Routing complete (pending remix), working '%s', parent '%s', name '%s', attribute '%s'."
        % (
            working if working is None else working.__class__.__name__,
            parent,
            name,
            attribute,
        )
    )
    if request.method == HTTP_PUT:
        if working is None:
            if attribute is not None and hasattr(attribute, "model"):
                working = attribute.model()
            else:
                working = base()
        log_http.debug(
            "RESTFul: Created a new (post) working object type '%s'"
            % working.__class__.__name__
        )
    elif request.method == HTTP_GET and working is None:
        if attribute is None:
            attribute = base.objects
        name = None
        result = list()
        log_http.debug("RESTFul: GET list requested, gathering an object list..")
        for obj in attribute.all():
            try:
                r = rest_func(request, obj, request.method, name, parent)
                if r is not None:
                    if isinstance(r, HttpError):
                        return r
                    result.append(r)
            except HttpError as err:
                return err
            except ValidationError as err:
                return HttpError400("invalid format '%s'" % ", ".join(err.message()))
            except Exception as err:
                return HttpError500("error calling 'rest_func'", err)
        del name
        del parent
        del working
        del attribute
        return new_response({REST_RESULT_KEY: result})
    log_http.debug(
        "RESTFul: Routing complete (remix complete), working '%s', parent '%s', name '%s', attribute '%s'."
        % (
            working if working is None else working.__class__.__name__,
            parent,
            name,
            attribute,
        )
    )
    if working is None:
        if request.method == HTTP_GET:
            if attribute is None:
                attribute = base.objects
            content = list()
            for obj in attribute.all():
                item = rest_func(request, obj, request.method, name, parent)
                content.append(item)
        else:
            attribute = base
    if working is None and request.method == HTTP_POST:
        del name
        del parent
        del attribute
        return HttpError400("cannot create an object via POST")
    if working is None and request.method == HTTP_DELETE:
        del name
        del parent
        del attribute
        return HttpError400("cannot delete an object without an identifier")
    try:
        response = rest_func(request, working, request.method, name, parent)
        if isinstance(response, HttpError):
            return response
        status = 200
        if request.method == HTTP_PUT:
            status = 201
        log_http.debug("RESTFul: Complete, returning results.")
        del name
        del parent
        del working
        del attribute
        return new_response(response, status=status)
    except HttpError as err:
        return err
    except Exception as err:
        return HttpError500("error calling 'rest_func'", err)


def get_field(obj, name):
    try:
        return obj._meta.get_field(name).related_model
    except (AttributeError, FieldDoesNotExist):
        pass
    return None


def check_func(obj, name):
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


def new_response(content, status=200):
    if not isinstance(content, dict):
        return HttpResponse(content=content, status=status)
    if "version" not in content:
        content["version"] = settings.VERSION
    return HttpResponse(
        content=dumps(content), status=status, content_type="application/json"
    )


def get_attr(obj, name, use_meta=False):
    if hasattr(obj, REST_FUNC_EXPOSES):
        exp = getattr(obj, REST_FUNC_EXPOSES)
        log_http.debug(
            "RESTFul: Checking an exposed attributes list with %d entries." % len(exp)
        )
        if isinstance(exp, list) and name.lower() in exp:
            func = check_func(obj, REST_FUNC_GET)
            if func is not None:
                try:
                    log_http.debug(
                        "RESTFul: Checking an exposed attribute '%s' against the rest get function."
                        % name
                    )
                    return func(None, name), True
                except Exception:
                    pass
            return None, True
    if len(name) == 0 or name is None:
        return None, False
    if hasattr(obj, name):
        r = getattr(obj, name)
        if r is None and use_meta:
            r = get_field(name)
        return r, True
    tname = name.title()
    if hasattr(obj, tname):
        r = getattr(obj, tname)
        if r is None and use_meta:
            r = get_field(tname)
        return r, True
    lname = name.lower()
    if hasattr(obj, lname):
        r = getattr(obj, lname)
        if r is None and use_meta:
            r = get_field(lname)
        return r, True
    tname = lname.title()
    if hasattr(obj, lname.title()):
        r = getattr(obj, tname)
        if r is None and use_meta:
            r = get_field(tname)
        return r, True
    if lname[len(lname) - 1] != "s":
        sname = "%ss" % lname
        if hasattr(obj, sname):
            r = getattr(obj, sname)
            if r is None and use_meta:
                r = get_field(sname)
            return r, True
        if hasattr(obj, sname.title()):
            r = getattr(obj, sname.title())
            if r is None and use_meta:
                r = get_field(sname.title())
            return r, True
    uname = name.upper()
    if hasattr(obj, uname):
        r = getattr(obj, uname)
        if r is None and use_meta:
            r = get_field(uname)
        return r, True
    return None, False


def rest_func(request, obj, method, name, parent):
    # check perms here
    log_auth.debug(
        "RESTFul: Checking auth now for model '%s' and method %s.."
        % (obj.__class__.__name__, method)
    )
    if name is not None:
        name = name.lower()
    if method == HTTP_GET:
        func = check_func(obj, REST_FUNC_GET)
        if func is not None:
            try:
                response = func(parent, name)
                if response is not None:
                    return response
            except TypeError as err:
                log_http.error(
                    "RESTFul: received a TypeError when attempting to call function!",
                    err,
                )
        if name is not None:
            value, has = get_attr(obj, name.lower())
            if has:
                if value is None:
                    return str()
                elif callable(value):
                    return value()
                return value
            return HttpError404(name)
        func = check_func(obj, REST_FUNC_JSON)
        if func is not None:
            try:
                return func()
            except TypeError as err:
                log_http.error(
                    "RESTFul: received a TypeError when attempting to call function!",
                    err,
                )
        return HttpError403(
            "object '%s' does not define any GET or JSON functions"
            % obj.__class__.__name__
        )
    elif method == HTTP_DELETE:
        func = check_func(obj, REST_FUNC_DLETE)
        if func is not None:
            try:
                response = func(parent, name)
                if response is not None:
                    return response
                return {"status": "success"}
            except TypeError as err:
                log_http.error(
                    "RESTFul: received a TypeError when attempting to call function!",
                    err,
                )
            except ValidationError as err:
                return HttpError400("invalid format '%s'" % ", ".join(list(err)))
            except Exception as err:
                return HttpError500("error occured during rest delete", err)
        return HttpError405(method)
    try:
        content = request.body.decode("UTF-8")
    except UnicodeDecodeError:
        return HttpError400("invalid UTF-8 data")
    if content is None or (name is None and len(content) == 0):
        return HttpError400("invalid or empty data content")
    secondary = None
    if name is None:
        try:
            data = loads(content)
        except JSONDecodeError as err:
            return HttpError400("invalid JSON syantax", cause=err)
        if data is None or len(data) == 0 or not isinstance(data, dict):
            return HttpError400("invalid or empty data content")
        if len(data) == 1 and method == HTTP_PUT:
            if "uuid" in data:
                secondary = get_by_id(obj.__class__.__name__, data["uuid"])
            elif "id" in data:
                secondary = get_by_id(obj.__class__.__name__, data["id"])
            if secondary is not None:
                log_http.debug(
                    "RESTFul: Found a PUT request with just a PK as data, loading that object '%s' with POST"
                    % secondary
                )
        elif parent is None:
            if hasattr(obj, REST_FUNC_PARENTS):
                pl = getattr(obj, REST_FUNC_PARENTS)
                if isinstance(pl, list):
                    log_http.debug(
                        "RESTFul: No parent given, but object exposes %d parent types, testing now.."
                        % len(pl)
                    )
                    for p in pl:
                        if not isinstance(p, tuple):
                            continue
                        if p[0] in data:
                            m = get_by_id(data[p[0]])
                            if is_model(m, p[1]):
                                log_http.debug(
                                    "RESTFul: value for '%s' matches requested parent '%s', setting."
                                    % (p[0], p[1])
                                )
                                parent = m
                                break
    else:
        data = content
    if method == HTTP_POST or secondary is not None:
        if secondary is not None:
            obj = secondary
        func = check_func(obj, REST_FUNC_POST)
        if func is not None:
            try:
                response = func(parent, name, data)
                if response is not None:
                    return response
            except TypeError as err:
                log_http.error(
                    "RESTFul: received a TypeError when attempting to call function!",
                    err,
                )
            except ValidationError as err:
                return HttpError400("invalid format '%s'" % ", ".join(list(err)))
            except Exception as err:
                return HttpError500("error occured during rest post", err)
    elif method == HTTP_PUT:
        func = check_func(obj, REST_FUNC_PUT)
        if func is not None:
            try:
                response = func(parent, data)
                if response is not None:
                    return response
            except TypeError as err:
                log_http.error(
                    "RESTFul: received a TypeError when attempting to call function!",
                    err,
                )
            except ValidationError as err:
                return HttpError400("invalid format '%s'" % ", ".join(list(err)))
            except Exception as err:
                return HttpError500("error occured during rest put", err)
    return HttpError405(method)
