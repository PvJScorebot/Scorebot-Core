#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from scorebot_utils.restful import HttpError428
from scorebot_utils.constants import PORT_TYPES
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


class Port(Model):
    class Meta:
        db_table = "ports"
        verbose_name = "Port"
        ordering = ["Game", "Number"]
        verbose_name_plural = "Ports"

    __parents__ = [("game", "Game")]

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

    def rest_json(self):
        return {
            "id": self.ID,
            "game": self.Game.ID,
            "type": self.Type,
            "type_str": self.get_Type_display(),
            "number": self.Number,
        }

    def save(self, *args, **kwargs):
        if self.Type == 2:
            self.Number = 0
        try:
            p = Port.objects.get(Number=self.Number, Game=self.Game, Type=self.Type)
            if not hasattr(self, "ID") or self.ID != p.ID:
                raise ValidationError(
                    'Port "%(port)d/%(type)s" is already open for Game "%(game)s"',
                    code="invalid",
                    params={
                        "port": self.Number,
                        "type": self.get_Type_display().lower(),
                        "game": self.Game.Name,
                    },
                )
        except ObjectDoesNotExist:
            pass
        super().save(*args, **kwargs)

    def rest_put(self, parent, data):
        if parent is not None:
            self.Game = parent
        if "number" not in data and self.ID is None:
            return HttpError428("port number")
        try:
            self.Number = int(data["number"])
        except ValueError:
            return HttpError428("port number is a number")
        if "type" in data:
            try:
                self.Type = int(data["type"])
            except ValueError:
                return HttpError428("port type is a number")
            if not (0 < self.Type < len(PORT_TYPES)):
                return HttpError428("port number out of bounds")
        self.save()
        return self.rest_json()

    def rest_delete(self, parent, name):
        if name is None:
            self.delete()
        return None

    def rest_post(self, parent, name, data):
        if name is None:
            return self.rest_post(parent, data)
        if name == "number":
            try:
                self.Number = int(data)
            except ValueError:
                return HttpError428("port number is a number")
        elif name == "type":
            try:
                self.Type = int(data)
            except ValueError:
                return HttpError428("port number is a number")
        self.save()
        return self.rest_json()
