#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from django.db.transaction import atomic
from scorebot_utils.constants import NewColor
from scorebot_utils.generic import CreateModel, GetManager
from scorebot_utils.restful import HttpError428, HttpError404
from django.db.models import (
    Model,
    ImageField,
    CharField,
    AutoField,
    ForeignKey,
    BooleanField,
    IntegerField,
    OneToOneField,
    SET_NULL,
    CASCADE,
    ObjectDoesNotExist,
)


class Team(Model):
    class Meta:
        db_table = "teams"
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    ID = AutoField(
        db_column="id",
        verbose_name="Team ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    Game = ForeignKey(
        db_column="Team Game",
        verbose_name="Team Game",
        null=False,
        on_delete=CASCADE,
        to="scorebot_db.Game",
        related_name="Teams",
    )
    Name = CharField(
        db_column="name", verbose_name="Team Name", null=False, max_length=255
    )
    Token = OneToOneField(
        db_column="token",
        verbose_name="Team Token",
        null=True,
        on_delete=SET_NULL,
        to="scorebot_db.Token",
        blank=True,
    )

    def __str__(self):
        s = self.GetScore()
        if s is not None:
            return "%s %dpts" % (self.Fullname(), s.Score())
        return self.Fullname()

    def GetGame(self):
        return self.Game

    def GetScore(self):
        if hasattr(self, "Scoring"):
            return self.Scoring.Score
        return None

    def Fullname(self):
        return "%s\%s" % (self.Game.Name, self.Name)

    def GetPlayer(self):
        if hasattr(self, "Scoring") and hasattr(self.Scoring, "Player"):
            return self.Scoring.Player
        return None

    def RestJSON(self):
        if hasattr(self, "Scoring") and hasattr(self.Scoring, "Player"):
            return self.Scoring.Player.RestJSON()
        if hasattr(self, "Scoring"):
            return self.Scoring.RestJSON()
        return {"id": self.ID, "name": self.Name, "game": self.GetGame().ID}

    def SetToken(self, token):
        self.Token = token
        self.save()

    """def RestDelete(self, parent, name):
        if name is None:
            self.delete()
            return
        else:
            if name == "name":
                self.name = ""
            elif name == "score":
                s = self.GetScore()
                if s is not None:
                    s.delete()
            elif name == "token":
                self.Token.delete()
            elif (
                name == "logo"
                or name == "color"
                or name == "store"
                or name == "offensive"
            ):
                p = self.GetPlayer()
                if p is not None:
                    if name == "logo":
                        p.Logo = None
                    elif name == "color":
                        p.Color = NewColor()
                    elif name == "store":
                        p.Store = None
                    elif name == "offensive":
                        p.Offense = False
                    p.save()
            self.save()
        return None

    def RestPut(self, parent, name, data):
        if "name" not in data:
            return HttpError428("team name")
        if "game" not in data:
            return HttpError428("team game")
        try:
            g = GetManager("Game").get(data["game"])
        except ObjectDoesNotExist:
            return HttpError404("game %s" % data["game"])
        with atomic():
            self.Game = g
            self.Name = data["name"]
            self.save()
            if (
                "score" in data
                or "color" in data
                or "logo" in data
                or "store" in data
                or "offensive" in data
                or "player" in data
            ):
                ts = CreateModel("ScoringTeam")
                ts.Team = self
                ts.save()
                if (
                    "color" in data
                    or "logo" in data
                    or "store" in data
                    or "offensive" in data
                    or "player" in data
                ):
                    tp = CreateModel("PlayerTeam")
                    tp.Team = ts
        if "expires" in data:
            self.Expires = make_aware(parse_datetime(data["expires"]))
        self.save()
        r = {"name": self.Name, "uuid": str(self.UUID)}
        if self.Expires is not None:
            r["expires"] = self.Expires.isoformat()
        return r

    def RestPost(self, parent, name, data):
        if name is None:
            return None
        if name.lower() == "name":
            self.Name = data
        elif name.lower() == "expires":
            if data == "now":
                self.Expires = now()
            else:
                self.Expires = make_aware(parse_datetime(data))
        self.save()
        return self.RestJSON()"""


class ScoringTeam(Model):
    class Meta:
        db_table = "teams_scoring"
        verbose_name = "Scoring Team"
        verbose_name_plural = "Scoring Teams"

    ID = AutoField(
        db_column="id",
        verbose_name="Team ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    Team = OneToOneField(
        db_column="team",
        verbose_name="Team",
        null=False,
        on_delete=CASCADE,
        to="scorebot_db.Team",
        related_name="Scoring",
    )
    Score = OneToOneField(
        db_column="score",
        verbose_name="Team Score",
        null=True,
        on_delete=CASCADE,
        to="scorebot_db.Score",
        blank=True,
    )

    def __str__(self):
        return "%s %dpts" % (self.Team, self.Score.Score())

    def GetGame(self):
        return self.Team.Game

    def GetScore(self):
        return self.Score

    def Fullname(self):
        return self.Team.Fullname()

    def RestJSON(self):
        if hasattr(self, "Player"):
            return self.Player.RestJSON()
        return {
            "id": self.ID,
            "name": self.Team.Name,
            "game": self.GetGame().ID,
            "score": self.GetScore().Score(),
        }

    def GetPlayer(self):
        if hasattr(self, "Player"):
            return self.Player
        return None

    def SetToken(self, token):
        self.Team.SetToken(token)
        self.save()

    def save(self, *args, **kwargs):
        if self.Score is None:
            self.Score = CreateModel("Score", save=True)
        super().save(*args, **kwargs)


class PlayerTeam(Model):
    class Meta:
        db_table = "teams_player"
        verbose_name = "Pleyer Team"
        verbose_name_plural = "Player Teams"

    ID = AutoField(
        db_column="id",
        verbose_name="Team ID",
        null=False,
        primary_key=True,
        editable=False,
    )
    Team = OneToOneField(
        db_column="team",
        verbose_name="Team",
        null=False,
        on_delete=CASCADE,
        to="scorebot_db.ScoringTeam",
        related_name="Player",
    )
    Color = CharField(
        db_column="color",
        verbose_name="Team Color",
        null=False,
        default=NewColor,
        max_length=9,
    )
    Store = IntegerField(
        db_column="store", verbose_name="Team Store ID", null=True, blank=True
    )
    Offense = BooleanField(
        db_column="offense", verbose_name="Team Can Attack", null=False, default=False
    )
    Logo = ImageField(db_column="logo", verbose_name="Team Logo", null=True, blank=True)

    def __str__(self):
        if not self.Offense:
            return "%s [D]" % self.Team.__str__()
        return self.Team.__str__()

    def GetGame(self):
        return self.Team.Team.Game

    def GetScore(self):
        return self.Team.Score

    def Fullname(self):
        return self.Team.Team.Fullname()

    def RestJSON(self):
        resp = {
            "id": self.ID,
            "name": self.Team.Team.Name,
            "game": self.GetGame().ID,
            "score": self.GetScore().Score(),
            "color": self.Color,
            "store_id": self.Store,
            "offensive": self.Offense,
        }
        if self.Logo:
            resp["logo"] = self.Logo.url
        return resp

    def GetPlayer(self):
        return self

    def SetToken(self, token):
        self.Team.SetToken(token)
        self.save()
