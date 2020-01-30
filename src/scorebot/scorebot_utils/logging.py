#!/usr/bin/false
# Scorebot UDP (Universal Development Platform)
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

from os import makedirs
from traceback import format_exc
from os.path import exists, isdir, dirname
from logging import getLogger, Formatter, StreamHandler, FileHandler


class Logger(object):
    def __init__(self, log_name, log_level="INFO", log_file=None):
        if not isinstance(log_level, str) or len(log_level) == 0:
            raise OSError('Parameter "log_level" must be a non-empty Python str!')
        self._log = getLogger(log_name)
        self._log.setLevel(log_level.upper())
        formatter = Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")
        stream = StreamHandler()
        stream.setFormatter(formatter)
        self._log.addHandler(stream)
        del stream
        if isinstance(log_file, str) and len(log_file) > 0:
            log_dir = dirname(log_file)
            if not isdir(log_dir) or not exists(log_dir):
                try:
                    makedirs(log_dir, exist_ok=True)
                except OSError as err:
                    raise OSError(
                        'Failed to create log file "%s"! (%s)' % (log_file, str(err))
                    )
            del log_dir
            try:
                file = FileHandler(log_file)
                file.setFormatter(formatter)
                file.setLevel(log_level.upper())
                self._log.addHandler(file)
            except OSError as err:
                raise OSError(
                    'Failed to create log file "%s"! (%s)' % (log_file, str(err))
                )
            else:
                del file
        del formatter

    def info(self, message, err=None):
        if err is not None:
            self._log.info("%s (%s): %s" % (message, str(err), format_exc(limit=3)))
        else:
            self._log.info(message)

    def debug(self, message, err=None):
        if err is not None:
            self._log.debug("%s (%s): %s" % (message, str(err), format_exc(limit=3)))
        else:
            self._log.debug(message)

    def error(self, message, err=None):
        if err is not None:
            self._log.error("%s (%s): %s" % (message, str(err), format_exc(limit=3)))
        else:
            self._log.error(message)

    def warning(self, message, err=None):
        if err is not None:
            self._log.warning("%s (%s): %s" % (message, str(err), format_exc(limit=3)))
        else:
            self._log.warning(message)
