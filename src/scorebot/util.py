#!/usr/bin/false
#
# Scorebotv4 - The Scorebot Project
# 2018 iDigitalFlame / The Scorebot / CTF Factory Team
#
# Scorebot Utilities & Functions

from scorebot.constants import AuthenticateMessage, GenericMessage

#from scorebot.util import unrest


from random import randint
from django.conf.urls import url
from json import loads, JSONDecodeError
from django.apps import AppConfig
from django.core.serializers import serialize
from django.core.handlers.wsgi import WSGIRequest
from scorebot import Authentication, Models, General, Name, Version, HTTP_HEADER
from django.core.exceptions import ValidationError, ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponseBadRequest, HttpResponseForbidden, HttpResponse, HttpResponseNotFound, \
                        HttpResponseServerError, HttpResponse, HttpResponseNotAllowed, JsonResponse
from scorebot.constants import AUTHENTICATE_MESSAGE_INVALID, AUTHENTICATE_MESSAGE_NO_HEADER, \
                               AUTHENTICATE_MESSAGE_INVALID_TOKEN, AUTHENTICATE_MESSAGE_EXPIRED, \
                               AUTHENTICATE_MESSAGE_MISSING_PERM
from django.db.models import AutoField, IntegerField, CharField, ManyToManyField, ManyToOneRel, OneToOneField, \
                             ForeignKey, ManyToManyRel, QuerySet

try:
    from ipware.ip import get_ip as _get_ip
except ImportError as err:
    Authentication.warning(
        'Django IPware is not installed, all IP address lookups will be attempted using header META lookups!'
    )

    def _get_ip(request):
        try:
            return str(request.META['REMOTE_ADDR'])
        except KeyError:
            pass
        return 'ERR-DJANGO-IPWARE-MISSING'


class ScorebotAPI(AppConfig):
    name = 'scorebot_api'
    verbose_name = 'Scorebot4 API'


class ScorebotDatabase(AppConfig):
    name = 'scorebot_db'
    verbose_name = 'Scorebot4 Database'


class ScorebotResponse(JsonResponse):
    def __init__(self, message, status=200, fields=None, data=None):
        if isinstance(fields, dict) and isinstance(message, str):
            message = message.format(**fields)
        if data is None:
            JsonResponse.__init__(self, status=status, data={'result': message, 'engine': '%s %s' % (Name, Version)})
        else:
            HttpResponse.__init__(self, status=status, content=serialize('json', {'derp': data}))
        self.setdefault('content_type', 'application/json')


class ScorebotError(ValidationError):
    def __init__(self, error):
        ValidationError.__init__(self, error)


def get(name):
    return Models.get(name.lower(), None)


def ip(request):
    return str(_get_ip(request))


def hex_color():
    return ('#%s' % hex(randint(0, 0xFFFFFF))).replace('0x', '')


def new(name, save=False):
    model = get(name)
    if callable(model):
        instance = model()
        if instance is not None and save:
            instance.save()
        return instance
    return None


def lookup_address(hostname):
    return '127.0.0.1'


def authenticate(perms=None, fields=None, methods=None):
    def _auth_wrapper(function):
        def _auth_wrapped(*args, **kwargs):
            err = _authenticate(args[0], function, perms, fields, methods)
            if err is not None:
                return err
            return function(*args, **kwargs)
        return _auth_wrapped
    return _auth_wrapper


