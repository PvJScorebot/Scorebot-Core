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

from django.utils.dateparse import parse_datetime
from django.utils.timezone import now, make_aware
from scorebot_utils.restful import HttpError428, HttpError404
from scorebot_utils import get_cached_option, set_cached_option
from scorebot_utils.generic import print_delta, create_model, get_by_id
from scorebot_utils.constants import (
    GAME_MODES,
    GAME_STATUS,
    GAME_TEAM_GOLD,
    GAME_TEAM_GRAY,
    OPTION_DEFAULTS,
)
from django.db.models import (
    Model,
    CharField,
    AutoField,
    DateTimeField,
    ForeignKey,
    PositiveSmallIntegerField,
    SET_NULL,
    ObjectDoesNotExist,
)


class Game(Model):
    class Meta:
        db_table = "games"
        verbose_name = "Game"
        verbose_name_plural = "Games"

    ID = AutoField(
        db_column="id",
        verbose_name="Game ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    Name = CharField(
        db_column="name", verbose_name="Game Name", null=False, max_length=255
    )
    Start = DateTimeField(
        db_column="start", verbose_name="Game Start Time", null=True, blank=True
    )
    End = DateTimeField(
        db_column="end", verbose_name="Game End Time", null=True, blank=True
    )
    Mode = PositiveSmallIntegerField(
        db_column="mode",
        verbose_name="Game Mode",
        null=False,
        default=0,
        choices=GAME_MODES,
    )
    Status = PositiveSmallIntegerField(
        db_column="status",
        verbose_name="Game Status",
        null=False,
        default=0,
        choices=GAME_STATUS,
    )
    Options = ForeignKey(
        db_column="options",
        verbose_name="Game Options",
        null=True,
        on_delete=SET_NULL,
        to="scorebot_db.Option",
        blank=True,
        related_name="Game",
    )

    def __str__(self):
        if self.Start is not None and self.End is not None:
            return "Game %s/%s %s (%s - %s)" % (
                self.Name,
                self.get_Mode_display(),
                self.get_Status_display(),
                self.Start.strftime("%m/%d/%y %H:%M"),
                self.End.strftime("%m/%d/%y %H:%M"),
            )
        if self.Start is not None and self.End is None and self.Status == 1:
            return "Game %s/%s %s (%s, running: %s)" % (
                self.Name,
                self.get_Mode_display(),
                self.get_Status_display(),
                self.Start.strftime("%m/%d/%y %H:%M"),
                print_delta((now() - self.Start).seconds),
            )
        return "Game %s/%s %s" % (
            self.Name,
            self.get_Mode_display(),
            self.get_Status_display(),
        )

    def rest_json(self):
        r = {
            "id": self.ID,
            "mode": self.Mode,
            "mode_str": self.get_Mode_display().lower(),
            "status": self.Status,
            "status_str": self.get_Status_display().lower(),
            "name": self.Name,
        }
        if self.End is not None:
            r["end"] = self.End.isoformat()
        if self.Start is not None:
            r["start"] = self.Start.isoformat()
        if self.Options is not None:
            r["options"] = self.Options.ID
        return r

    def gold_team(self):
        try:
            return self.Teams.all().get(Name__exact=GAME_TEAM_GOLD)
        except ObjectDoesNotExist:
            return self.create_team(GAME_TEAM_GOLD)

    def create_team(self, name):
        if name is None or len(name) == 0:
            return ValueError("name")
        t = create_model("Team")
        t.Name = name
        t.Game = self
        t.save()
        return t

    def save(self, *args, **kwargs):
        if self.Status >= 1 and self.Start is None:
            self.Start = now()
        if self.Status >= 3 and self.End is None:
            self.End = now()
        v = super().save(*args, **kwargs)
        if self.Teams.all().count() == 0:
            self.create_team(GAME_TEAM_GOLD)
            self.ceate_team_scoring(GAME_TEAM_GRAY)
        return v

    def rest_put(self, parent, data):
        if "name" not in data and parent is None:
            return HttpError428("game name")
        if "options" in data:
            try:
                o = get_by_id("Options", data["options"])
            except ObjectDoesNotExist:
                return HttpError404("options id")
            self.Options = o
        self.Name = data["name"]
        if "start" in data:
            if data["start"] == "now":
                self.Start = now()
            else:
                self.Start = make_aware(parse_datetime(data["start"]))
        if "end" in data:
            self.End = make_aware(parse_datetime(data["end"]))
        if "mode" in data:
            try:
                self.Mode = int(data["mode"])
            except ValueError:
                raise HttpError428("mode is a number")
            if not (0 <= self.Mode < len(GAME_MODES)):
                raise HttpError428("mode is out of bounds")
        if "status" in data:
            try:
                self.Status = int(data["status"])
            except ValueError:
                raise HttpError428("status is a number")
            if not (0 <= self.Status < len(GAME_STATUS)):
                raise HttpError428("status is out of bounds")
        self.save()
        return self.rest_json()

    def create_team_player(self, name):
        t = self.ceate_team_scoring(name)
        p = create_model("PlayerTeam")
        p.Team = t
        p.save()
        return p

    def ceate_team_scoring(self, name):
        t = self.create_team(name)
        s = create_model("ScoringTeam")
        s.Team = t
        s.save()
        return s

    def rest_delete(self, parent, name):
        if name == "options":
            self.Options = None
            self.save()
        else:
            self.delete()
        return None

    def get_option(self, name, value=None):
        o = get_cached_option(self.ID, name)
        if o is not None:
            return o
        if self.Options is None and value is not None:
            set_cached_option(self.ID, value)
            return value
        value = OPTION_DEFAULTS.get(name)
        if self.Options is None:
            if value is not None:
                set_cached_option(self.ID, value)
            return value
        fvalue = self.Options.get(name, value)
        if fvalue is not None:
            set_cached_option(self.ID, fvalue)
            return fvalue
        set_cached_option(self.ID, value)
        return value

    def rest_post(self, parent, name, data):
        if name is None:
            return self.rest_put(self, data)
        if name == "name":
            self.Name = data
        elif name == "options":
            try:
                o = get_by_id("Options", data["options"])
            except ObjectDoesNotExist:
                return HttpError404("options id")
            self.Options = o
        elif name == "start":
            if data == "now":
                self.Start = now()
            else:
                self.Start = make_aware(parse_datetime(data))
        elif name == "end":
            self.End = make_aware(parse_datetime(data))
        elif name == "mode":
            try:
                self.Mode = int(data)
            except ValueError:
                raise HttpError428("mode is a number")
            if not (0 <= self.Mode < len(GAME_MODES)):
                raise HttpError428("mode is out of bounds")
        if data == "status":
            try:
                self.Status = int(data)
            except ValueError:
                raise HttpError428("status is a number")
            if not (0 <= self.Status < len(GAME_STATUS)):
                raise HttpError428("status is out of bounds")
        self.save()
        return self.rest_json()
