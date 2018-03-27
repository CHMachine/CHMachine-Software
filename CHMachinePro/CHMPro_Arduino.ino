/*
  COCK HERO MACHINE Pro serial connection V.0.9
  http://cockheromachine.blogspot.it/
  cockheromachine@gmail.com
  
  This program is expected to receive over serial an 8bit integer value between the string 'V' and any other string(e.g. V100S) to vary the pulse width accordingly on the analog pin. 
  The pin PWM goes to 0 after 200ms if no integers are sent.
  
*/
#ifndef cbi
#define cbi(sfr, bit) (_SFR_BYTE(sfr) &= ~_BV(bit))
#endif
#include <SoftwareSerial.h>
int Value = 0;
int pinPWM = 0;// NOTA:pin 0 è corretto
int rxPin = 1;
int txPin = 2;
int timelimit = 200;
long unsigned timer = 0;
SoftwareSerial mySerial(rxPin, txPin); //rx,tx

void setup() {
  pinMode(pinPWM, OUTPUT);// initialize the digital pin as an output.
  analogWrite(pinPWM, 0);
  cbi(ADCSRA, ADEN); // Switch Analog to Digital converter OFF
  pinMode(rxPin, INPUT);
  pinMode(txPin, OUTPUT);
  //pinMode(3, INPUT_PULLUP); 
  //pinMode(4, INPUT_PULLUP); //pulling up unused pin, da non fare se si usa xtal
  mySerial.begin(9600);
  
}

// the loop routine runs over and over again forever:
void loop() {

  if (mySerial.available() > 0) {

    if (mySerial.peek() == 'V') {      //The 'V' character preced the PWM value for the PWM pin
      mySerial.read();                 //remove the first character(V)
      Value = mySerial.parseInt();     //read the value
      mySerial.read();                //remove the last character(S)
      analogWrite(pinPWM, Value);       // set the state of the PIN
      timer = millis();              //reset the timer
    }


    else if (mySerial.peek() == 'T') {      //the character 'T' is used to check if the connection is established
      mySerial.read();                 //clean the serial buffer
      mySerial.print("connOK");         //send a string
                
    }
    
    else
      mySerial.read();                 //clear the serial buffer


  }

  if (millis() - timer >= timelimit) { //turn off the pin after some time if no character 'K' is received
    analogWrite(pinPWM, 0);
  }

}
