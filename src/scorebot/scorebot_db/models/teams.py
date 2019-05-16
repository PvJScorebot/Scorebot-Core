#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from random import randint
from scorebot_utils.generic import CreateModel
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
)


def _new_color():
    return ("#%s" % hex(randint(0, 0xFFFFFF))).replace("0x", "")


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

    def GetPlayer(self):
        if hasattr(self.Scoring, "Player"):
            return self.Player
        return None

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
        default=_new_color,
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
            return "%s [D]" % self.Team
        return self.Team

    def GetGame(self):
        return self.Team.Team.Game

    def GetScore(self):
        return self.Team.Score

    def Fullname(self):
        return self.Team.Team.Fullname()

    def GetPlayer(self):
        return self
