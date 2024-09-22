#include <Adafruit_GFX.h>    
#include <Adafruit_ST7735.h> 
#include <SPI.h>
#include "HX711.h"
#include <Servo.h>

// HX711 circuit wiring
const int LOADCELL_DOUT_PIN = 50;
const int LOADCELL_SCK_PIN = 52;

HX711 scale;

const int csPin =  10;
const int dcPin = 9;
const int rstPin = 8;

Adafruit_ST7735 tft = Adafruit_ST7735(csPin, dcPin, rstPin);

int sensorPinV = A3;// lecture tension aprs division 
int sensorPinA = A4;// lecture amperage capteur de courant

float sensorValueV = 0;
float sensorValueA = 0;
float sensorValueT = 0;
int sensorValueR = 0;

// Motor control
const int ESC_PIN = 11;  // PWM pin for ESC control
Servo esc;
int currentSpeed = 0;
int targetSpeed = 0;

// Add these constants for motor speed options
const int SPEED_OPTIONS[] = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100};
const int NUM_SPEED_OPTIONS = 10;

// Speed ramping parameters
const int SPEED_INCREMENT = 1;  // Speed increment per step
const unsigned long RAMP_DELAY = 50;  // Delay between speed increments (milliseconds)
unsigned long lastRampTime = 0;

// PWM signal range
const int PWM_MIN = 1100;
const int PWM_MAX = 1900;

// Serial command handling
String inputString = "";
bool stringComplete = false;

int watts = 0;
float maxT = 0, highT = 0;
float maxA = 0, highA = 0;
float maxV = 0, highV = 0;
float maxR = 0, highR = 0;
int maxW = 0;
int highW = 0;
int x = 80;
int xh = 80;

//tachymetre
float value = 0;
float rev = 0;
int rpm;
int oldtime = 0;
int time;

void isr() //interrupt service routine
{
  rev++;
}

void setup() {
  attachInterrupt(0, isr, RISING);
  Serial.begin(57600);

  // Initialize motor control
  esc.attach(ESC_PIN, PWM_MIN, PWM_MAX);
  esc.writeMicroseconds(PWM_MIN);  // Ensure motor starts at minimum speed
  delay(5000);  // Wait for ESC to initialize

  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(-116.156);  // Calibration factor
  scale.tare();               // Reset the scale to 0

  // initialisation ecran
  tft.initR(INITR_GREENTAB);
  tft.fillScreen(ST7735_BLACK);
  tft.setTextSize(2);
  tft.setTextColor(ST7735_GREEN, ST7735_BLACK);
  //ecran d'accueuil
  tft.setCursor(30, 1);
  tft.print("THRUST ");
  tft.setCursor(35, 30);
  tft.print("STAND");
    tft.setCursor(50, 60);
 tft.print("YM");
  tft.setCursor(8, 80);
  tft.setTextSize(1);
  tft.setTextColor(ST7735_YELLOW,ST7735_BLACK);
  tft.print("mesures : ");
  tft.setCursor(10, 100);
  tft.setTextColor(ST7735_CYAN, ST7735_BLACK);
   tft.print("thrust G  ");
    tft.setCursor(10, 110);
   tft.print("tension batterie V ");
    tft.setCursor(10, 120);
   tft.print("Amperage A ");
    tft.setCursor(10, 130);
   tft.print("v rotation T/min ");
   tft.setCursor(10, 140);
   tft.print("puissance W ");
  delay (500);
  //ecran d'avertissement de danger
  for (int i=0; i <= 10; i++){ 
  tft.fillScreen(ST7735_BLACK);
  tft.setTextSize(2);
  tft.setTextColor(ST7735_RED,ST7735_BLACK);
  tft.setCursor(10, 10);
  tft.print("ATTENTION ");
  tft.setCursor(25, 50);
  tft.print("DANGER");
  tft.setCursor(10, 70);
  tft.print("ELOIGNER ");
  tft.setCursor(40, 90);
 tft.print("VOUS");
 tft.setCursor(50, 110);
 tft.print("DE");
 tft.setCursor(10, 130);
 tft.print(" L'HELICE  ");
 delay (50);
  }
 tft.fillScreen(ST7735_BLACK);
  
  
  Serial.println("Scale setup complete. Starting measurements...");
  Serial.println("Motor control commands:");
  Serial.println("S[0-9] : Set motor speed (10% to 100%)");
  Serial.println("R : Read current motor speed");
}

