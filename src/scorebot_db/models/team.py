#!/usr/bin/false
#
# Scorebotv4 - The Scorebot Project
# 2018 iDigitalFlame / The Scorebot / CTF Factory Team
#
# Scorebot Team Django Models

from uuid import UUID
from sys import maxsize
from html import escape
from datetime import timedelta
from scorebot import General, Events
from django.utils.timezone import now
from json import loads, JSONDecodeError
from django.http import HttpResponseBadRequest
from scorebot.util import new, get, hex_color, ip
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned, ValidationError
from scorebot.constants import MESSAGE_INVALID_FORMAT, TEAM_MESSAGE_NO_TEAM, TEAM_DEFAULT_FIELD, TEAM_DEFAULT_LOGO, \
                               TEAM_MESSAGE_MISSING_FIELD, MESSAGE_INVALID_ENCODING, TEAM_MESSAGE_EXPIRED, \
                               TEAM_MESSAGE_NOT_OFFENSIVE, MESSAGE_GAME_NO_RUNNING, TeamConstants
from django.db.models import Model, SET_NULL, ForeignKey, OneToOneField, BooleanField, CharField, ImageField, CASCADE, \
                             PositiveSmallIntegerField, BigIntegerField, PositiveIntegerField, ManyToManyField, \
                             Manager


class TeamManager(Manager):
    def get_team(self, uuid, beacon=False):
        try:
            uuid_string = UUID(str(uuid))
        except ValueError as err:
            return None
        else:
            try:
                token = get('Token').objects.get(uid=uuid_string)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                return None
            else:
                try:
                    if beacon:
                        return self.get(registered__in=[token])
                    return self.get(token=token)
                except (ObjectDoesNotExist, MultipleObjectsReturned):
                    return None
                finally:
                    del token
            finally:
                del uuid_string
        return None

    def get_team_token(self, uuid, beacon=False):
        try:
            uuid_string = UUID(str(uuid))
        except ValueError as err:
            return None, None
        else:
            try:
                token = get('Token').objects.get(uid=uuid_string)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                return None, None
            else:
                try:
                    if beacon:
                        return self.get(registered__in=[token]), token
                    return self.get(token=token), token
                except (ObjectDoesNotExist, MultipleObjectsReturned):
                    return None, None
            finally:
                del uuid_string
        return None, None

    def get_team_json(self, request, field=TEAM_DEFAULT_FIELD, beacon=False, offensive=False):
        client = ip(request)
        try:
            json_str = request.body.decode('UTF-8')
        except UnicodeDecodeError:
            General.error('[%s] Client attempted to submit an improperly encoded request!' & client)
            return None, None, None, HttpResponseBadRequest(content=MESSAGE_INVALID_ENCODING)
        try:
            json_data = loads(json_str)
        except JSONDecodeError:
            General.error('[%s] Client attempted to submit an improperly JSON formatted request!' & client)
            return None, None, None, HttpResponseBadRequest(content=MESSAGE_INVALID_FORMAT)
        finally:
            del json_str
        if field not in json_data:
            General.error('[%s] Data submitted by client is missing requested field "%s"!' & (client, field))
            return None, None, None, HttpResponseBadRequest(content=TEAM_MESSAGE_MISSING_FIELD.format(field=field))
        General.debug('[%s] Client connected with token "%s" to request a Team.' % (
            client, str(request.auth.token.uid)
        ))
        team, token = self.get_team_token(uuid=json_data[field], beacon=beacon)
        if team is None:
            General.info('[%s] Client attempted to use value "%s" to request a non-existant Team!' % (
                client, json_data[field])
            )
            return None, None, None, HttpResponseBadRequest(content=TEAM_MESSAGE_NO_TEAM)
        General.debug('[%s] Client connected and requested Team "%s" with Token "%s".' % (
            client, team.get_path(), json_data[field]
        ))
        if not team.token.__bool__():
            General.error('[%s] Client attempted to use token "%s" that has expired!' % (
                client, str(team.token.uid)
            ))
            return None, None, None, HttpResponseBadRequest(content=TEAM_MESSAGE_EXPIRED)
        if offensive:
            team = team.get_playingteam()
            if team is None or not team.offensive:
                General.error(
                    '[%s] Client connected and requested Team "%s" with Token "%s", but Team is not marked Offensive!'
                    % (client, team.get_path(), json_data[field])
                )
                return None, None, None, HttpResponseBadRequest(content=TEAM_MESSAGE_NOT_OFFENSIVE)
        if not team.get_game().__bool__():
            General.error(
                '[%s] Client connected and requested Team "%s" that is not currently in a running Game!'
                % (client, team.get_path())
            )
            return HttpResponseBadRequest(content=MESSAGE_GAME_NO_RUNNING)
        return team, json_data, token, None


