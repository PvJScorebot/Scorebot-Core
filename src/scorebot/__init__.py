#!/usr/bin/false
# Core Scorebot v4 Class Instances
# Allows for static pointers to be implemented and added.
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
from logging import Formatter
from os.path import join, isdir
from os import makedirs, environ

# Version and Information
Name = 'Scorebot'
Version = '4.2-Avacado'

# Models Dictionary
Models = dict()

# Logs
Jobs = None
Events = None
Scoring = None
General = None
Authentication = None

# System Directories
DIRECTORY = join('/var/run/', Name.lower())
if 'sbe-daemon' in environ:
    DIRECTORY_LOG = join(DIRECTORY, 'daemon-logs')
else:
    DIRECTORY_LOG = join(DIRECTORY, 'logs')
DIRECTORY_CACHE = join(DIRECTORY, 'cache')

# Log Defaults and Constants
LOG_PORT = None
LOG_SERVER = None
LOG_LEVEL = 'DEBUG'
LOG_FORMAT = Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')

# Constants
HTTP_GET = 'GET'
HTTP_POST = 'POST'
HTTP_HEADER = 'HTTP_SBE_AUTH'

try:
    if not isdir(DIRECTORY_LOG):
        makedirs(DIRECTORY_LOG)
    if not isdir(DIRECTORY_CACHE):
        makedirs(DIRECTORY_CACHE)
except OSError as err:
    print('FATAL: Could not create Log and Cache Directories (%s, %s)! (%s)' % (
        DIRECTORY_LOG, DIRECTORY_CACHE, str(err)
    ), file=stderr)
    exit(1)

try:
    # Core Log Import to prevent Loop Issues
    from scorebot.log import Log
    # Log Creation
    Jobs = Log('jobs', LOG_LEVEL, DIRECTORY_LOG, LOG_SERVER, LOG_PORT)
    Events = Log('event', LOG_LEVEL, DIRECTORY_LOG, LOG_SERVER, LOG_PORT)
    Scoring = Log('scoring', LOG_LEVEL, DIRECTORY_LOG, LOG_SERVER, LOG_PORT)
    General = Log('general', LOG_LEVEL, DIRECTORY_LOG, LOG_SERVER, LOG_PORT)
    Authentication = Log('auth', LOG_LEVEL, DIRECTORY_LOG, LOG_SERVER, LOG_PORT)
except OSError as err:
    print('FATAL: Could not setup Log objects! (%s)' % str(err), file=stderr)
    exit(1)

General.info('%s version: %s initilization complete!' % (Name, Version))
