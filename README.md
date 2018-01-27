Picochess-nonDGT
Modified version of picochess to run with reed switch chessboard controlled via Arduino nano

This system communicates with the arduino over the usb port. It is currently set to run on  raspberry pi . The arduino scans the switch matrix of the chess board and send messages to picochess based on switch changes. Additionaly it scans 4 buttons and a rorary encoder to simulate the buttons on a DGT clock, used by picochess for setting engine, mode time etc.

The messages are newgame:color, sent when the pieces are returned to the start position, B:button number when a button is pressed. or the move in format like E2E4.

The arduino can receive from picochess information to light leds on the board They are L:square_number led on F: square_number flash led, c:anything all led's off.
or the move to make, which is then indicated by lighting the leds for the from square, when that is lifted, the 'to' square is lit.
the arduino sends 'done' when the move is made so picochess can start the player clock again.


I added to picochess code to handle these messages, mostly in sensorboard.py,