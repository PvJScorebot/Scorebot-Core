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
    CONTENT_DEFAULT_VALUE,
)
from django.db.models import (
    Model,
    CharField,
    AutoField,
    ForeignKey,
    BooleanField,
    TextField,
    DateTimeField,
    PositiveSmallIntegerField,
    GenericIPAddressField,
    PositiveIntegerField,
    OneToOneField,
    CASCADE,
    ObjectDoesNotExist,
)


class Host(Model):
    class Meta:
        db_table = "hosts"
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
    Hidden = BooleanField(
        db_column="hidden",
        verbose_name="Host Hidden (No Score)",
        null=False,
        default=False,
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

    def fullname(self):
        t = self.team()
        if t is not None:
            return "%s\%s" % (t.fullname(), self.Nickname)
        return self.Nickname

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
        try:
            if Host.objects.get(Network__ID=self.Network.ID, IP=self.IP).ID != self.ID:
                raise ValidationError(
                    'Duplicate IP Address "%(address)s" already exists in Network range "%(range)s"',
                    code="invalid",
                    params={"address": str(self.IP), "range": self.Network.Subnet},
                )
        except ObjectDoesNotExist:
            pass
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
                self.Host.fullname(),
                self.Name,
                self.Port,
                self.get_Protocol_display(),
                self.Value,
            )
        return "%s\%s (%d/%s) %dpts" % (
            self.Host.fullname(),
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
            "status_str": self.get_Status_display().lower(),
            "protocol": self.Protocol,
            "protocol_str": self.get_Protocol_display().lower(),
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
        try:
            if (
                Service.objects.get(
                    Host__ID=self.Host.ID, Port=self.Port, Protocol=self.Protocol
                ).ID
                != self.ID
            ):
                raise ValidationError(
                    'Service "%(port)d/%(protocol)s" already exists on Host "%(host)s"',
                    code="invalid",
                    params={
                        "port": self.Port,
                        "protocol": self.get_Protocol_display(),
                        "host": self.Host.Name,
                    },
                )
        except ObjectDoesNotExist:
            pass
        if self.Name is None:
            try:
                self.Name = getservbyport(self.Port)
            except OSError:
                self.Name = "%d" % self.Port
        return super().save(*args, **kwargs)


class Content(Model):
    class Meta:
        db_table = "contents"
        verbose_name = "Service Content"
        verbose_name_plural = "Service Contents"

    ID = AutoField(
        db_column="id",
        verbose_name="Content ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    Value = PositiveSmallIntegerField(
        db_column="value",
        verbose_name="Content Value",
        null=False,
        default=CONTENT_DEFAULT_VALUE,
    )
    Type = CharField(
        db_column="type", verbose_name="Content Type", null=False, max_length=64
    )
    Data = TextField(
        db_column="data", verbose_name="Content Data", null=True, blank=True
    )
    Tolerance = PositiveSmallIntegerField(
        db_column="tolerance",
        verbose_name="Content Match Tolerance",
        null=True,
        blank=True,
    )
    Service = OneToOneField(
        db_column="service",
        verbose_name="Content Service",
        on_delete=CASCADE,
        null=False,
        to="scorebot_db.Service",
        related_name="Content",
    )

    def __str__(self):
        return "%s\%s (%s) %dpts" % (
            self.Service.Host.fullname(),
            self.Service.Name,
            self.Type,
            self.Value,
        )

    def rest_json(self):
        r = {
            "id": self.ID,
            "value": self.Value,
            "type": self.Type,
            "service": self.Service.ID,
            "data": "",
        }
        if self.Data is not None:
            r["data"] = self.Data
        return r
