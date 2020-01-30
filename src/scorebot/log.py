#!/usr/bin/false
# Log Core Structure Object
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

from sys import stderr, exit
from os.path import join, isdir
from traceback import format_exc
from logging.handlers import SysLogHandler
from scorebot import LOG_FORMAT, Name, Version
from logging import getLogger, FileHandler, StreamHandler


def panic(message, err=None):
    if err is not None:
        print('PANIC: %s, caused by (%s): %s' % (message, str(err), format_exc(limit=4)), file=stderr)
    else:
        print('PANIC: %s' % message, file=stderr)
    exit(1)


class Log(object):
    def __init__(self, name, level, directory=None, server=None, port=None):
        if not isinstance(name, str) or len(name) == 0:
            raise OSError('Parameter "name" must be a non-empty Python string!')
        if not isinstance(level, str) or len(level) == 0:
            raise OSError('Parameter "level" must be a non-empty Python string!')
        self.log = getLogger(name.lower())
        self.log.setLevel(level.upper())
        if isinstance(directory, str):
            if not isdir(directory):
                raise OSError('Parameter "directory" ("%s") must be an existant directory!' % directory)
            else:
                file = FileHandler(join(directory, '%s.log' % name.lower()))
                file.setFormatter(LOG_FORMAT)
                file.setLevel(level.upper())
                self.log.addHandler(file)
                del file
        if isinstance(server, str) and isinstance(port, int):
            syslog = SysLogHandler(address=(server, port))
            syslog.setFormatter(LOG_FORMAT)
            syslog.setLevel(level.upper())
            self.log.addHandler(syslog)
            del syslog
        stream = StreamHandler()
        stream.setFormatter(LOG_FORMAT)
        self.log.addHandler(stream)
        del stream
        self.log.info('[%s: %s] Log "%s" started!' % (Name, Version, name.lower()))

    def info(self, message, err=None):
        if err is not None:
            self.log.info('%s (%s): %s' % (message, str(err), format_exc(limit=4)))
        else:
            self.log.info(message)

    def debug(self, message, err=None):
        if err is not None:
            self.log.debug('%s (%s): %s' % (message, str(err), format_exc(limit=4)))
        else:
            self.log.debug(message)

    def error(self, message, err=None):
        if err is not None:
            self.log.error('%s (%s): %s' % (message, str(err), format_exc(limit=4)))
        else:
            self.log.error(message)

    def warning(self, message, err=None):
        if err is not None:
            self.log.warning('%s (%s): %s' % (message, str(err), format_exc(limit=4)))
        else:
            self.log.warning(message)