void loop() {
  // Handle serial commands
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }

  // Gradual speed adjustment
  if (currentSpeed != targetSpeed && millis() - lastRampTime >= RAMP_DELAY) {
    if (currentSpeed < targetSpeed) {
      currentSpeed = min(currentSpeed + SPEED_INCREMENT, targetSpeed);
    } else {
      currentSpeed = max(currentSpeed - SPEED_INCREMENT, targetSpeed);
    }
    setMotorSpeed(currentSpeed);
    lastRampTime = millis();
  }

  //tachymetre
  detachInterrupt(0);
  time = millis() - oldtime;
  rpm = (rev / time) * 60000 * 2;
  oldtime = millis();

  // Read thrust
  float thrust = scale.get_units(5);  // Average of 5 readings

  tft.setTextColor(ST7735_CYAN, ST7735_BLACK);
  tft.setCursor(33, 44);
  tft.print("     ");

  //
  tft.setTextSize(1);
  tft.setTextColor(ST7735_GREEN, ST7735_BLACK);
  sensorValueV = analogRead(sensorPinV); //lecture de la tension 
  sensorValueA = analogRead(sensorPinA); //lecture de l'amperage 
  
   sensorValueR = (rpm); //lecture vitesse rotation  
   cadre();
      
       
     //affichage ecran batterie
       
      tft.setCursor(5, 7);
      tft.setTextColor(ST7735_GREEN, ST7735_BLACK);
      tft.print("Vbat ");
      tft.setTextColor(ST7735_CYAN, ST7735_BLACK);
      tft.print(sensorValueV / 1023 * 23.9, 2);
      //Serial.print("Vbat");
     // Serial.println(sensorValueV/1023*23.9,2);
      tft.setCursor(5, 20);
       tft.setTextColor(ST7735_GREEN, ST7735_BLACK);
      tft.print("maxV ");
      tft.setTextColor(ST7735_CYAN, ST7735_BLACK);
      tft.print(maxV, 2);
      //Serial.print("Vbatmax");
     // Serial.println(maxV,2);

      //affichage ecran vitesse rotation
      
      tft.setCursor(5, 44);
       tft.setTextColor(ST7735_GREEN, ST7735_BLACK);
      tft.print("V rot");
      tft.setTextColor(ST7735_CYAN, ST7735_BLACK);
     tft.print(sensorValueR);tft.print("  ");
     tft.setCursor(5, 57);
    tft.setTextColor(ST7735_GREEN, ST7735_BLACK);
      tft.print("maxR ");
      tft.setTextColor(ST7735_CYAN, ST7735_BLACK);
      tft.print(maxR, 0);
    

     
       //affichage ecran Thrust
      tft.setCursor(5, 80);
      tft.setTextColor(ST7735_GREEN, ST7735_BLACK);
      tft.print("Thrust:");
      tft.setTextColor(ST7735_CYAN, ST7735_BLACK);
      tft.print(thrust, 1);
      tft.print(" g");

      tft.setTextColor(ST7735_CYAN, ST7735_BLACK);
      tft.setCursor(5, 95);
      tft.setTextColor(ST7735_GREEN, ST7735_BLACK);
      tft.print("T max ");
       tft.setTextColor(ST7735_CYAN, ST7735_BLACK);
      tft.print(maxT, 0);tft.print("  ");
      
     
      
      courbeA();
       

      //affichage ecran Amperage Amperage = lecture Ax/22.5 selon etalonnage capteur
       tft.setCursor(5, 115);
       tft.setTextColor(ST7735_GREEN, ST7735_BLACK);
      tft.print("A Act:");
      tft.setTextColor(ST7735_CYAN, ST7735_BLACK);
      tft.print ((sensorValueA / 22.5), 1);
      Serial.print("#");
      Serial.println(thrust, 1);
      Serial.print("");
      Serial.println(sensorValueR);
      Serial.print("%");
      Serial.println((sensorValueA / 22.5), 1);
      tft.setTextColor(ST7735_CYAN, ST7735_BLACK);
      tft.print(" ");
      tft.setCursor(5, 130);
      tft.setTextColor(ST7735_GREEN, ST7735_BLACK);
      tft.print("Amax:");
      tft.setTextColor(ST7735_CYAN, ST7735_BLACK);
      tft.print(maxA, 1);
      tft.setTextColor(ST7735_CYAN, ST7735_BLACK);
     
     
      
       //affichage ecran puissance max
       watts = (sensorValueA / 22.5) * (sensorValueV / 1023 * 23.9);
      tft.setCursor(5, 148);
      tft.setTextColor(ST7735_GREEN, ST7735_BLACK);
      tft.print("watts  ");
      tft.setTextColor(ST7735_CYAN, ST7735_BLACK);
     tft.print(watts);
     tft.setTextColor(ST7735_GREEN, ST7735_BLACK);
     tft.print("    max  ");
      tft.setTextColor(ST7735_CYAN, ST7735_BLACK);
      tft.print(maxW);
      tft.print(" ");
      
     maxiR();
     maxiA();
     maxiV();
     maxiT();
     maximumW();
    
      rev = 0;
  attachInterrupt(0, isr, RISING); //tachymetre
}

