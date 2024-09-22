#include <AccelStepper.h>

// Define pin connections for the motors
const int MOTOR1_STEP_PIN = 2;
const int MOTOR1_DIR_PIN = 3;
const int MOTOR2_STEP_PIN = 4;
const int MOTOR2_DIR_PIN = 5;
const int MOTOR3_STEP_PIN = 6;
const int MOTOR3_DIR_PIN = 7;

// Define motor interface type
#define MOTOR_INTERFACE_TYPE 1

// Create instances of AccelStepper for each motor
AccelStepper motor1(MOTOR_INTERFACE_TYPE, MOTOR1_STEP_PIN, MOTOR1_DIR_PIN);
AccelStepper motor2(MOTOR_INTERFACE_TYPE, MOTOR2_STEP_PIN, MOTOR2_DIR_PIN);
AccelStepper motor3(MOTOR_INTERFACE_TYPE, MOTOR3_STEP_PIN, MOTOR3_DIR_PIN);

// Variables for winding parameters
int numStators = 0;
int numLayers = 0;
float statorLength = 0.0;  // in mm

// Constants for motor control
const int STEPS_PER_REVOLUTION = 200;  // Adjust based on your stepper motor
const float WIRE_DIAMETER = 0.5;  // Wire diameter in mm, adjust as needed
const int FEED_STEPS_PER_MM = 100;  // Adjust based on your feed mechanism

// Variables to track winding progress
int currentStator = 0;
int currentLayer = 0;
int currentWinding = 0;
bool windingComplete = false;

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect
  }
  
  // Configure motor settings
  motor1.setMaxSpeed(1000);
  motor1.setAcceleration(500);
  motor2.setMaxSpeed(1000);
  motor2.setAcceleration(500);
  motor3.setMaxSpeed(1000);
  motor3.setAcceleration(500);
  
  Serial.println("Stator winder machine initialized");
  promptForParameters();
}

void loop() {
  if (!windingComplete) {
    windCopper();
    
    if (currentWinding >= calculateWindingsPerLayer()) {
      currentLayer++;
      currentWinding = 0;
      if (currentLayer >= numLayers) {
        currentStator++;
        currentLayer = 0;
        if (currentStator >= numStators) {
          windingComplete = true;
          Serial.println("All stators wound completely.");
        } else {
          Serial.println("Moving to next stator.");
          rotateToNextStator();
        }
      } else {
        Serial.println("Moving to next layer.");
        moveToNextLayer();
      }
    }
  } else {
    Serial.println("Winding process complete. Enter new parameters to start again.");
    delay(5000);
    promptForParameters();
  }
}

void promptForParameters() {
  Serial.println("Enter number of stators:");
  while (Serial.available() == 0) {}
  numStators = Serial.parseInt();
  
  Serial.println("Enter number of layers:");
  while (Serial.available() == 0) {}
  numLayers = Serial.parseInt();
  
  Serial.println("Enter stator length (mm):");
  while (Serial.available() == 0) {}
  statorLength = Serial.parseFloat();
  
  Serial.println("Parameters set. Starting winding process.");
  resetWinding();
}

void windCopper() {
  // Calculate steps for one winding
  int windingSteps = calculateWindingSteps();
  
  // Move winding motor (motor1)
  motor1.move(windingSteps);
  
  // Move feed motor (motor2) to advance wire
  float feedDistance = calculateFeedDistance();
  int feedSteps = feedDistance * FEED_STEPS_PER_MM;
  motor2.move(feedSteps);
  
  // Run both motors simultaneously
  while (motor1.isRunning() || motor2.isRunning()) {
    motor1.run();
    motor2.run();
  }
  
  currentWinding++;
  Serial.print("Completed winding: ");
  Serial.print(currentWinding);
  Serial.print(" of layer ");
  Serial.print(currentLayer + 1);
  Serial.print(" on stator ");
  Serial.println(currentStator + 1);
}

void rotateToNextStator() {
  int rotationSteps = STEPS_PER_REVOLUTION / numStators;
  motor3.move(rotationSteps);
  while (motor3.isRunning()) {
    motor3.run();
  }
  Serial.println("Rotated to next stator");
}

void moveToNextLayer() {
  // Move feed motor back to start position
  float returnDistance = statorLength;
  int returnSteps = returnDistance * FEED_STEPS_PER_MM;
  motor2.move(-returnSteps);
  while (motor2.isRunning()) {
    motor2.run();
  }
  Serial.println("Moved to next layer");
}

void resetWinding() {
  currentStator = 0;
  currentLayer = 0;
  currentWinding = 0;
  windingComplete = false;
  Serial.println("Winding reset. Ready for new cycle.");
}

int calculateWindingsPerLayer() {
  return statorLength / WIRE_DIAMETER;
}

int calculateWindingSteps() {
  // This is a simplified calculation. You may need to adjust this based on your specific setup
  return STEPS_PER_REVOLUTION;
}

float calculateFeedDistance() {
  // This is a simplified calculation. You may need to adjust this based on your specific winding pattern
  return WIRE_DIAMETER;
}