class Team(Model):
    """
    Team:
        Scorebot Team Base

        Base Python Class Object for all Teams involved in a Game.
        Tied to the Game and can be deleted after the Game is finished or archived.

        Subclasses Must Define:
            save        ()
            __json__    ()
            __score__   ()
            __string__  ()
            __append__  (score object)
    """
    class Meta:
        verbose_name = '[Team] Team'
        verbose_name_plural = '[Team] Teams'

    objects = TeamManager()
    name = CharField('Team Name', max_length=64)
    game = ForeignKey('scorebot_db.Game', related_name='teams', on_delete=CASCADE)
    subclass = PositiveSmallIntegerField('Team SubClass', default=None, null=True, editable=False,
                                         choices=TeamConstants.SUBCLASS)

    def json(self):
        return self.__subclass__().__json__()

    def path(self):
        return '%s\\(%d) %s' % (self.game.name, self.id, self.name)

    def score(self):
        return self.__subclass__().__score__()

    def __str__(self):
        return self.__subclass__().__string__()

    def __len__(self):
        return abs(self.score())

    def __json__(self):
        return None

    def __score__(self):
        return maxsize

    def __string__(self):
        return '[Team] %s' % self.path()

    def __subclass__(self):
        if self.subclass == TeamConstants.TEAM or self.__class__.__name__ == self.get_subclass_display():
            return self
        if self.subclass == TeamConstants.PLAYERTEAM:
            try:
                return self.playerteam
            except AttributeError:
                return self.scoreteam.playerteam
        if self.subclass == TeamConstants.SCORETEAM:
            return self.scoreteam
        return self

    def __lt__(self, other):
        return isinstance(other, Team) and other.score() > self.score()

    def __gt__(self, other):
        return isinstance(other, Team) and other.score() < self.score()

    def __eq__(self, other):
        return isinstance(other, Team) and other.score() == self.score()

    def append(self, score):
        return self.__subclass__().__append__(score)

    def __append__(self, score):
        raise ValidationError('Cannot add a Score Object to a Team base class!')

    def save(self, *args, **kwargs):
        if self.subclass is None:
            self.subclass = TeamConstants.TEAM
        Model.save(self, *args, **kwargs)


