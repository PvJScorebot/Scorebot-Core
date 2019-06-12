#!/usr/bin/python3
# Scorebot UDP (Universal Development Platform)
#
# The Scorebot Project / iDigitalFlame 2019

from django.db.transaction import atomic
from scorebot_utils.constants import new_color
from scorebot_utils.generic import create_model, get_by_id, get_bool
from scorebot_utils.restful import HttpError428, HttpError404, REST_RESULT_KEY
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
    Manager,
)


def create_team(team, scoring, player, game, data, step):
    if team is not None:
        b = team
    else:
        b = Team()
    if scoring is not None and step >= 1:
        s = scoring
    else:
        s = ScoringTeam()
    if player is not None and step >= 2:
        p = player
    else:
        p = PlayerTeam()
    with atomic():
        b.Game = game
        b.Name = data["name"]
        b.save()
        if step >= 1:
            s.Team = b
            s.save()
        if step >= 2:
            p.Team = s
            p.Color = data.get("color", new_color())
            sid = data.get("store", None)
            if sid is not None:
                try:
                    p.Store = int(sid)
                except ValueError:
                    raise HttpError428("store id is a number")
            p.Offense = get_bool(data.get("offense", False))
            t = create_model("Token")
            t.Name = str(t.UUID).split("-")[0]
            t.save()
            p.Token = t
            p.save()
            return t
    return None


class TeamManager(Manager):
    def get(self, *args, **kwargs):
        r = super(Manager, self).get(*args, **kwargs)
        if r is not None:
            s = r.get()
            if s is not None:
                return s
        return r

    def get_base(self, *args, **kwargs):
        return super(Manager, self).get(*args, **kwargs)


class Team(Model):
    class Meta:
        db_table = "teams"
        verbose_name = "Team"
        verbose_name_plural = "Teams"

    __parents__ = [("game", "Game")]
    __exposes__ = [
        "id",
        "game",
        "name",
        "score",
        "score_id",
        "color",
        "store",
        "offense",
        "logo",
        "player_id",
        "network",
        "hosts",
    ]

    objects = TeamManager()
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

    def get(self):
        if hasattr(self, "Scoring") and hasattr(self.Scoring, "Player"):
            return self.Scoring.Player
        if hasattr(self, "Scoring"):
            return self.Scoring
        return None

    def base(self):
        return self

    def game(self):
        return self.Game

    def score(self):
        if hasattr(self, "Scoring"):
            return self.Scoring.Score
        return None

    def __str__(self):
        s = self.get()
        if s is not None:
            return s.__str__()
        return "[System] %s" % self.fullname()

    def fullname(self):
        return "%s\%s" % (self.Game.Name, self.Name)

    def rest_json(self):
        s = self.get()
        if s is not None:
            return s.rest_json()
        return {"id": self.ID, "name": self.Name, "game": self.Game.ID}

    def is_player(self):
        return hasattr(self, "Scoring") and hasattr(self.Scoring, "Player")

    def is_scoring(self):
        return hasattr(self, "Scoring")

    def set_token(self, token):
        self.Token = token
        self.save()

    def rest_get(self, parent, name):
        if name == "id":
            return self.ID
        elif name == "game":
            return self.Game
        elif name == "name":
            return self.Name
        if name == "network" and hasattr(self, "Networks"):
            return self.Networks
        if hasattr(self, "Scoring"):
            if name == "score":
                return self.Scoring.Score
            elif name == "score_id":
                return self.Scoring.ID
            if hasattr(self.Scoring, "Player"):
                if name == "color":
                    return self.Scoring.Player.Color
                elif name == "store":
                    return self.Scoring.Player.Store
                elif name == "offense":
                    return self.Scoring.Player.Offense
                elif name == "logo":
                    return self.Scoring.Player.Logo
                elif name == "player_id":
                    return self.Scoring.Player.ID
        return None

    def rest_put(self, parent, data):
        if "name" not in data:
            return HttpError428("team name")
        if parent is None:
            return HttpError428("team game")
        if "player" in data or "color" in data or "offense" in data or "store" in data:
            t = create_team(self, None, None, parent, data, 2)
        elif "score" in data:
            t = create_team(self, None, None, parent, data, 1)
        else:
            t = create_team(self, None, None, parent, data, 0)
        r = self.rest_json()
        if t is not None:
            r["token"] = {"name": t.Name, "uuid": str(t.UUID)}
        return r

    def rest_delete(self, parent, name):
        s = self.get()
        if s is not None:
            return s.rest_delete(parent)
        if name is None:
            self.delete()
        return None

    def rest_post(self, parent, name, data):
        s = self.Get()
        if s is not None:
            return s.rest_post(parent, name, data)
        if parent is not None:
            self.Game = parent
        if name is None:
            if "game" in data:
                g = get_by_id("Game", data["game"])
                if g is None:
                    return HttpError404("game id")
                self.Game = g
            if "name" in data:
                self.Name = data["name"]
            self.save()
        else:
            if name == "name":
                self.Name = data
            elif name == "game":
                g = get_by_id("Game", data)
                if g is None:
                    return HttpError404("game id")
                self.Game = g
        self.save()
        return self.rest_json()


