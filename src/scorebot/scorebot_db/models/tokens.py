#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from uuid import uuid4
from scorebot_utils.generic import IsModel
from django.contrib.admin import ModelAdmin
from django.utils.dateparse import parse_datetime
from django.utils.timezone import now, make_aware
from scorebot_utils.restful import HttpError403, HttpError428
from django.db.models import Model, CharField, UUIDField, DateTimeField

__rest_doc__ = """
    GET:
        recv: {
            "name": [string],
            "expires": [string, date iso8601]
        }
    POST:
        accept, recv: {
            "name": [string],
            "expires": [string, date iso8601]
        }
    PUT:
        accept {
            "name": [string],
            "expires": [string, date iso8601]
        }
        recv: {
            "uuid": [string, uuid],
            "name": [string],
            "expires": [string, date iso8601]
        }
    DELETE:
        accept, recv {}

    PARAMS: (rw) name, (rw) expires
"""


class Token(Model):
    class Meta:
        db_table = "tokens"
        verbose_name = "Token"
        verbose_name_plural = "Tokens"

    class TokenAdmin(ModelAdmin):
        exclude = ("UUID",)
        readonly_fields = ("UUID",)

    UUID = UUIDField(
        db_column="uuid",
        verbose_name="Token UUID",
        null=False,
        primary_key=True,
        editable=False,
        default=uuid4,
    )
    Name = CharField(
        db_column="name",
        verbose_name="Token Name",
        null=True,
        max_length=255,
        blank=True,
    )
    Expires = DateTimeField(
        db_column="expires", verbose_name="Token Expire Time", null=True, blank=True
    )

    def Valid(self):
        if self.Expires is None:
            return True
        return (self.Expires - now()).seconds > 0

    def __str__(self):
        if self.Expires is None:
            if self.Name is None or len(self.Name) == 0:
                return "Token %s" % str(self.UUID)
            return "%s (%s)" % (self.Name, str(self.UUID))
        if self.Name is None or len(self.Name) == 0:
            return "Token %s Until: %s" % (
                str(self.UUID),
                self.Expires.strftime("%m/%d/%y %H:%M"),
            )
        return "%s (%s) Until: %s" % (
            self.Name,
            str(self.UUID),
            self.Expires.strftime("%m/%d/%y %H:%M"),
        )

    def RestJSON(self):
        r = {"name": self.Name}
        if self.Expires is not None:
            r["expires"] = self.Expires.isoformat()
        return r

    def RestGet(self, parent, name):
        if name is not None and name == "uuid":
            raise HttpError403(
                "the uuid field is not accessable from the api interface"
            )
        return None

    def RestDelete(self, parent, name):
        if name is None:
            self.delete()
            return
        elif name == "expires":
            self.expires = None
            self.save()
        return None

    def RestPut(self, parent, name, data):
        if "name" not in data:
            return HttpError428("token name")
        self.Name = data["name"]
        if "expires" in data:
            self.Expires = make_aware(parse_datetime(data["expires"]))
        self.save()
        if (
            IsModel(parent, "Team")
            or IsModel(parent, "ScoringTeam")
            or IsModel(parent, "PlayerTeam")
        ):
            parent.SetToken(self)
        r = {"name": self.Name, "uuid": str(self.UUID)}
        if self.Expires is not None:
            r["expires"] = self.Expires.isoformat()
        return r

    def RestPost(self, parent, name, data):
        if isinstance(data, dict):
            if "name" in data:
                self.Name = data["name"]
            if "expires" in data:
                if data["expires"] == "now":
                    self.Expires = now()
                else:
                    self.Expires = make_aware(parse_datetime(data["expires"]))
        else:
            if name.lower() == "name":
                self.Name = data
            elif name.lower() == "expires":
                if data == "now":
                    self.Expires = now()
                else:
                    self.Expires = make_aware(parse_datetime(data))
        if (
            IsModel(parent, "Team")
            or IsModel(parent, "ScoringTeam")
            or IsModel(parent, "PlayerTeam")
        ):
            parent.SetToken(self)
        self.save()
        return self.RestJSON()
