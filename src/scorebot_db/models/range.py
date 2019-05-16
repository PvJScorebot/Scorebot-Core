#!/usr/bin/false
#
# Scorebotv4 - The Scorebot Project
# 2018 iDigitalFlame / The Scorebot / CTF Factory Team
#
# Scorebot Team Django Models

from html import escape
from random import choice
from datetime import timedelta
from socket import getservbyport
from scorebot import General, Events
from django.utils.timezone import now
from scorebot.util import new, get, lookup_address
from ipaddress import IPv4Network, IPv4Address
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponseBadRequest, HttpResponseNotFound, HttpResponseForbidden, HttpResponse
from scorebot.constants import SERVICE_PROTOCOLS, SERVICE_STATUS, HOST_VALUE, FLAG_VALUE, \
                               SERVICE_VALUE, CONTENT_VALUE, HOST_MESSAGE_INVALID_IP, \
                               HOST_MESSAGE_NO_HOST, MESSAGE_GAME_NO_RUNNING, HOST_MESSAGE_BEACON_EXISTS, \
                               HOST_IP
from django.db.models import Model, SET_NULL, ForeignKey, ManyToManyField, CASCADE, OneToOneField, BooleanField, \
                             CharField, TextField, PositiveSmallIntegerField, GenericIPAddressField, SlugField, \
                             DateTimeField, Manager, IntegerField


class FlagManager(Manager):
    def get_next(self, team):
        if team.game.__bool__():
            try:
                flags = self.exclude(host__range__team=team).filter(
                    flag__enabled=True, host__enabled=True, host__range__enabled=True, stolen__isnull=True
                )
                if len(flags) > 0:
                    return choice(flags).description
            except IndexError:
                pass
            finally:
                del flags
        return None

    def get_flag(self, team, value):
        if team.game.__bool__():
            try:
                return self.exclude(host__range__team=team).get(
                    flag__enabled=True, host__enabled=True, host__range__enabled=True, flag__exact=value,
                    stolen__isnull=True
                )
            except ObjectDoesNotExist:
                pass
            except MultipleObjectsReturned as err:
                General.error(
                    'Team "%s" submitted Flag value "%s" seems to be in use by multiple Flags, cannot submit!'
                    % (team.path(), value), err
                )
        return None

    def get_flag_query(self, team, flag):
        game = team.get_game()
        if game.__bool__():
            try:
                flag = self.exclude(host__range__team=team).get(
                    host__range__team__game=game, flag__exact=flag, enabled=True, host__enabled=True
                )
            except ObjectDoesNotExist:
                return None
            except MultipleObjectsReturned:
                General.warning(
                    '%s attempted to get Flag "%s", but returned multiple Flags, multiple Flags have the vaue "%s"!'
                    % (team.get_path(), flag, flag)
                )
            else:
                return flag
            finally:
                del game
        return None


