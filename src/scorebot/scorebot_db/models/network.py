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

from dns.resolver import Resolver
from netaddr import IPNetwork, AddrFormatError
from django.core.exceptions import ValidationError
from django.db.models import (
    Model,
    CharField,
    AutoField,
    ForeignKey,
    BooleanField,
    ManyToManyField,
    DateTimeField,
    PositiveSmallIntegerField,
    GenericIPAddressField,
    SET_NULL,
    CASCADE,
    ObjectDoesNotExist,
)


class DNS(Model):
    class Meta:
        db_table = "nameservers"
        verbose_name = "Nameserver"
        verbose_name_plural = "Nameservers"

    __parent__ = [("network", "Network")]

    ID = AutoField(
        db_column="id",
        verbose_name="Nameserver ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    IP = GenericIPAddressField(
        db_column="address", verbose_name="Nameserver IP", null=False, unpack_ipv4=True
    )

    def __str__(self):
        return "Nameserver (%s)" % str(self.IP)

    def rest_json(self):
        return {"id": self.ID, "ip": str(self.IP)}

    def lookup(self, name):
        resq = Resolver()
        resq.timeout = 5
        resq.nameservers = [str(self.IP)]
        try:
            resp = resq.query(name)
            del resq
            if len(resp) > 0:
                return resp[0].address
        except Exception as err:
            return None
        return None


class Network(Model):
    class Meta:
        db_table = "networks"
        verbose_name = "Network"
        verbose_name_plural = "Networks"

    __parent__ = [("team", "Team"), ("team", "ScoringTeam"), ("team", "PlayerTeam")]

    ID = AutoField(
        db_column="id",
        verbose_name="Network ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    Subnet = CharField(
        db_column="subnet", verbose_name="Network Subnet", null=False, max_length=128
    )
    Domain = CharField(
        db_column="domain", verbose_name="Network Domain", null=False, max_length=255
    )
    Enabled = BooleanField(
        db_column="enabled", verbose_name="Network Enabled", null=False, default=True
    )
    Nameservers = ManyToManyField(
        db_column="nameservers",
        verbose_name="Network Nameservers",
        to="scorebot_db.DNS",
        blank=True,
    )
    Team = ForeignKey(
        db_column="team",
        verbose_name="Network Team",
        on_delete=SET_NULL,
        null=True,
        blank=True,
        to="scorebot_db.Team",
        related_name="Networks",
    )

    def game(self):
        if self.Team is not None:
            return self.Team.game()
        return None

    def __len__(self):
        return self.Hosts.all().count()

    def __str__(self):
        if self.Team is None:
            if not self.Enabled:
                return "[D] %s (%s) %d Hosts" % (
                    self.Domain,
                    self.Subnet,
                    self.Hosts.all().count(),
                )
            return "%s (%s) %d Hosts" % (
                self.Domain,
                self.Subnet,
                self.Hosts.all().count(),
            )
        if not self.Enabled:
            return "[D] %s\%s (%s) %d Hosts" % (
                self.Team.fullname(),
                self.Domain,
                self.Subnet,
                self.Hosts.all().count(),
            )
        return "%s\%s (%s) %d Hosts" % (
            self.Team.fullname(),
            self.Domain,
            self.Subnet,
            self.Hosts.all().count(),
        )

    def rest_json(self):
        r = {
            "id": self.ID,
            "subnet": self.Subnet,
            "enabled": self.Enabled,
            "domain": self.Domain,
            "nameservers": [n.rest_json() for n in self.Nameservers.all()],
        }
        if self.Team is not None:
            r["team"] = self.Team.ID
        return r

    def lookup(self, name):
        resq = Resolver()
        resq.timeout = 5
        resq.nameservers = [str(n.IP) for n in self.Nameservers.all()]
        if len(resq) == 0:
            del resq
            return None
        try:
            resp = resq.query(name)
            del resq
            if len(resp) > 0:
                return resp[0].address
        except Exception as err:
            return None
        return None

    def save(self, *args, **kwargs):
        if "/" not in self.Subnet:
            raise ValidationError(
                'Subnet "%(subnet)s" must be in slash notation',
                code="invalid",
                params={"subnet": self.Subnet},
            )
        try:
            n = IPNetwork(self.Subnet)
            if len(n) <= 1:
                raise ValidationError(
                    'Subnet "%(subnet)s" is not valid',
                    code="invalid",
                    params={"subnet": self.Subnet},
                )
        except AddrFormatError:
            raise ValidationError(
                'Subnet "%(subnet)s" is not valid',
                code="invalid",
                params={"subnet": self.Subnet},
            )
        return super().save(*args, **kwargs)
