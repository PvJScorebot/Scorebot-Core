#!/usr/bin/false
# Scorebot Team Django Models
# Scorebot v4 - The Scorebot Project
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


from scorebot import Name, Version
from scorebot.constants import MonitorMessage, GenericMessage


from math import floor
from html import escape
from random import choice
from scorebot.util import new, get, ScorebotResponse
from django.utils.timezone import now
from json import loads, JSONDecodeError
from scorebot import Events, General, Jobs, Authentication
from django.core.exceptions import ObjectDoesNotExist, MultipleObjectsReturned
from django.http import HttpResponseBadRequest, HttpResponse, JsonResponse
from scorebot.constants import GAME_MODES, GAME_STATUS, GAME_SETTINGS, GAME_RUNNING, MESSAGE_INVALID_ENCODING, \
                               MESSAGE_INVALID_FORMAT, JOB_MESSAGE_INVALID_JOB, MESSAGE_INVALID_METHOD, \
                               SERVICE_STATUS_LOOKUP, JOB_MESSAGE_PASSED, TEAM_MESSAGE_PORT_INVALID, \
                               TEAM_MESSAGE_PORT, TEAM_SUBCLASS_TEAM, TEAM_SUBCLASS_SCORETEAM, \
                               TEAM_SUBCLASS_PLAYERTEAM, GAME_GRAYTEAM_NAME, GAME_GOLDTEAM_NAME
from django.db.models import Model, Manager, SET_NULL, ForeignKey, ManyToManyField, CASCADE, OneToOneField, \
                             CharField, PositiveIntegerField, BooleanField, PositiveSmallIntegerField, DateTimeField, \
                             SlugField, TextField


class JobManager(Manager):
    def new_job(self, monitor):
        if not monitor.game.__bool__():
            return None
        teams = monitor.game.teams.filter(subclass=TEAM_SUBCLASS_PLAYERTEAM)
        print(teams)
        for team_num in range(0, len(teams)):
            team = choice(teams).__subclass__()
            ranges = team.ranges.filter(enabled=True)
            print(ranges)
            if team is None or len(ranges) == 0:
                continue
            Jobs.info('AssignedMonitor "%s": Selected Team "%s" for inspection.' % (
                monitor.name(), team.path()
            ))
            hosts = ranges[0].hosts.filter(enabled=True, scored__isnull=True)
            if len(hosts) == 0:
                Jobs.debug('AssignedMonitor "%s": Team "%s" has no valid hosts, skipping!' % (
                    monitor.name(), team.path()
                ))
                continue
            Jobs.debug('AssignedMonitor "%s": Team "%s" has "%d" valid hosts, beginning selection!' % (
                monitor.name(), team.path(), len(hosts)
            ))
            for host_num in range(len(hosts)):
                host = choice(hosts)
                if host.jobs.filter(end__isnull=True).count() > 0:
                    Jobs.debug('AssignedMonitor "%s": Skipping Host "%s" with open Jobs!' % (
                        monitor.name(), host.path()
                    ))
                    continue
                if monitor.selected.all().count() > 0 or not monitor.exclude:
                    Job.debug('AssignedMonitor "%s": Has selection rules in place!' % (monitor.name()))
                    host_selected = monitor.selected.filter(id=host.id).count()
                    if host_selected > 0:
                        if monitor.exclude:
                            Jobs.debug('AssignedMonitor "%s": Skipping Host "%s" as it is excluded!' % (
                                monitor.name(), host.path()
                            ))
                            continue
                    if not monitor.exclude and host_selected == 0:
                        Jobs.debug('AssignedMonitor "%s": Skipping Host "%s" as it is not included!' % (
                            monitor.name(), host.path()
                        ))
                        continue
                    del host_selected
                Jobs.info('AssignedMonitor "%s": Selected Host "%s"!' % (monitor.name(), host.path()))
                job = new('Job', False)
                job.monitor = monitor
                job.host = host
                job.save()
                return job
        return None

    def get_job(self, monitor, request):
        Jobs.info('AssignedMonitor "%s": Attempting to submit a Job!' % monitor.name)
        try:
            job_str = request.body.decode('UTF-8')
        except UnicodeDecodeError:
            Jobs.error('AssignedMonitor "%s": Attempted to submit a Job with an invaid encoding scheme!' % (
                monitor.name
            ))
            return HttpResponseBadRequest(content=MESSAGE_INVALID_ENCODING)
        else:
            try:
                job_json = loads(job_str)
                if not isinstance(job_json, dict) or 'id' not in job_json or 'host' not in job_json:
                    Jobs.error('AssignedMonitor "%s": Attempted to submit a Job with an invaid JSON format!' % (
                        monitor.name
                    ))
                    return HttpResponseBadRequest(content=MESSAGE_INVALID_FORMAT)
                try:
                    job = self.get(id=int(job_json['id']))
                    if job.end is not None:
                        Jobs.error('AssignedMonitor "%s": Attempted to submit a Job that was already completed!' % (
                            monitor.name
                        ))
                        return HttpResponseBadRequest(content=JOB_MESSAGE_INVALID_JOB)
                    Jobs.error('AssignedMonitor "%s": Submitted Job "%d" for processing.' % (monitor.name, job.id))
                    General.debug('AssignedMonitor "%s": Submitted Job "%d" for processing.' % (monitor.name, job.id))
                    return job.process_job(monitor, job_json['host'])
                except (KeyError, TypeError, ValueError, ObjectDoesNotExist, MultipleObjectsReturned) as err:
                    Jobs.error('AssignedMonitor "%s": Attempted to submit a Job that does not exist or invalid! %s' % (
                        monitor, str(err)
                    ), err)
                    return HttpResponseBadRequest(content=JOB_MESSAGE_INVALID_JOB)
                finally:
                    del job
                    del job_json
            except JSONDecodeError:
                Jobs.error('AssignedMonitor "%s": Attempted to submit a Job with an invaid JSON format!' % (
                    monitor.get_name()
                ))
                return HttpResponseBadRequest(content=MESSAGE_INVALID_FORMAT)
            finally:
                del job_str
        return HttpResponseBadRequest(content=MESSAGE_INVALID_METHOD)


