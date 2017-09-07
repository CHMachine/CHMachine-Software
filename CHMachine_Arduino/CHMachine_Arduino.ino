/*
  COCK HERO MACHINE serial connection V.0.9
  http://cockheromachine.blogspot.it/
  cockheromachine@gmail.com
  
  This program is expected to receive over serial an 8bit integer value between the string 'V' and any other string(e.g. V100S) to vary the pulse width accordingly on the analog pin. 
  The pin PWM goes to 0 after 200ms if no signal is received.
  
*/

int Value = 0;
int pin = 5;
int timelimit = 200;
long unsigned timer = 0;

void setup() {
  // initialize the digital pin as an output.
  pinMode(pin, OUTPUT);
  Serial.begin(9600);
  //Serial.print("connOK"); 
 
}

// the loop routine runs over and over again forever:
void loop() {
  
  if (Serial.available() > 0) {



    if (Serial.peek() == 'V') {      //check for the character that signifies that this will be on
      Serial.read();                 //remove the first character(V)
      Value = Serial.parseInt();     //read the value
      Serial.read();                 //remove the last character(S)
      analogWrite(pin, Value);       // set the state of the PIN
      timer = millis();              //reset the timer
    }


    else if (Serial.peek() == 'K') {      //the character K must be sent to reset the timer and keep the analog pin ON
      Serial.read();                 //remove the first character
      timer = millis();              //reset the timer
    }

    else if (Serial.peek() == 'T') {      //check for the character T that estabilish the connection
      Serial.read();   //clean the serial buffer
      Serial.println("connOK");         //send a string
      
         
    }
    else
      Serial.read();                 //clear the serial buffer


  }

  if (millis() - timer >= timelimit) { //turn off the pin after some time if no data is received
    analogWrite(pin, 0);
  }

}
