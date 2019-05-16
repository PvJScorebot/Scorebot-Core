#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from uuid import uuid4
from django.utils.timezone import now
from django.contrib.admin import ModelAdmin
from django.db.models import Model, CharField, UUIDField, DateTimeField


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