class HostManager(Manager):
    def get_beacon(self, team, token, address):
        try:
            target = IPv4Address(address)
        except ValueError:
            General.error('Team "%s" reported a Beacon for an invalid IP address "%s"!' % (team.get_path(), address))
            return HttpResponseBadRequest(content=HOST_MESSAGE_INVALID_IP)
        General.info('Received a Beacon request by Team "%s" for address "%s"!' % (team.get_path(), address))
        host = None
        ghost = False
        try:
            host = self.exclude(range__team=team).get(ip=address)
        except MultipleObjectsReturned:
            General.error('Team "%s" reported a Beacon for an invalid IP address "%s" that matches multiple Hosts!' % (
                team.get_path(), address
            ))
            return HttpResponseBadRequest(content=HOST_MESSAGE_INVALID_IP)
        except ObjectDoesNotExist:
            ghost = True
            try:
                host = get('BeaconHost').objects.exclude(range__team=team).get(ip=address)
            except (ObjectDoesNotExist, MultipleObjectsReturned):
                pass
            if host is None:
                General.info(
                    'Beacon request by Team "%s" for address "%s" does not match a known host, will attempt to match!'
                    % (team.get_path(), address)
                )
                victim = None
                for match in team.get_game().teams.exclude(id=team.id):
                    match_playing = match.get_playingteam()
                    if match_playing is None or match_playing.assets is None:
                        continue
                    try:
                        network = IPv4Network(match_playing.assets.subnet)
                    except ValueError:
                        General.warning('Team "%s" does not have a valid subnet entered for it\'s range "%s"!' % (
                            match.get_path(), match_playing.assets.subnet
                        ))
                        continue
                    else:
                        if target in network:
                            victim = match_playing
                            break
                    finally:
                        del match_playing
                if victim is None:
                    General.error(
                        'Beacon request by Team "%s" for address "%s" does not match a known host or Team subnet range!'
                        % (team.get_path(), address)
                    )
                    return HttpResponseNotFound(content=HOST_MESSAGE_NO_HOST)
                General.debug(
                    'Creating BeaconHost due to Beacon request by Team "%s" for address "%s" that matches Team "%s" '
                    'range!' % (team.get_path(), address, victim.get_path())
                )
                host = new('BeaconHost', False)
                host.ip = address
                host.range = victim.assets
                host.save()
                del victim
        del target
        General.debug('Received Beacon request by Team "%s" for Host "%s"!' % (team.get_path(), host.get_path()))
        if not host.get_game().__bool__():
            General.error('Received Beacon request by Team "%s" for Host "%s" for a non-running Game!' % (
                team.get_path(), host.get_path()
            ))
            return HttpResponseBadRequest(content=MESSAGE_GAME_NO_RUNNING)
        if host.get_game().id != team.get_game().id:
            General.error('Received Beacon request by Team "%s" for Host "%s" not in the same Game!' % (
                team.get_path(), host.get_path()
            ))
            return HttpResponseBadRequest(content=HOST_MESSAGE_NO_HOST)
        try:
            beacon = host.beacons.get(end__isnull=True, owner=team)
        except MultipleObjectsReturned:
            General.warning('Received Beacon request by Team "%s" for Host "%s" attempting to add multiple Beacons!' % (
                team.get_path(), host.get_path()
            ))
            return HttpResponseForbidden(content=HOST_MESSAGE_BEACON_EXISTS)
        except ObjectDoesNotExist:
            Events.info('Created a new Beacon on Host "%s" owned by Team "%s" from "%s"!' % (
                host.get_path(), host.get_team().get_path(), team.get_path()
            ))
            General.info('Created a new Beacon on Host "%s" owned by Team "%s" from "%s"!' % (
                host.get_path(), host.get_team().get_path(), team.get_path()
            ))
            team.get_game().event('%s has compromised a Host on %s\'s network!' % (
                team.get_name(), host.get_team().get_name()
            ))
            beacon = new('Beacon', False)
            beacon.owner = team
            if ghost:
                beacon.ghost = host
            else:
                beacon.host = host
        beacon.update = now()
        beacon.token = token
        beacon.save()
        return HttpResponse(status=201)


class DNS(Model):
    class Meta:
        verbose_name = '[Range] DNS Server'
        verbose_name_plural = '[Range] DNS Servers'

    ip = GenericIPAddressField('DNS Server Address', protocol='both', unpack_ipv4=True)

    def __str__(self):
        return '[DNS] %s' % str(self.ip)