class PortManager(Manager):
    def get_list(self):
        ports = list()
        for game in get('Game').objects.filter(status=GAME_RUNNING):
            for port in game.ports.all():
                ports.append(str(port.port))
        return ports

    def get_port(self, team, port):
        try:
            number = int(port)
            if number <= 0:
                raise ValueError()
        except ValueError:
            General.error('Team "%s" attempted to open port "%s" which is not a valid integer!' % (
                team.get_path(), str(port)
            ))
            return HttpResponseBadRequest(content=TEAM_MESSAGE_PORT_INVALID)
        try:
            self.get(port=number)
        except (ObjectDoesNotExist, MultipleObjectsReturned):
            pass
        else:
            return HttpResponse(status=418)
        openport = new('Port', False)
        openport.port = number
        openport.save()
        team.game.ports.add(openport)
        team.game.save()
        General.info('Team "%s" attempted to opened Beacon Port "%d"!' % (team.get_path(), number))
        del openport
        return HttpResponse(status=201, content=TEAM_MESSAGE_PORT.format(port=port))


class MonitorManager(Manager):
    def create_job(self, request):
        try:
            monitor = self.get(token=request.token)
        except ObjectDoesNotExist:
            Authentication.error(
                '[%s: %s] Attempted to access the jobs interface without being assigned a Monitor Token!'
                % (request.ip, str(request.token.uid))
            )
            return ScorebotResponse(status=403, message=MonitorMessage.NOT_MONTIOR)
        except MultipleObjectsReturned:
            Authentication.error('[%s: %s] Attempted to access the jobs interface with an improper Monitor Token!' % (
                request.ip, str(request.token.uid)
            ))
            return ScorebotResponse(status=403, message=MonitorMessage.NO_MONTIOR)
        games = monitor.assigned.filter(game__status=GAME_RUNNING)
        if len(games) == 0:
            Job.error('[%s: %s] %s: Monitor was not assigned to any running Games!' % (
                request.ip, str(request.token.uid), monitor.name
            ))
            return ScorebotResponse(status=403, message=MonitorMessage.NO_GAMES)
        Authentication.info('[%s: %s] %s: Monitor connected to request a Job.' % (
            request.ip, str(request.token.uid), monitor.name, len(games)
        ))
        Job.debug('[%s: %s] %s: Monitor connected to request a Job, assigned to "%d" running Games.' % (
            request.ip, str(request.token.uid), monitor.name, len(games)
        ))
        job = None
        for x in range(0, len(games)):
            game = choice(games)
            Job.debug('[%s: %s] %s: Game selection round "%d" selected Game "%s" for inspection.' % (
                request.ip, str(request.token.uid), monitor.name, x, game.name
            ))
            ranges = get('Range').objects.filter(
                enabled=True, team__subclass=TEAM_SUBCLASS_PLAYERTEAM, team__game=game.game
            )
            if len(ranges) == 0:
                Jobs.debug('[%s: %s] %s: Game "%s" has no valid or enabled Ranges, skipping!' % (
                    request.ip, str(request.token.uid), monitor.name, game.game.name
                ))
                continue
            for y in range(0, len(ranges)):
                network = choice(ranges)
                Job.debug('[%s: %s] %s: Range selection round "%d" selected Range "%s" for inspection.' % (
                    request.ip, str(request.token.uid), monitor.name, x, network.path()
                ))
                hosts = network.hosts.filter(enabled=True, scored__isnull=True)
                if len(hosts) == 0:
                    Jobs.debug('[%s: %s] %s: Range "%s" has no valid or enabled Hosts, skipping!' % (
                        request.ip, str(request.token.uid), monitor.name, network.path()
                    ))
                for z in range(0, len(hosts)):
                    host = choice(hosts)
                    if host.jobs.filter(end__isnull=True).count() > 0:
                        Jobs.debug('[%s: %s] %s: Skipping Host "%s" as it has open Jobs!' % (
                            request.ip, str(request.token.uid), monitor.name, host.path()
                        ))
                        continue
                    if game.selected.count() > 0 or not game.exclude:
                        selected = monitor.selected.filter(id=host.id).count()
                        if selected > 0:
                            if monitor.exclude:
                                Jobs.debug('[%s: %s] %s: Skipping Host "%s" as it selected as ecluded!' % (
                                    request.ip, str(request.token.uid), monitor.name, host.path()
                                ))
                                continue
                        if not monitor.exclude and selected == 0:
                            Jobs.debug('[%s: %s] %s: Skipping Host "%s" as it not included!' % (
                                request.ip, str(request.token.uid), monitor.name, host.path()
                            ))
                            continue
                        del selected
                    Jobs.info('[%s: %s] %s: Selected Host "%s" for checking!' % (
                            request.ip, str(request.token.uid), monitor.name, host.path()
                    ))
                    job = new('Job', False)
                    job.host = host
                    job.monitor = monitor
                    job.save()
                    break
        if job is None:
            Job.debug('[%s: %s] %s: No current valid hosts to choose from!' % (
                request.ip, str(request.token.uid), monitor.name, len(games)
            ))
            return ScorebotResponse(status=204, message=MonitorMessage.NO_HOSTS)
        return JsonResponse(status=201, data=job.json())

    def complete_job(self, request):
        try:
            monitor = self.get(token=request.token)
        except ObjectDoesNotExist:
            Authentication.error(
                '[%s: %s] Attempted to access the jobs interface without being assigned a Monitor Token!'
                % (request.ip, str(request.token.uid))
            )
            return ScorebotResponse(status=403, message=MonitorMessage.NOT_MONTIOR)
        except MultipleObjectsReturned:
            Authentication.error('[%s: %s] Attempted to access the jobs interface with an improper Monitor Token!' % (
                request.ip, str(request.token.uid)
            ))
            return ScorebotResponse(status=403, message=MonitorMessage.NO_MONTIOR)
        Job.debug('[%s: %s] Attempting to submit a Job!' % (request.ip, str(request.token.uid)))
        try:
            if not isinstance(request.json, dict):
                Job.warning('[%s: %s] %s: Attempted to submit invalid JSON data!' % (
                    request.ip, str(request.auth.token.uid), monitor.name
                ))
                return ScorebotResponse(status=400, message=GenericMessage.FORMAT)
        except AttributeError:
            Job.warning('[%s: %s] %s: Attempted to submit invalid JSON data!' % (
                request.ip, str(request.auth.token.uid), monitor.name
            ))
            return ScorebotResponse(status=400, message=GenericMessage.FORMAT)
        try:
            job = get('Job').objects.get(
                end__isnull=True, monitor__monitor=monitor, host__enabled=True, monitor__game__status=GAME_RUNNING,
                id=int(request.json['id'])
            )
        except ObjectDoesNotExist:
            Job.error('[%s: %s] %s: Attempted to submit a non-existant Job!' % (
                request.ip, str(request.auth.token.uid), monitor.name
            ))
            return ScorebotResponse(status=404, message=MonitorMessage.NOT_EXIST)
        except (ValueError, MultipleObjectsReturned):
            Job.error('[%s: %s] %s: Attempted to submit invalid JSON data!' % (
                request.ip, str(request.auth.token.uid), monitor.name
            ))
            return ScorebotResponse(status=400, message=GenericMessage.FORMAT)


