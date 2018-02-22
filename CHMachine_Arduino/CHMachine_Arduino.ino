/*
  COCK HERO MACHINE serial connection V.0.9.1
  http://cockheromachine.blogspot.it/
  cockheromachine@gmail.com

  This program is expected to receive over serial an 8bit integer value between the string 'V' and any other string(e.g. V100S) to vary the pulse width accordingly on the analog pin.
  The pin PWM goes to 0 after 200ms if no signal is received.
  Optionally, a rotary encoder can be connected to vary the PWM duty cycle without the need of a serial connection.

*/


const int encoderPin1 = 2; //encoder pin A
const int encoderPin2 = 3;//encoder pin B
const int pwmpin = 5; //PWM
const int BUTTONpin = 12; // Pin for Button
int Value = 0; //PWM speed from serial
const int timelimit = 200; // turn off time after no data is received

long unsigned timer = 0; // time since last data is received

volatile int lastEncoded = 0;
volatile long encoderValue = 0;//PWM value from encoder
long lastencoderValue = 0;// last PWM value from encoder
volatile bool knobstate = 1;//turn to 1 when encoder has been turned

const int buttonWaitInterval = 5000; //microseconds between bounces

unsigned long previousMicros = 0;// Used to track how long between "bounces"
bool previousButtonState = 0;// Used to track state of button (high or low)
bool debouncedButtonState = 0;// Variable reporting de-bounced state.
bool bounceState = 0;// Tracks if we are waiting for a "bounce" event


void setup() {
  Serial.begin (9600);

  pinMode(encoderPin1, INPUT_PULLUP);
  pinMode(encoderPin2, INPUT_PULLUP);
  pinMode(pwmpin, OUTPUT);
  pinMode(BUTTONpin, INPUT_PULLUP);

  analogWrite (pwmpin, 0);

  attachInterrupt(0, updateEncoder, CHANGE);
  attachInterrupt(1, updateEncoder, CHANGE);

}



void updateEncoder() {
  knobstate = 1;

  int MSB = digitalRead(encoderPin1); //MSB = most significant bit
  int LSB = digitalRead(encoderPin2); //LSB = least significant bit

  int encoded = (MSB << 1) | LSB; //converting the 2 pin value to single number
  int sum  = (lastEncoded << 2) | encoded; //adding it to the previous encoded value

  if (sum == 0b1101 || sum == 0b0100 || sum == 0b0010 || sum == 0b1011) encoderValue ++;
  if (sum == 0b1110 || sum == 0b0111 || sum == 0b0001 || sum == 0b1000) encoderValue --;

  lastEncoded = encoded; //store this value for next time
}


void updateButton() {

  if (bounceState == 1) {// Waiting for any activity on the button
    boolean currentButtonState = digitalRead(BUTTONpin); // Get and store current button state

    if (previousButtonState != currentButtonState) {// Check to see if a transition has occured (and only one)

      bounceState = 0;// A transition was detected, ignore the others for a while

      previousMicros = micros(); // Store current time (start the clock)
    }

    previousButtonState = currentButtonState;// Keep storing existing button state
  }

  if (bounceState == 0) {// We are waiting for the buttonWaitInterval to elapse

    unsigned long currentMicros = micros();// Compare current value of micros to previously stored, enough time yet?
    if ((unsigned long)(currentMicros - previousMicros) >= buttonWaitInterval) {
      // Store the state of the button to debouncedButtonState, which "reports"
      // the correct value. This allows for the code to handle active high or low inputs
      debouncedButtonState = digitalRead(BUTTONpin);

      bounceState = 1;// Go back to watching the button again.
    }
  }
}





void loop() {


  if (Serial.available() > 0 ) {
    knobstate = 0;
    encoderValue = 0;

    if (Serial.peek() == 'V') {      //The 'V' character preced the PWM value for the PWM pin
      Serial.read();                 //remove the first character(V)
      Value = Serial.parseInt();     //read the value
      Serial.read();                 //remove the last character(S)
      analogWrite(pwmpin, Value);       // set the state of the PIN
      timer = millis();              //reset the timer
    }


    else if (Serial.peek() == 'K') {      //the character 'K' reset the timer and keep the analog pin ON (if the connection is lost the pin goes LOW for safety precaution)
      Serial.read();                 //remove the first character
      timer = millis();              //reset the timer
    }

    else if (Serial.peek() == 'T') {      //the character 'T' is used to check if the connection is established
      Serial.read();                      //clean the serial buffer
      Serial.println("connOK");         //send a string


    }
    else
      Serial.read();                 //clear the serial buffer


  }

  if (millis() - timer >= timelimit and knobstate == 0) { //turn off the pin after some time if no character 'K' is received
    analogWrite(pwmpin, 0);
  }

////rotary encoder stuffs:
  if (knobstate == 1) {
    updateButton();

    if (debouncedButtonState == 0) {
      encoderValue = 0;
    }

    if (encoderValue != lastencoderValue) {

      if ( encoderValue > 255 ) {
        encoderValue = 255;
      }
      if ( encoderValue < 0 )   {
        encoderValue = 0;
      }

      analogWrite(pwmpin, encoderValue);
      lastencoderValue = encoderValue;
    }
  }





}





