#include <Servo.h>

// Motor speed reading
const int MOTOR_SPEED_PIN = 2;  // Digital pin 2 for motor speed input
volatile unsigned long pulseCount = 0;
unsigned long lastTime = 0;
unsigned int rpm = 0;

// Motor control
const int ESC_PIN = 9;  // PWM pin for ESC control
Servo esc;
int currentSpeed = 0;    // Start at 0%
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

void setup() {
  Serial.begin(9600);

  // Debugging: Setup start message
  Serial.println("Setup started");

  // Set up motor speed reading
  pinMode(MOTOR_SPEED_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(MOTOR_SPEED_PIN), countPulse, RISING);

  // Debugging: ESC setup
  Serial.println("Initializing ESC...");
  
  // Set up ESC control
  esc.attach(ESC_PIN, PWM_MIN, PWM_MAX);  // Attach ESC with 1100-1900μs range
  esc.writeMicroseconds(PWM_MIN);  // Set to minimum speed
  delay(5000);  // Wait for ESC to initialize

  // Debugging: ESC setup complete
  Serial.println("ESC initialized. Motor is static. Waiting for commands...");

  // Print available commands
  Serial.println("Motor control commands:");
  Serial.println("0-9: Set motor speed (10% to 100%)");
  Serial.println("R: Read current motor speed");
}

void loop() {
  // Handle serial commands
  if (stringComplete) {
    Serial.print("Processing command: ");
    Serial.println(inputString);  // Debugging: Print command received
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }

  // Gradual speed adjustment
  if (currentSpeed != targetSpeed && millis() - lastRampTime >= RAMP_DELAY) {
    Serial.print("Adjusting motor speed: ");  // Debugging: Speed adjustment process
    Serial.print("Current: ");
    Serial.print(currentSpeed);
    Serial.print("%, Target: ");
    Serial.print(targetSpeed);
    Serial.println("%");

    if (currentSpeed < targetSpeed) {
      currentSpeed = min(currentSpeed + SPEED_INCREMENT, targetSpeed);
    } else {
      currentSpeed = max(currentSpeed - SPEED_INCREMENT, targetSpeed);
    }

    setMotorSpeed(currentSpeed);
    lastRampTime = millis();
  }

  // Calculate and update RPM every second
  if (millis() - lastTime >= 1000) {
    detachInterrupt(digitalPinToInterrupt(MOTOR_SPEED_PIN));

    // Debugging: RPM calculation
    Serial.println("Calculating RPM...");

    // Calculate RPM (adjust 'pulsesPerRevolution' based on your motor/sensor)
    const int pulsesPerRevolution = 2;  // Example: 2 pulses per revolution
    rpm = (pulseCount * 60) / pulsesPerRevolution;
    
    // Reset pulse count and reattach interrupt
    pulseCount = 0;
    lastTime = millis();
    attachInterrupt(digitalPinToInterrupt(MOTOR_SPEED_PIN), countPulse, RISING);

    // Debugging: RPM output
    Serial.print("RPM: ");
    Serial.println(rpm);
  }
}

void countPulse() {
  pulseCount++;
}

void processCommand(String command) {
  command.trim();
  if (command.length() > 0) {
    char cmd = command.charAt(0);
    if (cmd >= '0' && cmd <= '9') {
      int index = cmd - '0';
      if (index < NUM_SPEED_OPTIONS) {
        targetSpeed = SPEED_OPTIONS[index];

        // Debugging: Target speed set
        Serial.print("Target motor speed set to ");
        Serial.print(targetSpeed);
        Serial.println("%");
      }
    } else if (cmd == 'R' || cmd == 'r') {
      // Debugging: Read current motor speed
      Serial.print("Current motor speed: ");
      Serial.print(currentSpeed);
      Serial.println("%");
    } else {
      // Debugging: Invalid command
      Serial.println("Invalid command. Use 0-9 to set speed or R to read current speed.");
    }
  }
}

void setMotorSpeed(int speed) {
  speed = constrain(speed, 0, 100);  // Ensure speed is between 0 and 100
  int pwmValue = map(speed, 0, 100, PWM_MIN, PWM_MAX);  // Map 0-100% to 1100-1900μs
  esc.writeMicroseconds(pwmValue);

  // Debugging: Motor speed adjusted
  Serial.print("Motor speed adjusted to ");
  Serial.print(speed);
  Serial.println("%");
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
