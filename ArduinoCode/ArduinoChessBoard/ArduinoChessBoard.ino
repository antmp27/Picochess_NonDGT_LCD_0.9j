
#include "Adafruit_LEDBackpack.h"
#include <Wire.h>
#include "Adafruit_GFX.h"


Adafruit_LEDBackpack matrix = Adafruit_LEDBackpack();

#define White 0
#define Black 1;
#define  SR_Sin  6  //4021 #3
#define  PSCont  8  //4021 #9
#define  SR_SCLK  7  //4021 #10

#define  Cntr_CLK 4   //4017 #14
#define  Cntr_CLR 5   //4017 #15  //4017 #13 grnd

#define B1 2
#define B2 3
#define B3 11
#define B4 12

#define Enc_In1 9
#define Enc_In2 10

//for encoders
#define DIR_CCW 0x10
#define DIR_CW 0x20

const unsigned char ttable[7][4] = {            //for encoders
  {0x0, 0x2, 0x4, 0x0}, {0x3, 0x0, 0x1, 0x10},
  {0x3, 0x2, 0x0, 0x0}, {0x3, 0x2, 0x1, 0x0},
  {0x6, 0x0, 0x4, 0x0}, {0x6, 0x5, 0x0, 0x20},
  {0x6, 0x5, 0x4, 0x0},
};
int speakerPin = 13;

int numTones = 10;
int tones[] = {261, 277, 294, 311, 330, 349, 370, 392, 415, 440};
//            mid C  C#   D    D#   E    F    F#   G    G#   A

char * boardsquare[] = {"A1", "B1", "C1", "D1", "E1", "F1", "G1", "H1",
                        "A2", "B2", "C2", "D2", "E2", "F2", "G2", "H2",
                        "A3", "B3", "C3", "D3", "E3", "F3", "G3", "H3",
                        "A4", "B4", "C4", "D4", "E4", "F4", "G4", "H4",
                        "A5", "B5", "C5", "D5", "E5", "F5", "G5", "H5",
                        "A6", "B6", "C6", "D6", "E6", "F6", "G6", "H6",
                        "A7", "B7", "C7", "D7", "E7", "F7", "G7", "H7",
                        "A8", "B8", "C8", "D8", "E8", "F8", "G8", "H8"
                       };
int move_to, move_from;
bool computermove = false;
bool gameinprogess = false;
int keychanged;
int buttonmask;
bool lifted;
int boardmatrix[8][8];     //kb matrix
long startTime = 0;  // the last time the output pin was toggled
long btnDebounce;

int key;
int row;
int column;
int state;
int rpState;
bool b1State;
bool b2State;
bool b3State;
bool b4State;

int b1Latch;
int b2Latch;
int b3Latch;
int b4Latch;
unsigned long lastDebounceTime = 0;  // the last time the output pin was toggled
unsigned long debounceDelay = 50;    // the debounce time; increase if the output flickers

void setup()
{
  pinMode(SR_Sin , INPUT);
  pinMode(PSCont, OUTPUT);
  pinMode(SR_SCLK, OUTPUT);

  pinMode(SR_Sin , INPUT);
  pinMode(Cntr_CLK, OUTPUT);
  pinMode(Cntr_CLR, OUTPUT);

  pinMode(Enc_In1, INPUT_PULLUP);
  pinMode(Enc_In2, INPUT_PULLUP);

  pinMode(B1, INPUT_PULLUP);
  pinMode(B2, INPUT_PULLUP);
  pinMode(B3, INPUT_PULLUP);
  pinMode(B4, INPUT_PULLUP);

  Serial.begin(115200);
  Serial.setTimeout(50);
  matrix.begin(0x70);  // pass in the address
  matrix.clear();
  //matrix.blinkRate(HT16K33_BLINK_2HZ);

  newgame(White);
  fillMatrix();
  matrix.writeDisplay();
}