class Job(Model):
    class Meta:
        verbose_name = '[Game] Job'
        verbose_name_plural = '[Game] Jobs'

    objects = JobManager()
    start = DateTimeField('Job Start', auto_now_add=True)
    end = DateTimeField('Job Finish', null=True, blank=True)
    host = ForeignKey('scorebot_db.Host', on_delete=CASCADE, related_name='jobs')
    monitor = ForeignKey('scorebot_db.AssignedMonitor', on_delete=CASCADE, related_name='jobs')

    def json(self):
        return {
            'id': self.id, 'host': self.host.__job__(), 'engine': '%s %s' % (Name, Version)
        }

    def __str__(self):
        if self.end is not None:
            return '[Job] %s: %s (%s - %s)' % (
                self.monitor.name, self.host.path(), self.start.strftime('%m/%d/%y %H:%M'),
                self.end.strftime('%m/%d/%y %H:%M')
            )
        return '[Job] %s: %s (%s - %d seconds)' % (
            self.monitor.name, self.host.path(), self.start.strftime('%m/%d/%y %H:%M'),
            self.__len__()
        )

    def __len__(self):
        if self.end is not None:
            return (self.end - self.start).seconds
        return (now() - self.start).seconds

    def __bool__(self):
        return self.end is not None

    def score_job(self, total):
        Jobs.info('Job "%d": Finished Scoring for Host "%s"!' % (self.id, self.host.path()))
        transaction = new('Payment', False)
        transaction.value = total
        transaction.target = self.host.team()
        transaction.source = transaction.target.game.goldteam()
        transaction.destination = transaction.target.game.grayteam()
        transaction.save()
        transaction.destination.append(transaction)
        transaction.process()
        self.end = now()
        self.save()
        return HttpResponse(status=202, content=JOB_MESSAGE_PASSED)

    def process_job(self, monitor, data):
        if monitor.id != self.monitor.id:
            Jobs.error('AssignedMonitor "%s": Attempted to submit a Job owned by another Monitor "%s"!' % (
                monitor.name, self.monitor.name()
            ))
            return HttpResponseBadRequest(content=JOB_MESSAGE_INVALID_JOB)
        Jobs.debug('Job "%d": Starting scoring on Host "%s".' % (
            self.id, self.host.path()
        ))
        try:
            sent = int(data['ping_sent'])
            response = int(data['ping_respond'])
        except (ValueError, KeyError):
            Jobs.error('AssignedMonitor "%s": Attempted to submit a Job "%d" with invalid JSON integers!' % (
                monitor.name, self.id
            ))
            return HttpResponseBadRequest(content=JOB_MESSAGE_INVALID_JOB)
        tolerance = self.host.get_tolerance()
        try:
            ratio = floor(float(response / sent) * 100)
        except ZeroDivisionError:
            Jobs.error('AssignedMonitor "%s": Attempted to submit a Job "%d" with invalid JSON values!' % (
                monitor.name, self.id
            ))
            return HttpResponseBadRequest(content=JOB_MESSAGE_INVALID_JOB)
        Jobs.debug('Job "%d": Host "%s" was sent "%d" pings and responded to "%d" (%d%%), tolerance is %d%%.' % (
            self.id, self.host.path(), sent, response, ratio, tolerance
        ))
        total = 0
        self.host.status = (ratio >= tolerance)
        if 'ip_address' in data:
            self.host.ip = str(data['ip_address'])
        if self.host.status:
            total += self.host.value
        self.host.scored = now()
        self.host.save()
        del sent
        del ratio
        del response
        del tolerance
        Jobs.info('Job "%d": Set Host "%s" status to "%s"!' % (
            self.id, self.host.path(), 'Online' if self.host.status else 'Offline'
        ))
        if 'services' not in data and self.host.status:
            Jobs.warning('Job "%d": Set Host "%s" status, but is missing Service values!' % (
                self.id, self.host.path()
            ))
            return self.score_job(total)
        for service in self.host.services.filter(enabled=True):
            for job_service in data['services']:
                if 'status' not in job_service:
                    Jobs.warning('Job "%d": Attempted to set Service status for "%s" without any data!' % (
                        self.id, service.path()
                    ))
                    continue
                if self.host.status:
                    status = SERVICE_STATUS_LOOKUP.get(job_service['status'].lower(), 2)
                else:
                    status = 2
                if service.port == int(job_service['port']):
                    Jobs.debug('Job "%d": Starting scoring on Services "%s".' % (self.id, service.path()))
                    service.status = status
                    if service.bonus:
                        if not service.bonus_enabled and status == 0:
                            Jobs.debug('Job "%d": Enabled Bonus Service "%s"!.' % (self.id, service.path()))
                            service.bonus_enabled = True
                        if service.bonus_enabled:
                            total += service.value
                    elif status == 0:
                        total += service.value
                    content = service.content
                    if content is not None:
                        if 'content' in job_service and 'status' in job_service['content']:
                            try:
                                content_status = int(job_service['content']['status'])
                                if content_status > 0:
                                    content_value = floor(float(content_status/100))
                                    Jobs.debug('Job "%d": Set Service "%s" Content status to 0%%!' % (
                                        self.id, service.path(), content_value
                                    ))
                                    total += content.value * content_value
                                    del content_value
                                else:
                                    Jobs.debug('Job "%d": Set Service "%s" Content status to "Incorrect" (0%%)!' % (
                                        self.id, service.path()
                                    ))
                                del content_status
                            except (ValueError, ZeroDivisionError):
                                Jobs.error('Job "%d": Service Content status for "%s" is invalid!' % (
                                    self.id, service.path()
                                ))
                        else:
                            Jobs.warning('Job "%d": Ignored Service Content for "%s"!' % (self.id, service.path()))
                        del content
                    Jobs.debug('Job "%d": Set Service "%s" status to "%s".' % (
                        self.id, service.path(), service.get_status_display()
                    ))
                    service.save()
        return self.score_job(total)