class ScoringTeam(Model):
    class Meta:
        db_table = "teams_scoring"
        verbose_name = "Scoring Team"
        verbose_name_plural = "Scoring Teams"

    __hidden__ = True
    __parents__ = Team.__parents__
    __exposes__ = Team.__exposes__

    objects = TeamManager()
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
        related_name="Owner",
    )

    def get(self):
        if hasattr(self, "Player"):
            return self.Player
        return None

    def base(self):
        return self.Team

    def game(self):
        return self.Team.Game

    def score(self):
        return self.Score

    def __str__(self):
        s = self.get()
        if s is not None:
            return s.__str__()
        return "[Scoring] %s %dpts" % (self.Team.fullname(), self.Score.Value)

    def fullname(self):
        return self.Team.fullname()

    def rest_json(self):
        s = self.get()
        if s is not None:
            return s.rest_json()
        return {
            "id": self.Team.ID,
            "name": self.Team.Name,
            "score": self.Score.Value,
            "game": self.Team.Game.ID,
            "score_id": self.ID,
        }

    def is_player(self):
        return hasattr(self.Scoring, "Player")

    def is_scoring(self):
        return True

    def set_token(self, token):
        self.Team.Token = token
        self.Team.save()

    def save(self, *args, **kwargs):
        if self.Score is None:
            self.Score = create_model("Score", save=True)
        super().save(*args, **kwargs)

    def rest_get(self, parent, name):
        if name == "id":
            return self.Team.ID
        elif name == "game":
            return self.Team.Game
        elif name == "name":
            return self.Team.Name
        elif name == "score":
            return self.Score
        elif name == "score_id":
            return self.ID
        if name == "network" and hasattr(self.Team, "Networks"):
            return self.Team.Networks
        if hasattr(self, "Player"):
            if name == "color":
                return self.Player.Color
            elif name == "store":
                return self.Player.Store
            elif name == "offense":
                return self.Player.Offense
            elif name == "logo":
                return self.Player.Logo
            elif name == "player_id":
                return self.Player.ID
        return None

    def rest_put(self, parent, data):
        if "name" not in data:
            return HttpError428("team name")
        if parent is None:
            return HttpError428("team game")
        if "player" in data or "color" in data or "offense" in data or "store" in data:
            t = create_team(None, self, None, parent, data, 2)
        else:
            t = create_team(None, self, None, parent, data, 1)
        r = self.rest_json()
        if t is not None:
            r["token"] = {"name": t.Name, "uuid": str(t.UUID)}
        return r

    def rest_delete(self, parent, name):
        s = self.get()
        if s is not None:
            return s.rest_delete(parent)
        if name is None:
            self.delete()
            self.Team.delete()
        return None

    def rest_post(self, parent, name, data):
        s = self.get()
        if s is not None:
            return s.rest_post(parent, name, data)
        return self.Team.rest_post(parent, name, data)


