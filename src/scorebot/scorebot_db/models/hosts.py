#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from socket import getservbyport
from django.core.exceptions import ValidationError
from netaddr import IPNetwork, AddrFormatError, IPAddress
from scorebot_utils.constants import (
    PORT_TYPES,
    SERVICE_STATUS,
    SERVICE_DEFAULT_VALUE,
    HOST_DEFAULT_VALUE,
)
from django.db.models import (
    Model,
    CharField,
    AutoField,
    ForeignKey,
    BooleanField,
    DateTimeField,
    PositiveSmallIntegerField,
    GenericIPAddressField,
    PositiveIntegerField,
    CASCADE,
)


class Host(Model):
    class Meta:
        db_table = "host"
        verbose_name = "Host"
        verbose_name_plural = "Hosts"

    ID = AutoField(
        db_column="id",
        verbose_name="Host ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    Network = ForeignKey(
        db_column="network",
        verbose_name="Host Network",
        on_delete=CASCADE,
        null=False,
        to="scorebot_db.Network",
        related_name="Hosts",
    )
    Enabled = BooleanField(
        db_column="enabled", verbose_name="Host Enabled", null=False, default=True
    )
    Name = CharField(
        db_column="fqdn", verbose_name="Host FQDN", max_length=256, null=False
    )
    IP = GenericIPAddressField(
        db_column="address", verbose_name="Host IP", null=False, unpack_ipv4=True
    )
    Scoretime = DateTimeField(
        db_column="scoretime",
        verbose_name="Host Last Scored",
        null=True,
        blank=True,
        editable=False,
    )
    Online = BooleanField(
        db_column="online",
        verbose_name="Host Online",
        null=False,
        default=False,
        editable=False,
    )
    Nickname = CharField(
        db_column="nickname",
        verbose_name="Host Nickname",
        max_length=64,
        null=True,
        blank=True,
    )
    Value = PositiveSmallIntegerField(
        db_column="value",
        verbose_name="Host Value",
        null=False,
        default=HOST_DEFAULT_VALUE,
    )
    Tolerance = PositiveSmallIntegerField(
        db_column="tolerance", verbose_name="Host Ping Tolerance", null=True, blank=True
    )

    def team(self):
        if self.Network.Team is not None:
            return self.Network.Team
        return None

    def game(self):
        t = self.team()
        if t is not None:
            return t.game()
        return None

    def servies(self):
        return self.Services.all().filter(Enabled=True)

    def __len__(self):
        return self.Services.all().count()

    def __str__(self):
        t = self.team()
        if t is not None:
            if not self.Enabled:
                return "[D] %s %s (%s) %dpts" % (
                    t.fullname(),
                    self.Nickname,
                    str(self.IP),
                    self.Value,
                )
            return "%s %s (%s) %dpts" % (
                t.fullname(),
                self.Nickname,
                str(self.IP),
                self.Value,
            )
        if not self.Enabled:
            return "[D] %s (%s) %dpts" % (self.Nickname, str(self.IP), self.Value)
        return "%s (%s) %dpts" % (self.Nickname, str(self.IP), self.Value)

    def rest_json(self):
        r = {
            "id": self.ID,
            "fqdn": self.Name,
            "name": self.Nickname,
            "ip": str(self.IP),
            "online": self.Online,
            "enabled": self.Enabled,
            "value": self.Value,
            "network": self.Network.ID,
        }
        t = self.team()
        if t is not None:
            r["team"] = t.base().ID
        if self.Tolerance is not None:
            r["tolerance"] = self.Tolerance
        if self.Scoretime is not None:
            r["scoretime"] = self.Scoretime.isoformat()
        return r

    def save(self, *args, **kwargs):
        if self.Nickname is None:
            v = self.Name
            if "." in self.Name:
                v = self.Name.split(".")[0]
            else:
                self.Name = "%s.%s" % (self.Name, self.Network.Domain)
            if len(v) < 64:
                self.Nickname = v
            else:
                self.Nickname = v[:64]
        n = IPNetwork(self.Network.Subnet)
        try:
            a = IPAddress(str(self.IP))
            if a not in n:
                raise ValidationError(
                    'IP Address "%(address)s" is not in Network range "%(range)s"',
                    code="invalid",
                    params={"address": str(self.IP), "range": self.Network.Subnet},
                )
            del a
            del n
        except AddrFormatError:
            raise ValidationError(
                'IP Address "%(address)s" is not valid',
                code="invalid",
                params={"address": str(self.IP)},
            )
        return super().save(*args, **kwargs)


class Service(Model):
    class Meta:
        db_table = "services"
        verbose_name = "Service"
        verbose_name_plural = "Services"

    ID = AutoField(
        db_column="id",
        verbose_name="Service ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    Port = PositiveIntegerField(
        db_column="port", verbose_name="Service Port", null=False
    )
    Enabled = BooleanField(
        db_column="enabled", verbose_name="Service Enabled", null=False, default=True
    )
    Status = PositiveSmallIntegerField(
        db_column="status",
        verbose_name="Service Status",
        null=False,
        default=0,
        choices=SERVICE_STATUS,
        editable=False,
    )
    Protocol = PositiveSmallIntegerField(
        db_column="protocol",
        verbose_name="Service Protocol",
        null=False,
        default=0,
        choices=PORT_TYPES,
    )
    Flags = PositiveSmallIntegerField(
        db_column="flags", verbose_name="Service Flags", null=False, default=0
    )
    Value = PositiveSmallIntegerField(
        db_column="value",
        verbose_name="Service Value",
        null=False,
        default=SERVICE_DEFAULT_VALUE,
    )
    Host = ForeignKey(
        db_column="host",
        verbose_name="Service Host",
        on_delete=CASCADE,
        null=False,
        to="scorebot_db.Host",
        related_name="Services",
    )
    Name = CharField(
        db_column="name",
        verbose_name="Service Name",
        null=True,
        max_length=64,
        blank=True,
    )
    Application = CharField(
        db_column="application",
        verbose_name="Service Application",
        null=True,
        max_length=64,
        blank=True,
    )

    def __str__(self):
        if not self.Enabled:
            return "[D] %s\%s (%d/%s) %dpts" % (
                self.Host.Name,
                self.Name,
                self.Port,
                self.get_Protocol_display(),
                self.Value,
            )
        return "%s\%s (%d/%s) %dpts" % (
            self.Host.Name,
            self.Name,
            self.Port,
            self.get_Protocol_display(),
            self.Value,
        )

    def rest_json(self):
        r = {
            "id": self.ID,
            "port": self.Port,
            "enable": self.Enabled,
            "status": self.Status,
            "protocol": self.Protocol,
            "flags": self.Flags,
            "value": self.Value,
            "host": self.Host.ID,
            "name": self.Name,
            "application": self.Application,
        }
        if hasattr(self, "Content"):
            r["content"] = self.Content.ID
        return r

    def save(self, *args, **kwargs):
        if self.Name is None:
            try:
                self.Name = getservbyport(self.Port)
            except OSError:
                self.Name = "%d" % self.Port
        return super().save(*args, **kwargs)
