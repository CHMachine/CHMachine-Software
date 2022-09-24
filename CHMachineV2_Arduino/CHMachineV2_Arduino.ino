/*
  COCK HERO MACHINE serial connection V.2.0
  http://cockheromachine.blogspot.it/
  cockheromachine@gmail.com

  This program can interpret both the Cock Hero Machine code AND
  the Toy-code("T-code" v0.3)https://stpihkal.docs.buttplug.io/protocols/tcode.html

*/

#include <SoftwareSerial.h>
int rxPin = 2;
int txPin = 3;
SoftwareSerial mySerial(rxPin, txPin);
int PWMPin = 5;

String softserial_str; //string buffer for softserial
String str; //to store the command from serial
String command_str;//to manipulate the command from serial
String magnitude_str;
String timeinterval_str;
String magnituderamp_str;
float magnitude;
float magnitudenow = 0;
float timeinterval;
float magnituderamp;
int PWMspeed;
int CHM_timelimit = 200; //timelimit to stop the motor if no commands are received
int TCODE_timelimit = 1000; //timelimit to stop the motor if no commands are received
long unsigned TICms;
long unsigned timezero;
long unsigned CHM_timer; //time(ms)since the last CHM command
long unsigned TCODE_timer; //time(ms)since the last TCODE command
bool CHM_mode = false;
bool TCODE_mode = false;

void setup() {

  pinMode(PWMPin, OUTPUT); // initialize the digital pin as an output.
  pinMode(rxPin, INPUT);//softserial rx pin
  pinMode(txPin, OUTPUT);//softserial tx pin
  timezero = millis();
  CHM_timer = millis();
  TCODE_timer = millis();
  mySerial.begin(57600);
  Serial.begin(115200);
  // reserve 200 bytes for the input command strings:
  str.reserve(200);
  softserial_str.reserve(200);
  //
}


void loop() { // the loop routine runs over and over again forever:
  //read inputs from serial:
  if (mySerial.available() > 0) {

    char inChar = (char)mySerial.read();
    softserial_str = softserial_str + inChar;

    if (inChar == '\n') {
      str = softserial_str;
      softserial_str = ("");
      CHM_timer = millis();
      str.trim();//gets rid of all the unseen character like \n \r
      str.toUpperCase(); //set all characters to uppercase

    }


  }
  else if (Serial.available() > 0) {
    str = Serial.readStringUntil('\n');
    CHM_timer = millis();
    str.trim();//gets rid of all the unseen character like \n \r
    str.toUpperCase(); //set all characters to uppercase
  }
  //

  //CHM-code:

  if (str.startsWith("V") && str.endsWith("S")) {
    CHM_mode = true;
    TCODE_mode = false;
    command_str = str.substring(1, str.length() - 1);//extract the PWM value from the command string
    PWMspeed = command_str.toInt();
    str = ("");//empties the used str
  }

  else if (str.indexOf("CHMT") != -1) {
    CHM_mode = true;
    TCODE_mode = false;
    Serial.println("connOK");
    mySerial.println("connOK");
    str = ("");//empties the used str
  }

  //
  //Toy-code:
  else if (str.indexOf("V0") != -1) {
    TCODE_mode = true;
    CHM_mode = false;
    TCODE_timer = millis();
    str = str + " ";   //append a space to serve as end of line

    //Remove start/end of line commands from the received string:
    int indx_a = str.indexOf("V0");
    int indx_b = str.indexOf(" ", indx_a);
    command_str = str.substring(indx_a + 2, indx_b);
    //

    str = "";//empties the used str
    int indx_c = command_str.indexOf("I");// search for time interval command
    int indx_d = command_str.indexOf("S");// search for time ramp speed command

    if (indx_c != -1) {// if timeinterval command
      magnitude_str = command_str.substring(0, indx_c);//extract magnitude string
      magnitude_str = "0." + magnitude_str;//add "0." to convert the string to float

      //convert string to float:
      char carraymag[magnitude_str.length() + 1]; //determine size of the array
      magnitude_str.toCharArray(carraymag, sizeof(carraymag)); //put string into an array
      magnitude = atof(carraymag);//convert array to float
      //

      timeinterval_str = command_str.substring(indx_c + 1, command_str.length()); // extract time interval value from string

      //convert string to float:
      char carraytime[timeinterval_str.length() + 1]; //determine size of the array
      timeinterval_str.toCharArray(carraytime, sizeof(carraytime)); //put string into an array
      timeinterval = atof(carraytime);//convert array to float
      //

      magnituderamp = ((magnitude - magnitudenow) / timeinterval); //calculate rate of magnitude variation from time interval(dMAGNITUDE/ms)(example: (V199I2000  ramp to 0.99 over 2 seconds)
      magnituderamp = sqrt(magnituderamp * magnituderamp); //remove negative sign

    }

    else if (indx_d != -1) { // if timeramp command
      magnitude_str = command_str.substring(0, indx_d);//extract magnitude string
      magnitude_str = "0." + magnitude_str;//add "0." to convert the string to float

      //convert string to float:
      char carraymag[magnitude_str.length() + 1]; //determine size of the array
      magnitude_str.toCharArray(carraymag, sizeof(carraymag)); //put string into an array
      magnitude = atof(carraymag);//convert array to float
      //
      magnituderamp_str = command_str.substring(indx_d + 1, command_str.length()); // extract ramp speed value

      //convert string to float:
      char carrayramp[magnituderamp_str.length() + 1]; //determine size of the array
      magnituderamp_str.toCharArray(carrayramp, sizeof(carrayramp)); //put string into an array
      magnituderamp = atof(carrayramp);//convert array to float
      magnituderamp = magnituderamp / 100000;//convert the units to dMAGNITUDE/ms, (example: (V020S10 ramp to 0.2 at a rate of 0.1/sec))

      //

    }

    else {//if magnitude only command
      magnitude_str = command_str.substring(0, command_str.length());//extract magnitude string
      magnitude_str = "0." + magnitude_str;

      //convert string to float:
      char carraymag[magnitude_str.length() + 1]; //determine size of the array
      magnitude_str.toCharArray(carraymag, sizeof(carraymag)); //put string into an array
      magnitude = atof(carraymag);//convert array to float
      //

      magnituderamp = 1;
    }
  }

  if (TCODE_mode) {

    //calculate magnitude variation on every loop cicle:
    TICms = millis() - timezero;
    timezero = millis();
    if (magnitudenow < magnitude) {
      magnitudenow += magnituderamp * TICms;
      if (magnitudenow > magnitude) {
        magnitudenow = magnitude;
      }
    }
    if (magnitudenow > magnitude) {
      magnitudenow -= magnituderamp * TICms;
      if (magnitudenow < magnitude) {
        magnitudenow = magnitude;
      }
    }
    PWMspeed = round(magnitudenow * 255.0);//calculate PWM value from magnitude
    //
  }

  if ((millis() - CHM_timer >= CHM_timelimit) && (CHM_mode == true)) { //turn off the toy after some time if no commands are received (just a safety precaution)
    PWMspeed = 0;
    CHM_mode = false;
  }

  if ((millis() - TCODE_timer >= TCODE_timelimit) && (TCODE_mode == true)) { //turn off the toy after some time if no commands are received (just a safety precaution)
    str = "V00I500\n";
    TCODE_mode = false;
  }

  analogWrite(PWMPin, PWMspeed);

}
