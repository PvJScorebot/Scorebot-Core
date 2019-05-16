#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from django.core.exceptions import ValidationError
from django.db.models import (
    Model,
    PositiveIntegerField,
    PositiveSmallIntegerField,
    ForeignKey,
    AutoField,
    CASCADE,
    ObjectDoesNotExist,
)

PORT_TYPES = ((0, "TCP"), (1, "UDP"), (2, "ICMP"))


class Port(Model):
    class Meta:
        db_table = "ports"
        verbose_name = "Port"
        ordering = ["Game", "Number"]
        verbose_name_plural = "Ports"

    ID = AutoField(
        db_column="id",
        verbose_name="Port ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    Game = ForeignKey(
        db_column="game",
        verbose_name="Port Game",
        null=False,
        on_delete=CASCADE,
        to="scorebot_db.Game",
        related_name="Ports",
    )
    Type = PositiveSmallIntegerField(
        db_column="type",
        verbose_name="Port Type",
        null=False,
        default=0,
        choices=PORT_TYPES,
    )
    Number = PositiveIntegerField(
        db_column="number", verbose_name="Port Number", null=False
    )

    def __str__(self):
        return "Port %d/%s (%s)" % (
            self.Number,
            self.get_Type_display(),
            self.Game.Name,
        )

    def save(self, *args, **kwargs):
        if self.Type == 2:
            self.Number = 0
        try:
            p = Port.objects.get(Number=self.Number, Game=self.Game)
            if not hasattr(self, "ID") or self.ID != p.ID:
                raise ValidationError(
                    'Port "%(port)d" is already open for Game "%(game)s"',
                    code="invalid",
                    params={"port": self.Number, "game": self.Game.Name},
                )
        except ObjectDoesNotExist:
            pass
        super().save(*args, **kwargs)