class Flag(Model):
    class Meta:
        verbose_name = '[Range] Flag'
        verbose_name_plural = '[Range] Flags'

    objects = FlagManager()
    name = SlugField('Flag Name', max_length=64)
    flag = CharField('Flag Value', max_length=128)
    enabled = BooleanField('Flag Enabled', default=True)
    description = TextField('Flag Description', null=True, blank=True)
    value = PositiveSmallIntegerField('Flag Score Value', default=FLAG_VALUE)
    host = ForeignKey('scorebot_db.Host', on_delete=CASCADE, related_name='flags')
    stolen = ForeignKey('scorebot_db.PlayerTeam', on_delete=SET_NULL, null=True, blank=True, related_name='captured')

    def path(self):
        return '%s\\(%d) %s' % (self.host.path(), self.id, self.name)

    def game(self):
        return self.host.game()

    def team(self):
        return self.host.team()

    def json(self):
        return {
            'name': self.name, 'flag': self.flag, 'value': self.value, 'enabled': self.enabled,
            'stolen': self.stolen.name if self.stolen is not None else None
        }

    def __str__(self):
        if self.stolen is not None:
            return '[Flag] %s: %d (Stolen: %s)' % (self.path(), self.value, self.stolen.path())
        return '[Flag] %s: %d' % (self.path(), self.value)

    def __bool__(self):
        return self.enabled and self.stolen is None and self.game() is not None and self.game().__bool__()

    def capture(self, team):
        if not self.__bool__():
            General.warning(
                'Team "%s" attempted to capture Flag "%s" which is not enabled!!' % (team.path(), self.path()))
            return None
        if self.stolen is not None:
            General.warning(
                'Team "%s" attempted to capture Flag "%s" owned by "%s" which was already captured by "%s"!'
                % (team.path(), self.path(), self.team().path(), self.stolen.path())
            )
            return None
        self.stolen = team
        result = new('TransactionFlag', save=False)
        result.flag = self
        result.value = self.value
        result.destination = team
        result.source = self.team()
        result.save()
        team.append(result)
        self.team().append(result.reverse())
        self.save()
        del result
        self.game().event('%s stole a Flag from %s!' % (self.stolen.get_name(), self.get_team().get_name()))
        Events.info('Flag "%s" owned by "%s" was captured by "%s"!' % (
            self.path(), self.team().path(), self.stolen.path()
        ))
        return Flag.objects.get_next(team)


class Host(Model):
    class Meta:
        verbose_name = '[Range] Host'
        verbose_name_plural = '[Range] Hosts'

    objects = HostManager()
    enabled = BooleanField('Host Enabled', default=True)
    name = SlugField('Host Nickname', max_length=64, null=True)
    status = BooleanField('Host Online', default=False, editable=False)
    scored = DateTimeField('Host Last Scored', null=True, editable=False)
    fqdn = CharField('Host Full Name', max_length=128, null=True, blank=True)
    value = PositiveSmallIntegerField('Host Score Value', default=HOST_VALUE)
    ip = GenericIPAddressField('Host Address', protocol='both', unpack_ipv4=True)
    range = ForeignKey('scorebot_db.Range', on_delete=CASCADE, related_name='hosts')
    tolerance = PositiveSmallIntegerField('Host Ping Tolerance Percentage', null=True, blank=True)

    def path(self):
        return '%s\\(%d) %s' % (self.range.path(), self.id, self.fqdn)

    def game(self):
        return self.range.game()

    def team(self):
        return self.range.team

    def __str__(self):
        return '[Host] %s (%d, %s, %s)' % (
            self.path(), self.value, str(self.ip), 'Online' if self.status else 'Offline'
        )

    def __bool__(self):
        return self.enabled and self.game() is not None and self.game().__bool__()

    def get_tolerance(self):
        if self.tolerance is not None:
            return self.tolerance
        if self.__bool__():
            try:
                return int(self.game().get_setting('ping_tolerance'))
            except ValueError:
                pass
        return 0

    def json(self, job=False):
        if job:
            return {
                'host': {
                    'fqdn': self.fqdn,
                    'services': [service.json(True) for service in self.services.filter(enabled=True)]
                },
                'dns': [str(dns.ip) for dns in self.range.dns.all()],
                'timeout': int(self.game().get_setting('job_timeout'))
            }
        return {
            'name': self.name, 'fqdn': self.fqdn,
            'value': self.value, 'status': self.status, 'enabled': self.enabled,
            'services': [service.json() for service in self.services.filter(enabled=True)],
            'flags': [flag.json() for flag in self.flags.filter(enabled=True)]
        }

    def save(self, *args, **kwargs):
        if self.ip == HOST_IP and self.fqdn is not None:
            self.ip = lookup_address(self.fqdn)
        if self.name is None and self.fqdn is not None:
            self.name = self.fqdn.split('.')[0]
        if self.fqdn is None and self.name is not None:
            self.fqdn = '%s.%s' % (self.name, self.range.domain)
        if self.name is None and self.fqdn is None:
            self.name = '%s@%s' % (self.ip, self.range.domain)
        Model.save(self, *args, **kwargs)

    def get_scoreboard(self, old=False):
        if old:
            return {
                'id': self.id,
                'name': escape(self.name),
                'online': self.status,
                'services': [{
                    'port': service.port,
                    'bonus': service.bonus,
                    'status': service.get_status_display(),
                    'protocol': service.get_protocol_display()[0]
                } for service in self.services.filter(enabled=True)]
            }
        return None


