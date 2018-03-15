/*
  COCK HERO MACHINE serial connection V.0.9
  http://cockheromachine.blogspot.it/
  cockheromachine@gmail.com
  
  This program is expected to receive over serial an 8bit integer value between the string 'V' and any other string(e.g. V100S) to vary the pulse width accordingly on the analog pin. 
  The PWM pin goes to 0 after 200ms if no signal is received.
  
*/

int Value = 0;
int pin = 5;
int timelimit = 200;
long unsigned timer = 0;

void setup() {
  // initialize the digital pin as an output.
  pinMode(pin, OUTPUT);
  Serial.begin(9600);

 
}

// the loop routine runs over and over again forever:
void loop() {
  
  if (Serial.available() > 0) {



    if (Serial.peek() == 'V') {      //check for the character V
      Serial.read();                 //remove the character V from buffer
      Value = Serial.parseInt();     //read the integer value
      Serial.read();                 //remove the last character(S)
      analogWrite(pin, Value);       // set the state of the PIN
      timer = millis();              //reset the timer
    }

    //check if the connection is estabilished:
    else if (Serial.peek() == 'T') {      //check for the character T
      Serial.read();                      //clean the serial buffer
      Serial.println("connOK");           //send a string
      
         
    }
    else
      Serial.read();                 //clear the serial buffer from other characters


  }

  if (millis() - timer >= timelimit) { //turn off the pin for after some time if no data is received (just a safety precaution)
    analogWrite(pin, 0);
  }

}