void loop()
{

  bool buttonEnable = true;
  long buttonDelay;
  int r;


 
  FromPython();


  r = rotary_process();
  if (r == 16)
  {
    ToPython("B:3\n");
    r = 0;
  }
  else if (r == 32)
  {
    ToPython("B:1\n");
    r = 0;
  }

  if (KeyChanged())
  {
    FlashSquare(keychanged, 100);
    if (computermove)
    {
      MakeComputerMove(keychanged);
    }
    else
    {
      MakeUserMove(keychanged);
    }
    if(!lifted)
    {
      CheckBoardPosition();
    }
  }
//  if (CheckStartPosition())
//  {
//    //ToPython("NG");
//    if (gameinprogess)
//    {
//      //ToPython("ng_GIP");
//      newgame(White);
//      gameinprogess = false;
//    }
//  }

  if ((millis() - lastDebounceTime) > debounceDelay)
  {

    if (digitalRead(B1) == 0)
    {
      lastDebounceTime = millis();
      if (b1Latch == 1 && b1State == false)
      {
        b1State = true;
        ToPython("B:4\n");  //lever
      }
      else
      {
        b1Latch = 1;
      }
    }
    else
    {
      b1Latch == 0;
      b1State = false;
    }



    if (digitalRead(B2) == 0)
    {
      lastDebounceTime = millis();
      if (b2Latch == 1 && b2State == false)
      {
        b2State = true;
        ToPython("B:0\n");  //lever
      }
      else
      {
        b2Latch = 1;
      }
    }
    else
    {
      b2Latch == 0;
      b2State = false;
    }

    if (digitalRead(B4) == 0)
    {

      lastDebounceTime = millis();
      if (b4Latch == 1 && b4State == false)
      {
        b4State = true;
        ToPython("B:5\n");  //lever
      }
      else
      {
        b4Latch = 1;
      }
    }
    else
    {
      b4Latch == 0;
      b4State = false;
    }

    if (digitalRead(B3) == 0)
    {
      lastDebounceTime = millis();
      if (b3Latch == 1 && b3State == false)
      {
        b3State = true;
        ToPython("B:2\n");  //lever
      }
      else
      {
        b3Latch = 1;
      }
    }
    else
    {
      b3Latch == 0;
      b3State = false;
    }


  }
}
void MakeComputerMove(int square)
{
  if (lifted)
  {
    if (square == move_from)
    {
      beep(450, 100);
      LightSquare(move_to, true);
      matrix.writeDisplay();
    }
    else if (square == move_to)  //remove taken piece
    {
      //do nothing
    }
    else
    {
      beep(550, 150);
      beep(450, 100); //wrong
    }
  }

  else   //dropped
  {
    if (square == move_to)
    {
      beep(350, 100);
      matrix.clear();
      matrix.writeDisplay();
      computermove = false;
      ToPython("Done");
    }
  }
}
void MakeUserMove(int square)
{
  static bool startsquare;
  if (lifted)
  {
    if (!startsquare)
    {
      beep(500, 100);
      LightSquare(square, true);
      matrix.writeDisplay();
      move_from = square;
      startsquare = true;
    }
    else
    {
      // remove oppenents piece
    }
  }
  else  //dropped
  {
    if (move_from != square)    //!put back on same square
    {
      matrix.clear();
      String move = boardsquare[move_from];
      ToPython(move + boardsquare[square]);
      FlashSquare(square, 100);
      beep(400, 100);
    }
    else
    {
      FlashSquare(square, 100);  //dropped on same square
      beep(300, 200);
    }
    startsquare = false;
  }
}

void ToPython(String s)
{
  Serial.println(s);// write a string
}

void FromPython()
{
  if (Serial.available() > 2)
  {
    char data = Serial.read();
    //    if (data == 'F')  //Flash
    //    {
    //      int sq = Serial.parseInt();
    //      FlashSquare(sq, 50);
    //    }
    //    if (data == 'L') //LED on
    //    {
    //      beep(600);
    //      int sq = Serial.parseInt();
    //      LightSquare(sq,true);
    //      matrix.writeDisplay();
    //    }
    //    if (data == 'C')  //LED Off
    //    {
    //       int sq = Serial.parseInt();
    //       ClearLeds();
    //    }
    //    if (data == 'B')
    //    {
    //       int sq = Serial.parseInt();
    //       beep(sq);
    //    }
    if (data == 'F')    //from computer 'from square'
    {
      gameinprogess = true;
      computermove = true;
      move_from = Serial.parseInt();
      beep(350, 50);
      LightSquare(move_from, true);
      matrix.writeDisplay();
    }
    if (data == 'T')  //from computer 'to square'
    {
      move_to = Serial.parseInt();
      computermove = true;
      //LightSquare(sq,true);
      // beep(450,50);
      // matrix.writeDisplay();
    }
  }
}

bool KeyChanged()
{
  static int lastkey;

  if (checkmatrix() != 99)
  { //key changed

    boardmatrix[row][column] = state;
    keychanged = key;
    if (state == 1) lifted = false;
    else lifted = true;
    return true;
  }
  return false;
}

bool GetKeyState(int key)
{
  int c = key / 8;
  int r = key & 0x7;
  if (boardmatrix[c][r] == 1) return true;
  else return false;
}

int checkmatrix()
{
  static int lastkey;
  //Serial.println("CheckMatrix");
  digitalWrite(Cntr_CLR, HIGH); //reset 4017
  digitalWrite(Cntr_CLR, LOW);

  for (row = 0; row < 8; row++)
  {
    digitalWrite(Cntr_CLK, HIGH);  //clock 4017 -use outputs 1-9 ; not 0
    digitalWrite(Cntr_CLK, LOW);

    digitalWrite(PSCont, HIGH);   //latch paralel data
    digitalWrite(PSCont, LOW);
    for (column = 7; column >= 0; column--)
    {
      int data = digitalRead(SR_Sin);
      if (data != boardmatrix[row][column])
      {
        state = data;
        key = (row * 8 + column);
        if (key == lastkey)
        {
          lastkey = 0;
          return (key);
        }
        else
        {
          lastkey = key;
        }
      }
      digitalWrite(SR_SCLK, HIGH);            //next bit
      digitalWrite(SR_SCLK, LOW);
    }
  }
  //digitalWrite(Cntr_CLR, HIGH); //reset 4017
  //digitalWrite(Cntr_CLR, LOW);
  return (99);
}