class Range(Model):
    class Meta:
        verbose_name = '[Range] Range'
        verbose_name_plural = '[Range] Ranges'

    domain = CharField('Range Domain', max_length=64)
    subnet = CharField('Range Subnet', max_length=128)
    enabled = BooleanField('Range Enabled', default=True)
    dns = ManyToManyField('scorebot_db.DNS', related_name='ranges')
    team = ForeignKey('scorebot_db.PlayerTeam', on_delete=SET_NULL, null=True, blank=True, related_name='ranges')

    def path(self):
        if self.team is not None:
            return '%s\\(%d) %s' % (self.team.path(), self.id, self.domain)
        return '(%d) %s' % (self.id, self.domain)

    def game(self):
        if self.team is not None:
            return self.team.game
        return None

    def json(self):
        return {
            'domain': self.domain, 'network': self.subnet,
            'dns': [str(dns.ip) for dns in self.dns.all()], 'enabled': self.enabled,
            'hosts': [host.get_json() for host in self.hosts.all().filter(enabled=True)]
        }

    def __str__(self):
        return '[Range] %s: %d' % (self.path(), self.hosts.filter(enabled=True).count())

    def get_beacons(self):
        beacons = list()
        for host in self.hosts.filter(enabled=True):
            beacons += host.beacons.filter(end__isnull=True)
        return beacons

    def get_flags(self, stolen=False):
        flags = list()
        for host in self.hosts.filter(enabled=True):
            flags += host.flags.filter(enabled=True, stolen__isnull=(not stolen))
        return flags


class Beacon(Model):
    class Meta:
        verbose_name = '[Range] Beacon'
        verbose_name_plural = '[Range] Beacons'

    start = DateTimeField('Beacon Start', auto_now_add=True)
    end = DateTimeField('Beacon Finish', null=True, blank=True)
    update = DateTimeField('Beacon Last Update', null=True, blank=True)
    scored = DateTimeField('Beacon Last Scored', null=True, editable=False)
    token = ForeignKey('scorebot_db.Token', on_delete=CASCADE, related_name='beacons')
    owner = ForeignKey('scorebot_db.PlayerTeam', on_delete=CASCADE, related_name='beacons')
    host = ForeignKey('scorebot_db.Host', on_delete=CASCADE, related_name='beacons', null=True)
    ghost = ForeignKey('scorebot_db.BeaconHost', on_delete=CASCADE, related_name='beacons', null=True, blank=True)

    def path(self):
        return '%s\\(%d) %s' % (self.target(), self.id, self.owner.name)

    def team(self):
        return self.target().team()

    def game(self):
        return self.owner.game

    def target(self):
        if self.ghost is not None:
            return self.ghost
        return self.host

    def update(self):
        if self.end is not None:
            return
        if self.scored is not None:
            last = timedelta(now() - self.scored).seconds
            if last < self.game().get_setting('beacon_score_timeout'):
                return
            del last
        if self.update is not None:
            last = timedelta(now() - self.update).seconds
            if last >= self.game().get_setting('beacon_timeout'):
                Events.info('Beacon by "%s" on Host "%s" has expired after "%d" seconds!' % (
                    self.owner.path(), self.target().path(), self.__len__()
                ))
                self.end = now()
        else:
            Events.info('Beacon by "%s" on Host "%s" has expired after "%d" seconds!' % (
                self.owner.path(), self.target().path(), self.__len__()
            ))
            self.end = now()
        self.scored = now()
        result = new('TransactionBeacon', False)
        result.beacon = self
        result.destination = self.owner
        result.source = self.target().team()
        result.value = int(self.game().get_setting('beacon_score'))
        result.save()
        self.owner.append(result)
        reverse = result.reverse()
        reverse.beacon = self
        reverse.save()
        self.target().team().append(reverse)
        del reverse
        self.save()
        Events.info('Scored a Beacon by "%s" on Host "%s" owned by "%s" for "%d" PTS!' % (
            self.owner.path(), self.target().path(), self.target().path(), result.value
        ))
        del result

    def __str__(self):
        return '[Beacon] %s -> %s (%s seconds)' % (self.owner.path(), self.target().path(), self.__len__())

    def __len__(self):
        if self.update is not None:
            return (self.update - self.start).seconds
        return (now() - self.start).seconds

    def __bool__(self):
        return self.end is None

    def get_scoreboard(self, old=False):
        if old:
            return {
                'team': self.owner.id,
                'color': self.owner.color
            }
        return None