class Game(Model):
    class Meta:
        verbose_name = '[Game] Game'
        verbose_name_plural = '[Game] Games'

    name = CharField('Game Name', max_length=64)
    start = DateTimeField('Game Start', null=True)
    ports = ManyToManyField('scorebot_db.Port', blank=True)
    end = DateTimeField('Game Finish', null=True, blank=True)
    mode = PositiveIntegerField('Game Mode', default=0, choices=GAME_MODES)
    status = PositiveIntegerField('Game Status', default=0, choices=GAME_STATUS)
    settings = ForeignKey('scorebot_db.Settings', on_delete=SET_NULL, null=True, blank=True, related_name='games')

    def path(self):
        return self.name

    def json(self):
        return {
            'name': self.name, 'mode': self.get_mode_display(),
            'status': self.get_status_display(),
            'end': (self.end.isoformat() if self.end is not None else None),
            'start': (self.start.isoformat() if self.start is not None else None),
            'teams': [team.json() for team in get('PlayerTeam').objects.filter(game=self)]
        }

    def __str__(self):
        if self.start is not None and self.end is not None:
            return '[Game] %s (%s - %s) %s - %s, Teams: %d' % (
                self.name, self.get_mode_display(), self.get_status_display(), self.start.strftime('%m/%d/%y %H:%M'),
                self.end.strftime('%m/%d/%y %H:%M'), self.teams.count()
            )
        elif self.start is not None:
            return '[Game] %s (%s - %s) %s, Teams: %d' % (
                self.name, self.get_mode_display(), self.get_status_display(), self.start.strftime('%m/%d/%y %H:%M'),
                self.teams.count()
            )
        return '[Game] %s (%s - %s) Teams: %d' % (
            self.name, self.get_mode_display(), self.get_status_display(),  self.teams.count()
        )

    def __len__(self):
        if self.start is not None and self.end is not None:
            return (self.end - self.start).seconds
        elif self.start is not None:
            return (now() - self.start).seconds
        return 0

    def __bool__(self):
        return self.status == GAME_RUNNING and self.start is not None

    def goldteam(self):
        goldteam = self.teams.filter(subclass=TEAM_SUBCLASS_TEAM).first()
        if goldteam is None:
            goldteam = new('Team', save=False)
            goldteam.game = self
            goldteam.name = GAME_GOLDTEAM_NAME
            goldteam.save()
        return goldteam

    def grayteam(self):
        grayteam = self.teams.filter(subclass=TEAM_SUBCLASS_SCORETEAM).first()
        if grayteam is None:
            grayteam = new('ScoreTeam', save=False)
            grayteam.game = self
            grayteam.name = GAME_GRAYTEAM_NAME
            grayteam.save()
        return grayteam

    def get_team_list(self):
        teams = get('ScoringTeam').objects.filter(game=self)
        return {
            'id': self.id,
            'name': self.name,
            'teams': [{
                    'id': team.id,
                    'name': team.name,
                    'token': str(team.token.uid)
                } for team in teams]
        }

    def ranges(self, monitor):
        pass

    def event(self, message):
        Events.debug('Event occured "%s".' % message)

    def get_setting(self, name):
        General.error('Setting: "%s" requested!' % name)
        if self.settings is not None:
            try:
                return getattr(self.settings, name)
            except AttributeError:
                pass
        return GAME_SETTINGS.get(name, None)

    def save(self, *args, **kwargs):
        Model.save(self, *args, **kwargs)
        if self.goldteam() is None:
            goldteam = new('Team', save=False)
            goldteam.game = self
            goldteam.name = 'Gold Team'
            goldteam.save()
            Model.save(self, *args, **kwargs)
        if self.grayteam() is None:
            grayteam = new('ScoreTeam', save=False)
            grayteam.game = self
            grayteam.name = 'Gray Team'
            grayteam.save()
            Model.save(self, *args, **kwargs)

    def get_scoreboard(self, old=False):
        if old:
            return {
                'name': escape(self.name),
                'message': 'This is Scorebot',
                'mode': self.mode,
                'teams': [team.get_scoreboard(old) for team in get('PlayerTeam').objects.filter(game=self)],
                'events': [],
                'credit': ''
            }
        return None


