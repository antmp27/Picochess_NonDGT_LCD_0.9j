# Copyright (C) 2013-2017 Jean-Francois Romang (jromang@posteo.de)
#                         Shivkumar Shivaji ()
#                         Jürgen Précour (LocutusOfPenguin@posteo.de)
#
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program. If not, see <http://www.gnu.org/licenses/>.

import logging
import os
import configparser
import spur
import paramiko

from subprocess import DEVNULL
from dgt.api import Event
from utilities import Observable
import chess.uci
from chess import Board
from uci.informer import Informer


class UciEngine(object):

    """Handle the uci engine communication."""

    def __init__(self, file: str, hostname=None, username=None, key_file=None, password=None, home=''):
        super(UciEngine, self).__init__()
        try:
            self.shell = None
            if hostname:
                logging.info('connecting to [%s]', hostname)
                if key_file:
                    shell = spur.SshShell(hostname=hostname, username=username, private_key_file=key_file,
                                          missing_host_key=paramiko.AutoAddPolicy())
                else:
                    shell = spur.SshShell(hostname=hostname, username=username, password=password,
                                          missing_host_key=paramiko.AutoAddPolicy())
                self.shell = shell
                self.engine = chess.uci.spur_spawn_engine(shell, [home + os.sep + file])
            else:
                self.engine = chess.uci.popen_engine(file, stderr=DEVNULL)

            self.file = file
            if self.engine:
                handler = Informer()
                self.engine.info_handlers.append(handler)
                self.engine.uci()
            else:
                logging.error('engine executable [%s] not found', file)
            self.options = {}
            self.future = None
            self.show_best = True

            self.res = None
            self.level_support = False

        except OSError:
            logging.exception('OS error in starting engine')
        except TypeError:
            logging.exception('engine executable not found')

    def get_name(self):
        """Get engine name."""
        return self.engine.name

    def get_options(self):
        """Get engine options."""
        return self.engine.options

    def option(self, name, value):
        """Set OptionName with value."""
        self.options[name] = value

    def send(self):
        """Send options to engine."""
        self.engine.setoption(self.options)

    def level(self, options: dict):
        """Set options."""
        self.options = options

    def has_levels(self):
        """Return engine level support."""
        has_lv = self.has_skill_level() or self.has_handicap_level() or self.has_limit_strength() or self.has_strength()
        return self.level_support or has_lv

    def has_skill_level(self):
        """Return engine skill level support."""
        return 'Skill Level' in self.engine.options

    def has_handicap_level(self):
        """Return engine handicap level support."""
        return 'Handicap Level' in self.engine.options

    def has_limit_strength(self):
        """Return engine limit strength support."""
        return 'UCI_LimitStrength' in self.engine.options

    def has_strength(self):
        """Return engine strength support."""
        return 'Strength' in self.engine.options

    def has_chess960(self):
        """Return chess960 support."""
        return 'UCI_Chess960' in self.engine.options

    def has_ponder(self):
        """Return ponder support."""
        return 'Ponder' in self.engine.options

    def get_file(self):
        """Get File."""
        return self.file

    def get_shell(self):
        """Get Shell."""
        return self.shell  # shell is only "not none" if its a local engine - see __init__

    def position(self, game: Board):
        """Set position."""
        self.engine.position(game)

    def quit(self):
        """Quit engine."""
        if self.engine.quit():  # Ask nicely
            if self.engine.terminate():  # If you won't go nicely....
                if self.engine.kill():  # Right that does it!
                    return False
        return True

    def uci(self):
        """Send start uci command."""
        self.engine.uci()

    def stop(self, show_best=False):
        """Stop engine."""
        logging.info('show_best old: %s new: %s', self.show_best, show_best)
        self.show_best = show_best
        if self.is_waiting():
            logging.info('engine already stopped')
            return self.res
        try:
            self.engine.stop()
        except chess.uci.EngineTerminatedException:
            logging.error('Engine terminated')  # @todo find out, why this can happen!
        return self.future.result()

    def go(self, time_dict: dict):
        """Go engine."""
        self.show_best = True
        time_dict['async_callback'] = self.callback

        Observable.fire(Event.START_SEARCH())
        self.future = self.engine.go(**time_dict)
        return self.future

    def ponder(self):
        """Ponder engine."""
        self.show_best = False

        Observable.fire(Event.START_SEARCH())
        self.future = self.engine.go(ponder=True, infinite=True, async_callback=self.callback)
        return self.future

    def brain(self, time_dict: dict):
        """Permanent brain."""
        self.show_best = True
        time_dict['ponder'] = True
        time_dict['async_callback'] = self.callback3

        Observable.fire(Event.START_SEARCH())
        self.future = self.engine.go(**time_dict)
        return self.future

    def hit(self):
        """Send a ponder hit."""
        logging.info('show_best: %s', self.show_best)
        self.engine.ponderhit()
        self.show_best = True

    def callback(self, command):
        """Callback function."""
        try:
            self.res = command.result()
        except chess.uci.EngineTerminatedException:
            logging.error('Engine terminated')  # @todo find out, why this can happen!
            self.show_best = False
        logging.info('res: %s', self.res)
        Observable.fire(Event.STOP_SEARCH())
        if self.show_best and self.res:
            Observable.fire(Event.BEST_MOVE(move=self.res.bestmove, ponder=self.res.ponder, inbook=False))
        else:
            logging.info('event best_move not fired')

    def callback3(self, command):
        """Callback function."""
        try:
            self.res = command.result()
        except chess.uci.EngineTerminatedException:
            logging.error('Engine terminated')  # @todo find out, why this can happen!
            self.show_best = False
        logging.info('res: %s', self.res)
        Observable.fire(Event.STOP_SEARCH())
        if self.show_best and self.res:
            Observable.fire(Event.BEST_MOVE(move=self.res.bestmove, ponder=self.res.ponder, inbook=False))
        else:
            logging.info('event best_move not fired')

    def is_thinking(self):
        """Engine thinking."""
        return not self.engine.idle and not self.engine.pondering

    def is_pondering(self):
        """Engine pondering."""
        return not self.engine.idle and self.engine.pondering

    def is_waiting(self):
        """Engine waiting."""
        return self.engine.idle

    def newgame(self, game: Board):
        """Engine sometimes need this to setup internal values."""
        self.engine.ucinewgame()
        self.engine.position(game)

    def startup(self, options: dict, show=True):
        """Startup engine."""
        parser = configparser.ConfigParser()
        parser.optionxform = str
        if not options and parser.read(self.get_file() + '.uci'):
            options = dict(parser[parser.sections().pop()])
        self.level_support = bool(options)
        if parser.read(os.path.dirname(self.get_file()) + os.sep + 'engines.uci'):
            pc_opts = dict(parser[parser.sections().pop()])
            pc_opts.update(options)
            options = pc_opts

        logging.debug('setting engine with options %s', options)
        self.level(options)
        self.send()
        self.newgame(Board())
        if show:
            logging.debug('Loaded engine [%s]', self.get_name())
            logging.debug('Supported options [%s]', self.get_options())
