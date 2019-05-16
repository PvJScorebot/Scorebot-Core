#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from django.db.models import (
    Model,
    CharField,
    AutoField,
    ForeignKey,
    BooleanField,
    ManyToManyField,
    SET_NULL,
    ObjectDoesNotExist,
)


class Network(Model):
    class Meta:
        db_table = "network"
        verbose_name = "Network"
        verbose_name_plural = "Networks"

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
        db_column="enabled", verbose_name="Network Enabled", null=False, default=False
    )
    Nameservers = ManyToManyField(
        db_column="nameservers",
        verbose_name="Network Nameservers",
        on_delete=SET_NULL,
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

    def __str__(self):