class Port(Model):
    class Meta:
        verbose_name = '[Game] Beacon Port'
        verbose_name_plural = '[Game] Beacon Ports'

    objects = PortManager()
    port = PositiveIntegerField('Beacon Port')

    def __str__(self):
        return '[Port] %d' % self.port


class Credit(Model):
    class Meta:
        verbose_name = '[Game] Credit'
        verbose_name_plural = '[Game] Credits'

    name = SlugField('Credit Name', max_length=75)
    content = TextField('Credit HTML Code', blank=True, null=True)

    def __str__(self):
        return '[Credit] %s' % self.name


class Monitor(Model):
    class Meta:
        verbose_name = '[Game] Monitor'
        verbose_name_plural = '[Game] Monitors'

    objects = MonitorManager()
    name = SlugField('Monitor Name', max_length=75)
    token = OneToOneField('scorebot_db.Authorization', on_delete=SET_NULL, null=True, blank=True)

    def __str__(self):
        return '[Monitor] %s' % self.name

    def save(self, *args, **kwargs):
        if self.token is None:
            self.token = new('Token', save=True)
        if not self.token['__SYS_MONITOR']:
            self.token['__SYS_MONITOR'] = True
        Model.save(self, *args, **kwargs)


class Settings(Model):
    class Meta:
        verbose_name = '[Game] Game Settings'
        verbose_name_plural = '[Game] Game Settings'

    name = SlugField('Settings Name', max_length=150)
    beacon_score = PositiveSmallIntegerField('Beacon Scoring Value', default=300)
    beacon_time = PositiveSmallIntegerField('Beacon Timeout (seconds)', default=300)
    job_timeout = PositiveSmallIntegerField('Unfinished Job Timeout (seconds)', default=300)
    host_ping = PositiveSmallIntegerField('General Host Ping Tolerance Percentage', default=100)
    job_cleanup_time = PositiveSmallIntegerField('Finished Job Cleanup Time (seconds)', default=900)

    def __str__(self):
        return '[Settings] %s' % self.name


class AssignedMonitor(Model):
    class Meta:
        verbose_name = '[Game] Assigned Monitor'
        verbose_name_plural = '[Game] Assigned Monitors'

    exclude = BooleanField('Monitor Exclude', default=True)
    selected = ManyToManyField('scorebot_db.Host', blank=True)
    game = ForeignKey('scorebot_db.Game', on_delete=CASCADE, related_name='monitors')
    monitor = ForeignKey('scorebot_db.Monitor', on_delete=CASCADE, related_name='assigned')

    def __str__(self):
        return '[AssignedMonitor] %s: %s' % (self.game.name, self.monitor.name)