def _authenticate(request, function, perms=None, fields=None, methods=None):
    if not isinstance(request, WSGIRequest):
        Authentication.warning('[INVALID] Connected, but did not produce any valid HTTP headers!')
        return JsonResponse(status=400, data=AuthenticateMessage.INVALID)
    request.ip = ip(request)
    if methods is not None:
        if isinstance(methods, str):
            methods = [methods]
        if isinstance(methods, list) and request.method not in methods:
            return ScorebotResponse(status=405, message=methods) ##
    Authentication.debug('[%s] Connected to the Scorebot API!' % request.ip)
    if HTTP_HEADER not in request.META:
        Authentication.error('[%s] Connected without an Authorization Header!' % request.ip)
        return ScorebotResponse(status=403, message=AuthenticateMessage.HEADERS)
    request.auth = Models['authorization'].objects.get_key(request.META[HTTP_HEADER])
    if request.auth is None:
        Authentication.error('[%s] Submitted an invalid token!' % request.ip)
        return ScorebotResponse(status=403, message=AuthenticateMessage.TOKEN)
    if not request.auth:
        Authentication.error('[%s] Submitted an expired token "%s"!' % (request.ip, str(request.auth.token)))
        return ScorebotResponse(status=403, message=AuthenticateMessage.EXPIRED)
    Authentication.debug('[%s: %s] Connected to the Scorebot API, using token: "%s".' % (
        request.ip, str(request.auth.token.uid), str(request.auth.token.uid)
    ))
    if isinstance(perms, list):
        for item in perms:
            if not request.auth[item]:
                Authentication.error(
                    '[%s: %s] Attempted to access function "%s" which requires the "%s" permission!'
                    % (request.ip, str(request.auth.token.uid), str(function.__qualname__), item)
                )
                return ScorebotResponse(status=403, message=AuthenticateMessage.PERMISSION, fields={'perm': str(item)})
    elif isinstance(perms, str) or isinstance(perms, int):
        if not request.auth[perms]:
            Authentication.error('[%s: %s] Attempted to access function "%s" which requires the "%s" permission!' % (
                request.ip, str(request.auth.token.uid), str(function.__qualname__), perms
            ))
            return ScorebotResponse(status=403, message=AuthenticateMessage.PERMISSION, fields={'perm': str(perms)})
    if fields is not None:
        Authentication.debug('[%s: %s] Required the JSON fields "%s", checking.')
        try:
            json_body = request.body.decode('UTF-8')
        except UnicodeDecodeError as err:
            Authentication.warning('[%s: %s] Attempted to use non UTF-8 encoding to send JSON data!' % (
                request.ip, str(request.auth.token.uid)
            ), err)
            return ScorebotResponse(status=400, message=GenericMessage.ENCODING)
        try:
            request.json = loads(json_body)
        except JSONDecodeError as err:
            Authentication.warning('[%s: %s] Attempted to send invalid JSON data!' % (
                request.ip, str(request.auth.token.uid)
            ), err)
            return ScorebotResponse(status=400, message=GenericMessage.FORMAT)
        finally:
            del json_body
        if isinstance(fields, str) and fields not in request.json:
            Authentication.warning('[%s: %s] Attempted to send JSON data that lacks the required field value "%s"!' % (
                request.ip, str(request.auth.token.uid), fields
            ))
            return ScorebotResponse(status=400, message=GenericMessage.FIELD, fields={'fields': fields})
        elif isinstance(fields, list):
            for field in fields:
                if str(field) not in request.json:
                    Authentication.warning(
                        '[%s: %s] Attempted to send JSON data that lacks the required field value "%s"!'
                        % (request.ip, str(request.auth.token.uid), fields)
                    )
                    return ScorebotResponse(status=400, message=GenericMessage.FIELD, fields={'fields': field})
    Authentication.info('[%s: %s]: Successfully Authenticated using token "%s", passing control to function "%s"!' % (
        request.ip, str(request.auth.token.uid), str(function.__qualname__)
    ))
    return None


"""def authenticate_team(field, perms=None, fields=None, beacon=False, offensive=False,  methods=None):
    def _auth_wrapper(function):
        def _auth_wrapped(*args, **kwargs):
            if fields is not None:
                fields = field
            else:
                fields.insert(0, field)
            err = _authenticate(args[0], function, perms, fields, methods)
            if err is not None:
                return err
            return function(*args, **kwargs)
        return _auth_wrapped
    return _auth_wrapper"""



# EOF
