#include <AccelStepper.h>

// Define pins for stepper motors
#define WIND_STEP_PIN 2
#define WIND_DIR_PIN 4
#define FEED_STEP_PIN 10
#define FEED_DIR_PIN 12
#define ROT_STEP_PIN 6
#define ROT_DIR_PIN 8

// Initialize stepper motors
AccelStepper windingMotor(1, WIND_STEP_PIN, WIND_DIR_PIN);
AccelStepper feedMotor(1, FEED_STEP_PIN, FEED_DIR_PIN);
AccelStepper rotatorMotor(1, ROT_STEP_PIN, ROT_DIR_PIN);

void setup() {
  Serial.begin(9600);

  // Set max speed and acceleration
  windingMotor.setMaxSpeed(3200);
  windingMotor.setAcceleration(400);
  feedMotor.setMaxSpeed(1000);
  feedMotor.setAcceleration(200);
  rotatorMotor.setMaxSpeed(1000);
  rotatorMotor.setAcceleration(200);
};

void loop() {
  windingMotor.move(5 * 1600);
  feedMotor.move(200);
  windingMotor.run();
  feedMotor.run();

  // step 1
  // home all motors
  
  // step 2
  // winding motor 5 turns

  // step 3
  // feed motor wire width backward

  // step 4
  // repeat step 2 and3 till the feed is equal to the length of the slot

  // step 5 
  // reverse the feed direction and repeat the step 2 and step3 till the remaining coil is wound

  // step 6 
  // run the feed motor for the remaining length of the slot

  // step 7
  // the rotational motor turn 1/no. of slot turn
};