// reads the current switch states into matrix
void fillMatrix()
{
  digitalWrite(Cntr_CLR, HIGH); //reset 4017
  digitalWrite(Cntr_CLR, LOW);

  for (int row = 0; row < 8; row++)
  {
    digitalWrite(Cntr_CLK, HIGH);  //clock 4017 -use outputs 1-9 ; not 0
    digitalWrite(Cntr_CLK, LOW);

    // digitalWrite(PSCont, HIGH);   //latch paralel data
    PORTB = PORTB | B00000001;
    delayMicroseconds(1);
    // digitalWrite(PSCont, LOW);
    PORTB = PORTB & B11111110;
    for (int column = 7; column >= 0; column--)
    {
      int data = digitalRead(SR_Sin);
      boardmatrix[row][column] = data;

      PORTD = PORTD | B10000000;
      delayMicroseconds(1);
      // digitalWrite(SR_SCLK, HIGH);            //next bit
      PORTD = PORTD & B01111111;
      //  digitalWrite(SR_SCLK, LOW);
    }
  }
}
void  lightled(int row, int column, bool on)
{
  if (column < 8)
  {
    if (on) matrix.displaybuffer[column] |= (1 << row);
    else matrix.displaybuffer[column] &= ~(1 << row);
  }
  else if (row < 8) //column 8
  {
    if (on) matrix.displaybuffer[row] |= (1 << 9);
    else matrix.displaybuffer[row] &= ~(1 << 9);
  }
  else  //column and row 8
  {
    if (on) matrix.displaybuffer[0] |= (1 << 10);
    else matrix.displaybuffer[0] &= ~(1 << 10);
  }
}

void ClearLeds()
{
  for (int i = 0; i < 8; i++)
  {
    matrix.displaybuffer[i] = 0;
  }
  matrix.writeDisplay();
}

void FlashSquare(int square, int milliseconds)
{
  ClearLeds();
  LightSquare(square, true);
  matrix.writeDisplay();
  //beep(350,milliseconds);
  delay(milliseconds);
  LightSquare(square, false);
  matrix.writeDisplay();
}

void  LightSquare(int square, bool on)
{
  int row = int (square / 8);
  int column = square & 7;
  lightled(row, column, on);
  lightled(row + 1, column, on);
  lightled(row, column + 1, on);
  lightled(row + 1, column + 1, on);
  matrix.writeDisplay();
}

void beep(int note1, int lengh)
{
  tone(speakerPin, note1);
  delay(lengh);
  noTone(speakerPin);
  //delay(100);
  //tone(speakerPin, note2);
  //delay(50);
  //noTone(speakerPin);

}
unsigned char rotary_process()
{


  unsigned char pinstate = ((bitRead(PINB, 1)) << 1) | bitRead(PINB, 2); //Digitalpin 9&10
  rpState = ttable[rpState & 0xf][pinstate];
  return (rpState & 0x30);
}
bool CheckStartPosition()
{
  for (int i = 0; i < 16; i++)
  {
    if (!GetKeyState(i))
    {
      return false;
    }
  }
  for (int i = 48; i < 64; i++)
  {
    if (!GetKeyState(i))
    {
      return false;
    }
  }
  return true;
}
void newgame(int color)
{
  int brdsetup = 0;

  while (brdsetup < 32)
  {
    fillMatrix(); //piece positions to matrix
    bool on;
    matrix.clear();

    brdsetup = 32;
    for (int i = 0; i < 16; i++)
    {
      if (!GetKeyState(i))
      {
        brdsetup--;
        LightSquare(i, true);
      }
    }
    for (int i = 48; i < 64; i++)
    {
      if (!GetKeyState(i))
      {
        brdsetup--;
        LightSquare(i, true);
      }
    }
    matrix.writeDisplay();
  }
  //
  //    beep(400, 50);
  //    delay(500);
  //    beep(400, 50);
  //    delay(500);
  //    beep(440, 300);

  if (color)   ToPython("newgame:b");
  else ToPython("newgame:w");
}
//'RNBKQBNR/PPPPPPPP/8/8/8/8/pppppppp/rnbqqbnr' = REBOOT


void CheckBoardPosition()
{
  fillMatrix(); //piece positions to matrix
  int squarecount=0;
  for (row = 0; row < 8; row++)
  {
    for (column = 0; column < 8; column++)
    {
      if (row == 0 || row == 1 || row == 6 || row == 7)
      {
        if (boardmatrix[row][column] == 1) //occupied
        {
          squarecount++;
          //LightSquare(row * 8 + column, true);
        }
      }
    }
  }
  if(squarecount==32)
  {
     if (boardmatrix[2][0] == 1)
     {
        ToPython("shutdown");  //reboot
     }
     else if(boardmatrix[2][1] == 1)
     {
        ToPython("reboot");  //reboot
     }
     else ToPython("newgame:w");
     
  }
}