class ScoreTeam(Team):
    """
    ScoreTeam:
        Scorebot Scoreable Team Base

        This Python Class reperesents any Team that may have a Score or can gain/lose PTS. Players assigned to this
        Team type cannot Attack or Defend, nor own any Ranges.
    """
    class Meta:
        verbose_name = '[Team] Score Team'
        verbose_name_plural = '[Team] Score Teams'

    objects = TeamManager()
    total = BigIntegerField('Team Total Score', default=0, editable=False)
    token = OneToOneField('scorebot_db.Token', on_delete=SET_NULL, null=True, blank=True)
    stack = OneToOneField('scorebot_db.Transaction', on_delete=SET_NULL, null=True, blank=True, related_name='owner')

    def __score__(self):
        return self.total

    def __string__(self):
        return '[ScoreTeam] %s: %d' % (self.path(), self.total)

    def payed(self, subclass=None):
        if isinstance(subclass, int):
            payments = self.payer.filter(subclass=subclass)
        else:
            payments = self.payer.all()
        total = 0
        for payment in payments:
            total += payment.score()
        del payment
        return total

    def save(self, *args, **kwargs):
        if self.subclass is None:
            self.subclass = TeamConstants.SCORETEAM
        if self.token is None:
            self.token = new('Token', save=True)
        if self.stack is not None:
            self.total = self.stack.total()
        Team.save(self, *args, **kwargs)

    def received(self, subclass=None):
        if isinstance(subclass, int):
            payments = self.receiver.filter(subclass=subclass)
        else:
            payments = self.receiver.all()
        total = 0
        for payment in payments:
            total += payment.score()
        del payments
        return total

    def __append__(self, transaction):
        transaction.previous = self.stack
        transaction.save()
        self.stack = transaction
        self.total += transaction.score()
        self.save()
        transaction.log()
        Events.info('Added a Transaction Type "%s" with value "%d" to Team "%s" from "%s"!' % (
            transaction.name(), transaction.score(), self.path(), transaction.source.path()
        ))


class PlayerTeam(ScoreTeam):
    """
    PlayerTeam:
        Scorebot Player Team Base

        This Python Class reperesents any Team that can own Ranges/Hosts and may Attack or Defend. Players are assigned
        to this type of team.
    """
    class Meta:
        verbose_name = '[Team] Player Team'
        verbose_name_plural = '[Team] Player Teams'

    objects = TeamManager()
    logo = ImageField('Team Logo', null=True, blank=True)
    offensive = BooleanField('Team Can Attack', default=False)
    minimal = BooleanField('Team Score Is Hidden', default=False)
    color = CharField('Team Color', max_length=9, default=hex_color)
    store = PositiveIntegerField('Team Store ID', blank=True, null=True)
    deduction = PositiveSmallIntegerField('Team Score Deduction Percentage', default=0)
    registered = ManyToManyField('scorebot_db.Token', blank=True, related_name='beacon_tokens')
    membership = ForeignKey('scorebot_db.Membership', blank=True, null=True, on_delete=SET_NULL, related_name='teams')

    def __json__(self):
        return {
            'color': self.color, 'name': self.name,
            'mininal': self.minimal, 'score': self.total,
            'offensive': self.offensive, 'logo': self.logo.url if bool(self.logo) else None
        }

    def __string__(self):
        return '[PlayerTeam] %s: %d' % (self.path(), self.total)

    def save(self, *args, **kwargs):
        if self.subclass is None:
            self.subclass = TeamConstants.PLAYERTEAM
        ScoreTeam.save(self, *args, **kwargs)

    def get_scoreboard(self, old=False):
        if old:
            return {
                'id': self.id,
                'name': escape(self.name),
                'color': self.color,
                'offense': self.offensive,
                'flags': {
                    'captured': self.captured.filter(enabled=True).count(),
                    'lost': self.ranges.all()[0].get_flags(True) if self.ranges.all().count() > 0 else 0,
                    'open': self.ranges.all()[0].get_flags(False) if self.ranges.all().count() > 0 else 0
                },
                'tickets': {
                    'open': 0,
                    'closed': 0
                },
                'hosts': [
                    host.get_scoreboard(old) for host in self.ranges.all()[0].hosts.filter(enabled=True)
                ] if self.ranges.all().count() > 0 else [],
                'logo': self.logo.url if bool(self.logo) else TEAM_DEFAULT_LOGO,
                'beacons': [
                    beacon.get_scoreboard(old) for beacon in self.ranges.all()[0].get_beacons()
                ] if self.ranges.all().count() > 0 else [],
                'minimal': self.minimal
            }
        return None

    def register_token(self, days=TeamConstants.DEFAULT_DAYS):
        token = new('Token', save=False)
        if isinstance(days, int) and days > 0:
            token.expires = (now() - timedelta(days=days))
        token.save()
        self.registered.add(token)
        self.save()
        return token

# EOF
