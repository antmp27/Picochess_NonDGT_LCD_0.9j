# Copyright (C) 2013-2016 Jean-Francois Romang (jromang@posteo.de)
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

import threading
import chess
from utilities import *
from dgt.api import Event, Message

keyboard_last_fen = None


class KeyboardInput(Observable, threading.Thread):
    def __init__(self, is_pi):
        super(KeyboardInput, self).__init__()
        self.flip_board = False
        self.board_plugged_in = True
        self.rt = RepeatedTimer(1, self.fire_no_board_connection)
        self.is_pi = is_pi

    def fire_no_board_connection(self):
        s = 'Board!'
        text = Dgt.DISPLAY_TEXT(l='no e-' + s, m='no' + s, s=s, wait=True, beep=False, maxtime=0)
        DisplayMsg.show(Message.NO_EBOARD_ERROR(text=text, is_pi=self.is_pi))

    def run(self):
        logging.info('evt_queue ready')
        print('#' * 42 + ' PicoChess v' + version + ' ' + '#' * 42)
        print('To play a move enter the from-to squares like "e2e4". To play this move on board, enter "go".')
        print('When the computer displays its move, also type "go" to actually do it on the board (see above).')
        print('Other commands are:')
        print('newgame:<w|b>, print:<fen>, setup:<fen>, fen:<fen>, button:<0-5>, lever:<l|r>, plug:<in|off>')
        print('')
        print('This console mode is mainly for development. Better activate picochess together with a DGT-Board ;-)')
        print('#' * 100)
        print('')
        while True:
            raw = input('PicoChess v'+version+':>').strip()
            if not raw:
                continue
            cmd = raw.lower()

            try:
                if cmd.startswith('print:'):
                    fen = raw.split(':')[1]
                    print(chess.Board(fen))
                else:
                    if not self.board_plugged_in and not cmd.startswith('plug:'):
                        print('The command isnt accepted cause the virtual board is not plugged in')
                        continue
                    if cmd.startswith('newgame:'):
                        side = cmd.split(':')[1]
                        if side == 'w':
                            self.flip_board = False
                            self.fire(Event.DGT_FEN(fen='rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR'))
                        elif side == 'b':
                            self.flip_board = True
                            self.fire(Event.DGT_FEN(fen='RNBKQBNR/PPPPPPPP/8/8/8/8/pppppppp/rnbkqbnr'))
                        else:
                            raise ValueError(side)
                    elif cmd.startswith('setup:'):
                        fen = raw.split(':')[1]
                        uci960 = False  # make it easy for the moment
                        bit_board = chess.Board(fen, uci960)
                        if bit_board.is_valid():
                            self.fire(Event.SETUP_POSITION(fen=bit_board.fen(), uci960=uci960))
                        else:
                            raise ValueError(fen)
                    # Here starts the simulation of a dgt-board!
                    # Let the user send events like the board would do
                    elif cmd.startswith('fen:'):
                        fen = raw.split(':')[1]
                        # dgt board only sends the basic fen => be sure
                        # it's same no matter what fen the user entered
                        self.fire(Event.DGT_FEN(fen=fen.split(' ')[0]))
                    elif cmd.startswith('button:'):
                        button = int(cmd.split(':')[1])
                        if button not in range(6):
                            raise ValueError(button)
                        if button == 5:  # make it to power button
                            button = 0x11
                        self.fire(Event.KEYBOARD_BUTTON(button=button, dev = 'ser'))
                    elif cmd.startswith('lever:'):
                        lever = cmd.split(':')[1]
                        if lever not in ('l', 'r'):
                            raise ValueError(lever)
                        button = 0x40 if lever == 'r' else -0x40
                        self.fire(Event.KEYBOARD_BUTTON(button=button, dev = 'ser'))
                    elif cmd.startswith('plug:'):
                        plug = cmd.split(':')[1]
                        if plug not in ('in', 'off'):
                            raise ValueError(plug)
                        if plug == 'in':
                            self.board_plugged_in = True
                            self.rt.stop()
                            text_l, text_m, text_s = 'VirtBoard  ', 'V-Board ', 'VBoard'
                            text = Dgt.DISPLAY_TEXT(l=text_l, m=text_m, s=text_s, wait=True, beep=False, maxtime=1)
                            DisplayMsg.show(Message.EBOARD_VERSION(text=text, channel='console'))
                        if plug == 'off':
                            self.board_plugged_in = False
                            self.rt.start()
                    elif cmd.startswith('go'):
                        if keyboard_last_fen is not None:
                            self.fire(Event.KEYBOARD_FEN(fen=keyboard_last_fen))
                        else:
                            print('last move already send to virtual board')
                    elif cmd.startswith('shutdown'):
                        self.fire(Event.SHUTDOWN())
                    # end simulation code
                    else:
                        # move => fen => virtual board sends fen
                        move = chess.Move.from_uci(cmd)
                        self.fire(Event.KEYBOARD_MOVE(move=move))

            except ValueError as e:
                logging.warning('Invalid user input [%s]', raw)


class TerminalDisplay(DisplayMsg, threading.Thread):
    def __init__(self):
        super(TerminalDisplay, self).__init__()

    def run(self):
        global keyboard_last_fen
        logging.info('msg_queue terminaldisplay ready')
        while True:
            # Check if we have something to display
            try:
                message = self.msg_queue.get()

                if not isinstance(message, Message.DGT_SERIAL_NR):
                    logging.debug('received message from msg_queue: %s', message)
                    #print(message)
                if isinstance(message, Message.COMPUTER_MOVE):
                    game_copy = message.game.copy()
                    game_copy.push(message.move)
                    keyboard_last_fen = game_copy.fen().split(' ')[0]
                    Observable.fire(Event.KEYBOARD_FEN(fen=keyboard_last_fen))
                    mov = message.move.uci()

                elif isinstance(message, Message.CLOCK_TIME):
                    time_u = message.time_white
                    time_c = message.time_black
                    l_hms = hms_time(time_u)
                    r_hms = hms_time(time_c)
                    text_l = '{}:{:02d}.{:02d}'.format(l_hms[0], l_hms[1], l_hms[2])
                    text_r = '{}:{:02d}.{:02d}'.format(r_hms[0], r_hms[1], r_hms[2])
                    print('Clock time: {} - {}'.format(text_l,text_r))
                elif isinstance(message, Message.ENGINE_STARTUP):
                    print(message.level_index)
                elif isinstance(message, Message.ENGINE_READY):
                    print(message.engine_name)
                elif isinstance(message, Message.SYSTEM_INFO):
                    engine_name = message.info['engine_name']

                    self.user_name = message.info['user_name']
                    self.user_elo = message.info['user_elo']
                    print(engine_name)
                elif isinstance(message, Message.STARTUP_INFO):
                    self.level_text = message.info['level_text']
                    self.level_name = message.info['level_name']
                    timetexta = message.info['time_text']
                    timetext = timetexta.m
                    print(timetext)
                elif isinstance(message, Message.LEVEL):
                    print(message.level_text.m)
                elif isinstance(message, Message.DISPLAY_TEXT):
                    print(message.text)

            except queue.Empty:
                pass