class PlayerTeam(Model):
    class Meta:
        db_table = "teams_player"
        verbose_name = "Pleyer Team"
        verbose_name_plural = "Player Teams"

    __hidden__ = True
    __parents__ = Team.__parents__
    __exposes__ = Team.__exposes__

    objects = TeamManager()
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
        default=new_color,
        max_length=9,
    )
    Store = IntegerField(
        db_column="store", verbose_name="Team Store ID", null=True, blank=True
    )
    Offense = BooleanField(
        db_column="offense", verbose_name="Team Can Attack", null=False, default=False
    )
    Logo = ImageField(db_column="logo", verbose_name="Team Logo", null=True, blank=True)

    def get(self):
        return None

    def base(self):
        return self.Team.Team

    def game(self):
        return self.Team.Team.Game

    def score(self):
        return self.Team.Score

    def __str__(self):
        if self.Offense:
            return "[Player] %s %dpts Attacker" % (
                self.Team.Team.fullname(),
                self.Team.Score.Value,
            )
        return "[Player] %s %dpts" % (self.Team.Team.fullname(), self.Team.Score.Value)

    def fullname(self):
        return self.Team.Team.fullname()

    def rest_json(self):
        r = {
            "id": self.Team.Team.ID,
            "name": self.Team.Team.Name,
            "game": self.Team.Team.Game.ID,
            "score": self.Team.Score.Value,
            "color": self.Color,
            "store_id": self.Store,
            "offensive": self.Offense,
            "player_id": self.ID,
            "score_id": self.Team.ID,
        }
        if self.Logo:
            r["logo"] = self.Logo.url
        return r

    def is_player(self):
        return True

    def is_scoring(self):
        return True

    def set_token(self, token):
        self.Team.Team.Token = token
        self.Team.Team.save()

    def hosts(self, scorable=False):
        # This is a cool example of a function that facilitates the API calls as a function.
        # THis is function is somewhat useless in my opinon. WHy? well its a static, so you can't index further.
        hosts = list()
        for n in self.Team.Team.Networks.filter(Enabled=True):
            if scorable:
                hl = n.Hosts.all().filter(Enable=True, Scoretime__isnull=True)
            else:
                hl = n.Hosts.all().filter(Enabled=True)
            for h in hl:
                hosts.append(h.rest_json())
        return {REST_RESULT_KEY: hosts}

    def rest_get(self, parent, name):
        if name == "id":
            return self.Team.Team.ID
        elif name == "game":
            return self.Team.Team.Game
        elif name == "name":
            return self.Team.Team.Name
        elif name == "score":
            return self.Team.Score
        elif name == "score_id":
            return self.Team.ID
        elif name == "color":
            return self.Color
        elif name == "store":
            return self.Store
        elif name == "offense":
            return self.Offense
        elif name == "logo":
            return self.Logo
        elif name == "player_id":
            return self.ID
        elif name == "network" and hasattr(self.Team.Team, "Networks"):
            return self.Team.Team.Networks
        elif name == "hosts":
            return self.hosts()
        return None

    def rest_put(self, parent, data):
        if "name" not in data:
            return HttpError428("team name")
        if parent is None:
            return HttpError428("team game")
        t = create_team(None, None, self, parent, data, 2)
        r = self.rest_json()
        r["token"] = {"name": t.Name, "uuid": str(t.UUID)}
        return r

    def rest_delete(self, parent, name):
        if name is None:
            self.delete()
            self.Team.delete()
            self.Team.Team.delete()
        return None

    def rest_post(self, parent, name, data):
        if parent is not None:
            self.Game = parent
        if name is None:
            if "game" in data:
                g = get_by_id("Game", data["game"])
                if g is None:
                    return HttpError404("game id")
                self.Game = g
            if "name" in data:
                self.Name = data["name"]
            if "color" in data:
                self.Color = data["color"]
            if "store" in data:
                try:
                    self.Store = int(data["store"])
                except ValueError:
                    raise HttpError428("store id is a number")
            if "offense" in data:
                self.Offense = get_bool(data["offense"])
            self.save()
        else:
            if name == "name":
                self.Name = data
            elif name == "game":
                g = get_by_id("Game", data)
                if g is None:
                    return HttpError404("game id")
                self.Game = g
            elif name == "color":
                self.Color = data
            elif name == "store":
                try:
                    self.Store = int(data)
                except ValueError:
                    raise HttpError428("store id is a number")
            elif name == "offense":
                self.Offense = get_bool(data)
        self.save()
        return self.rest_json()