class Service(Model):
    class Meta:
        verbose_name = '[Range] Service'
        verbose_name_plural = '[Range] Services'

    port = IntegerField('Service Port')
    bonus = BooleanField('Service is Bonus', default=False)
    enabled = BooleanField('Service Enabled', default=True)
    name = SlugField('Service Name', max_length=64, null=True)
    value = PositiveSmallIntegerField('Service Score Value', default=SERVICE_VALUE)
    host = ForeignKey('scorebot_db.Host', on_delete=CASCADE, related_name='services')
    bonus_enabled = BooleanField('Service Bonus Enabled', default=False, editable=False)
    application = SlugField('Service Application', max_length=64, null=True, blank=True)
    status = PositiveSmallIntegerField('Service Status', default=0, choices=SERVICE_STATUS)
    content = OneToOneField('scorebot_db.Content', on_delete=SET_NULL, null=True, blank=True)
    protocol = PositiveSmallIntegerField('Service Protocol', default=0, choices=SERVICE_PROTOCOLS)

    def path(self):
        return '%s\\ (%d) %s' % (self.host.path(), self.id, self.name)

    def game(self):
        return self.host.game()

    def team(self):
        return self.host.team()

    def __str__(self):
        return '[Service] %s %d/%s (%d%s) %s' % (
            self.path(), self.get_port(), self.get_protocol_display(), self.value,
            (', %s' % self.application if self.application is not None else ''), self.get_status_display()
        )

    def __bool__(self):
        if self.bonus:
            return self.bonus_enabled and self.enabled
        return self.enabled

    def json(self, job=False):
        if job:
            return {
                'port': self.port,
                'application': self.application,
                'protocol': self.get_protocol_display(),
                'content': self.content.json(True) if self.content is not None else None
            }
        return {
            'name': self.name, 'bonus': self.bonus,
            'value': self.value, 'port': self.port,
            'application': self.application, 'bonus_enabled': self.bonus_enabled,
            'status': self.get_status_display(), 'protocol': self.get_protocol_display(),
            'content': self.content.json() if self.content is not None else None
        }

    def save(self, *args, **kwargs):
        if self.name is None:
            try:
                self.name = getservbyport(self.port)
            except OSError:
                self.name = 'port-%d' % self.port
        Model.save(self, *args, **kwargs)


class Content(Model):
    class Meta:
        verbose_name = '[Range] Service Content'
        verbose_name_plural = '[Range] Service Content'

    format = CharField('Content Format', max_length=64)
    data = TextField('Content Data', null=True, blank=True)
    value = PositiveSmallIntegerField('Content Score Value', default=CONTENT_VALUE)

    def path(self):
        if self.service is None:
            return self.format
        return '%s\\(%d) %s'

    def game(self):
        if self.service is not None:
            return self.service.game()
        return None

    def team(self):
        if self.service is not None:
            return self.service.team()
        return None

    def __str__(self):
        return '[Content] %s (%s/%d)' % (self.path(), self.format, self.value)

    def json(self, job=False):
        if job:
            return {
                'type': self.format, 'content': self.data
            }
        return {
            'value': self.value, 'format': self.format
        }


class BeaconHost(Model):
    class Meta:
        verbose_name = '[Range] Beacon Host'
        verbose_name_plural = '[Range] Beacon Hosts'

    range = ForeignKey('scorebot_db.Range', on_delete=CASCADE, related_name='ghosts')
    ip = GenericIPAddressField('Beacon Host Address', protocol='both', unpack_ipv4=True)

    def path(self):
        return '%s\\(%d) %s' % (self.range.path(), self.id, self.ip)

    def game(self):
        return self.range.game()

    def team(self):
        return self.range.team

    def __str__(self):
        return '[BeaconHost] %s (%s)' % (self.path(), str(self.ip))

# EOF
