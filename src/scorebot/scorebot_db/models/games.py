#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from django.utils.timezone import now
from scorebot_utils.generic import PrintDelta, CreateModel
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

GAME_MODES = (
    (0, "Red vs Blue"),
    (1, "Blue vs Blue"),
    (2, "King"),
    (4, "High Ground"),
    (5, "Score Attack"),
)
GAME_STATUS = (
    (0, "Not Started"),
    (1, "Running"),
    (2, "Paused"),
    (3, "Completed"),
    (4, "Stopped"),
    (5, "Archivd"),
)
GAME_TEAM_GOLD = "Gold Team"
GAME_TEAM_GRAY = "Gray Team"


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
                PrintDelta((now() - self.Start).seconds),
            )
        return "Game %s/%s %s" % (
            self.Name,
            self.get_Mode_display(),
            self.get_Status_display(),
        )

    def GoldTeam(self):
        try:
            return self.Teams.all().get(Name__exact=GAME_TEAM_GOLD)
        except ObjectDoesNotExist:
            return self.CreateTeam(GAME_TEAM_GOLD)

    def CreateTeam(self, name):
        if name is None or len(name) == 0:
            return ValueError("name")
        t = CreateModel("Team")
        t.Name = name
        t.Game = self
        t.save()
        return t

    def save(self, *args, **kwargs):
        if self.Status >= 1 and self.Start is None:
            self.Start = now()
        if self.Status >= 3 and self.End is None:
            self.End = now()
        super().save(*args, **kwargs)
        if self.Teams.all().count() == 0:
            try:
                g = self.Teams.all().get(Name__exact=GAME_TEAM_GOLD)
                if hasattr(g, "Scoring"):
                    g.Scoring.delete()
                    g.Scoring = None
                    g.save()
            except ObjectDoesNotExist:
                super().save(*args, **kwargs)
                self.CreateTeam(GAME_TEAM_GOLD)
            try:
                g = self.Teams.all().get(Name__exact=GAME_TEAM_GRAY)
                if not hasattr(g, "Scoring"):
                    s = CreateModel("ScoringTeam")
                    s.Team = g
                    s.save()
                p = s.Scoring
                if hasattr(p, "Player"):
                    p.Player.delete()
                    p.Player = None
                    p.save()
            except ObjectDoesNotExist:
                super().save(*args, **kwargs)
                self.CreateScoringTeam(GAME_TEAM_GRAY)

    def CreatePlayerTeam(self, name):
        t = self.CreateScoringTeam(name)
        p = CreateModel("PlayerTeam")
        p.Team = t
        p.save()
        return p

    def CreateScoringTeam(self, name):
        t = self.CreateTeam(name)
        s = CreateModel("ScoringTeam")
        s.Team = t
        s.save()
        return s