void cadre() {
  // affichage ecran
       //cadre
       tft.drawLine(0,0,130,0,ST7735_RED);
       tft.drawLine(0,1,130,1,ST7735_RED);
       tft.drawLine(0,158,130,158,ST7735_RED);
       tft.drawLine(0,142,130,142,ST7735_RED);
       tft.drawLine(0,141,130,141,ST7735_RED);
       tft.drawLine(0,107,130,107,ST7735_RED);
       tft.drawLine(0,108,130,108,ST7735_RED);
       
       tft.drawLine(80,1,80,140,ST7735_RED);
       tft.drawLine(81,1,81,140,ST7735_RED);
 
       tft.drawLine(0,159,130,159,ST7735_RED);
        tft.drawLine(0,0,0,156,ST7735_RED);
       tft.drawLine(1,1,1,157,ST7735_RED);
       tft.drawLine(127,0,127,156,ST7735_RED);
       tft.drawLine(126,0,126,156,ST7735_RED);
       tft.drawLine(0,35,130,35,ST7735_RED);
       tft.drawLine(0,36,130,36,ST7735_RED);
       tft.drawLine(0,70,130,70,ST7735_RED);
       tft.drawLine(0,71,130,71,ST7735_RED);
       
}

void courbeA() {


  float nouvelleValeurA;
  float nouvelleValeurV;
  float nouvelleValeurT;
  float nouvelleValeurR;

  // converison Ampere voltage et thrust en pixel
  nouvelleValeurA = map((sensorValueA / 22.5), 0, 8, 137, 110); // car l'cran a 64 pixels de haut
  nouvelleValeurV = map((sensorValueV / 1023 * 23.9), 0, 20, 33, 3); // car l'cran a 64 pixels de haut
  nouvelleValeurT = map(scale.get_units(5), 0, 400, 104, 72); // car l'cran a 64 pixels de haut
  nouvelleValeurR = map(rpm, 0, 30000, 68, 40); // car l'cran a 64 pixels de haut

  
  x++;
 
  tft.drawPixel(x, nouvelleValeurA, ST7735_CYAN);
  tft.drawPixel(x, nouvelleValeurV, ST7735_CYAN);
  tft.drawPixel(x, nouvelleValeurT, ST7735_CYAN);
  tft.drawPixel(x, nouvelleValeurR, ST7735_CYAN);
  
  if (x > 123) {
    x = 80;
    tft.fillRect(82, 110, 43, 30, ST7735_BLACK);
    tft.fillRect(82, 1, 43, 33, ST7735_BLACK);
    tft.fillRect(82, 72, 43, 35, ST7735_BLACK);
    tft.fillRect(82, 38, 43, 33, ST7735_BLACK);
  }
}

void maxiV() {
  highV = (sensorValueV / 1023 * 23.9);
  if (highV > maxV) {
    maxV = highV;
  }
}

void maxiA() {
  highA = (sensorValueA / 22.5);
  if (highA > maxA) {
    maxA = highA;
  }
}

void maxiR() {
  highR = (rpm);
  if (highR > maxR) {
    maxR = highR;
  }
}

void maximumW() {
  highW = (watts);
  if (highW > maxW) {
    maxW = highW;
  }
}

void maxiT() {
  highT = scale.get_units(5);
  if (highT > maxT) {
    maxT = highT;
  }
}

void setMotorSpeed(int speed) {
  speed = constrain(speed, 0, 100);  // Ensure speed is between 0 and 100
  int pwmValue = map(speed, 0, 100, PWM_MIN, PWM_MAX);  // Map 0-100% to 1100-1900μs
  esc.writeMicroseconds(pwmValue);
  Serial.print("Motor speed adjusted to ");
  Serial.print(speed);
  Serial.println("%");
}

void processCommand(String command) {
  command.trim();
  if (command.length() > 1) {
    char cmd = command.charAt(0);
    if (cmd == 'S' || cmd == 's') {
      int index = command.charAt(1) - '0';
      if (index >= 0 && index < NUM_SPEED_OPTIONS) {
        targetSpeed = SPEED_OPTIONS[index];
        Serial.print("Target motor speed set to ");
        Serial.print(targetSpeed);
        Serial.println("%");
      }
    } else if (cmd == 'R' || cmd == 'r') {
      Serial.print("Current motor speed: ");
      Serial.print(currentSpeed);
      Serial.println("%");
    } else {
      Serial.println("Invalid command. Use S[0-9] to set speed or R to read current speed.");
    }
  }
}

void serialEvent() {
  while (Serial.available()) {
    char inChar = (char)Serial.read();
    inputString += inChar;
    if (inChar == '\n') {
      stringComplete = true;
    }
  }
}