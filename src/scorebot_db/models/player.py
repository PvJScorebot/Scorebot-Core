#!/usr/bin/false
#
# Scorebotv4 - The Scorebot Project
# 2018 iDigitalFlame / The Scorebot / CTF Factory Team
#
# Scorebot Player Django Models

from scorebot.util import new, hex_color
from django.contrib.auth.models import User
from django.db.models import Model, SET_NULL, ForeignKey, CASCADE, OneToOneField, CharField, ImageField, IntegerField, \
                             BigIntegerField


class Player(Model):
    class Meta:
        verbose_name = '[Player] Player'
        verbose_name_plural = '[Player] Players'

    name = CharField('Player Name', max_length=64, unique=True)
    score = IntegerField('Player Score', default=0, editable=False)
    user = OneToOneField(User, null=True, blank=True, on_delete=SET_NULL)
    team = ForeignKey('scorebot_db.Team', on_delete=CASCADE, related_name='players')
    token = OneToOneField('scorebot_db.Token', on_delete=SET_NULL, null=True, blank=True)
    member = ForeignKey('scorebot_db.Member', null=True, blank=True, on_delete=SET_NULL, related_name='players')

    def __str__(self):
        return '[Player] %s: %d' % (self.get_path(), self.get_score())

    def __json__(self):
        return {
            'name': self.name,
            'score': self.score
        }

    def get_path(self):
        return '%s\\%s' % (self.game.get_name(), self.get_name())

    def get_game(self):
        return self.team.game

    def get_team(self):
        return self.team

    def get_name(self):
        return self.name

    def get_score(self):
        return self.score

    def __lt__(self, other):
        return isinstance(other, Player) and other.get_score() > self.get_score()

    def __gt__(self, other):
        return isinstance(other, Player) and other.get_score() < self.get_score()

    def __eq__(self, other):
        return isinstance(other, Player) and other.get_score() == self.get_score()

    def save(self, *args, **kwargs):
        if self.token is None:
            self.token = new('Token')
        Model.save(self, *args, **kwargs)


class Member(Model):
    class Meta:
        verbose_name = '[Player] Member'
        verbose_name_plural = '[Player] Members'

    name = CharField('Member Name', max_length=64, unique=True)
    score = BigIntegerField('Member Lifetime Score', default=0)
    user = OneToOneField(User, null=True, blank=True, on_delete=SET_NULL)
    handle = CharField('Member Twitter Handle', max_length=64, null=True, blank=True)
    membership = ForeignKey('scorebot_db.Membership', related_name='members', null=True, blank=True, on_delete=SET_NULL)

    def __str__(self):
        if self.handle is None:
            return '[Member] %s (Lifetime %d)' % (self.name, self.score)
        return '[Member] %s <@%s> (Lifetime %d)' % (self.name, self.handle, self.score)

    def __json__(self):
        return {
            'name': self.name,
            'score': self.score,
            'handle': self.handle
        }

    def get_name(self):
        return self.name

    def get_score(self):
        return self.score

    def create_player(self):
        player = new('Player', False)
        player.name = self.name
        player.user = self.user
        player.member = self
        player.save()
        return player

    def __lt__(self, other):
        return isinstance(other, Member) and other.get_score() > self.get_score()

    def __gt__(self, other):
        return isinstance(other, Member) and other.get_score() < self.get_score()

    def __eq__(self, other):
        return isinstance(other, Member) and other.get_score() == self.get_score()


class Membership(Model):
    class Meta:
        verbose_name = '[Player] Membership'
        verbose_name_plural = '[Player] Memberships'

    name = CharField('Membership Name', max_length=64)
    logo = ImageField('Membership Logo', null=True, blank=True)
    score = BigIntegerField('Membership Lifetime Score', default=0)
    color = CharField('Membership Color', max_length=9, default=hex_color())

    def __str__(self):
        return '[Membership] %s (Lifetime %d)' % (self.name, self.score)

    def __json__(self):
        return {
            'name': self.name,
            'score': self.score,
            'color': self.color,
            'logo': self.logo.url if self.logo is not None else ''
        }

    def get_name(self):
        return self.name

    def get_score(self):
        return self.score

    def create_team(self):
        team = new('PlayingTeam', False)
        team.name = self.name
        team.logo = self.logo
        team.color = self.color
        team.membership = self
        team.save()
        return team

    def __lt__(self, other):
        return isinstance(other, Membership) and other.get_score() > self.get_score()

    def __gt__(self, other):
        return isinstance(other, Membership) and other.get_score() < self.get_score()

    def __eq__(self, other):
        return isinstance(other, Membership) and other.get_score() == self.get_score()

# EOF
