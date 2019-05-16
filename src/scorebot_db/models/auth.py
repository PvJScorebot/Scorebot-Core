#!/usr/bin/false
#
# Scorebotv4 - The Scorebot Project
# 2018 iDigitalFlame / The Scorebot / CTF Factory Team
#
# Scorebot AAA Django Models

from uuid import uuid4, UUID
from scorebot.util import new
from django.forms import ModelForm
from django.utils.timezone import now
from scorebot.constants import AUTHORIZATION_NAMES
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.db.models import Model, Manager, CASCADE, UUIDField, DateTimeField, BigIntegerField, OneToOneField


class AuthorizationForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(ModelForm, self).__init__(*args, **kwargs)


class AuthorizationManager(Manager):
    def get_key(self, uuid):
        try:
            token = Token.objects.get(uid=UUID(uuid))
        except (ValueError, ObjectDoesNotExist, MultipleObjectsReturned):
            return None
        else:
            try:
                return self.get(token=token)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                return None
            finally:
                del token
        return None


class Token(Model):
    class Meta:
        get_latest_by = 'expires'
        verbose_name = '[Access] Authentication Token'
        verbose_name_plural = '[Access] Authentication Tokens'

    class Admin:
        exclude = ('uid',)
        readonly_fields = ('uid',)

    expires = DateTimeField('Token Expire Time', null=True, blank=True)
    uid = UUIDField('Token UUID', primary_key=True, default=uuid4, editable=False)

    def __str__(self):
        if self.expires is not None:
            return '[Token] %s (%s)' % (str(self.uid), self.expires.strftime('%m/%d/%y %H:%M'))
        return '[Token] %s (No Expire)' % str(self.uid)

    def __len__(self):
        if self.expires is not None:
            return max((self.expires - now()).seconds, 0)
        return 0

    def __bool__(self):
        return len(self) > 0 or self.expires is None


class Authorization(Model):
    class Meta:
        verbose_name = '[Access] Access Token'
        verbose_name_plural = '[Access] Access Tokens'

    form = AuthorizationForm
    objects = AuthorizationManager()
    access = BigIntegerField('Access Boolean Byte', default=0)
    token = OneToOneField('scorebot_db.Token', on_delete=CASCADE, related_name='keys', null=True, blank=True)

    def __str__(self):
        return '[Authorization] %s - %s' % (hex(self.access), str(self.token))

    def __getitem__(self, value):
        if isinstance(value, int):
            bit = value
        elif isinstance(value, str):
            if value.upper() not in AUTHORIZATION_NAMES:
                raise KeyError('The Authorization Name "%s" does not exist!' % value.upper())
            bit = AUTHORIZATION_NAMES[value.upper()]
        else:
            raise KeyError('The Authorization value provided must be a Python string or integer!')
        return (self.access & (1 << bit)) > 0

    def save(self, *args, **kwargs):
        if self.token is None:
            self.token = new('Token')
        Model.save(self, *args, **kwargs)

    def __setitem__(self, name, value):
        if isinstance(value, int):
            bit = value
        elif isinstance(value, str):
            if value.upper() not in AUTHORIZATION_NAMES:
                raise KeyError('The Authorization Name "%s" does not exist!' % value.upper())
            bit = AUTHORIZATION_NAMES[value.upper()]
        else:
            raise KeyError('The Authorization value provided must be a Python string or integer!')
        if bool(value):
            self.access = (self.access | (1 << bit))
        else:
            self.access = (self.access & (~(1 << bit)))

# EOF
