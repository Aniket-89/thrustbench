#include <Servo.h>
#include "HX711.h"
#include <Arduino.h>
#include <Wire.h>
#include <Adafruit_MLX90614.h>

// Motor control
const int ESC_PIN = 9;  // PWM pin for ESC control
Servo esc;
int currentSpeed = 0;
int targetSpeed = 0;

// Add these constants for motor speed options
const int SPEED_OPTIONS[] = {10, 20, 30, 40, 50, 60, 70, 80, 90, 100};
const int NUM_SPEED_OPTIONS = 10;

// Speed ramping parameters
const int SPEED_INCREMENT = 1;  // Speed increment per step
const unsigned long RAMP_DELAY = 75;  // Delay between speed increments (milliseconds)
unsigned long lastRampTime = 0;

// PWM signal range
const int PWM_MIN = 1050;
const int PWM_MAX = 1950;

// Serial command handling
String inputString = "";
bool stringComplete = false;

// HX711 circuit wiring
const int LOADCELL_DOUT_PIN = 26;
const int LOADCELL_SCK_PIN = 24;

HX711 scale;

// WSC1700 Hall effect current sensor configuration (70A version)
const int HALL_CURRENT_SENSOR_PIN = A0;  // Analog pin A0 for Hall current sensor input
const float VOLTAGE_REFERENCE = 5.0;  // Reference voltage of Arduino Mega
const float SENSITIVITY = 0.025;  // Sensitivity of WCS1700 (25mV/A for 70A version)

float voltageOffset = 0.0;  // Will be set during calibration

// MLXC90214 temperature sensor
Adafruit_MLX90614 mlx = Adafruit_MLX90614();

// IR Proximity Sensor for RPM measurement
const int IR_SENSOR_PIN = 39;  // Make sure this is the correct pin
unsigned long lastRpmTime = 0;
unsigned long pulseCount = 0;
unsigned int rpm = 0;

float currentOffset = 0.0;

void setup() {
  Serial.begin(57600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB
  }

  // Set up ESC control
  esc.attach(ESC_PIN, PWM_MIN, PWM_MAX);  // Attach ESC with 1100-1900μs range
  esc.writeMicroseconds(PWM_MIN);  // Set to minimum speed
  delay(5000);  // Wait for ESC to initialize

  // Set up load cell
  Serial.println("Initializing the scale");
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  Serial.println("Scale begin complete");
  scale.set_scale(-112.756);  // This value is obtained by calibrating the scale with known weights
  Serial.println("Scale factor set");

  scale.tare();               // Reset the scale to 0
  Serial.println("Tare complete");

  // Set up Hall effect current sensor
  pinMode(HALL_CURRENT_SENSOR_PIN, INPUT);

  // Set up MLXC90214 temperature sensor
  if (!mlx.begin()) {
    Serial.println("Error connecting to MLX sensor. Check wiring.");
    while (1);
  }
  Serial.println("MLXC90214 infrared temperature sensor initialized");

  Serial.println("Thrustbench ready");
  Serial.println("Motor control commands:");
  Serial.println("0-9: Set motor speed (10% to 100%)");
  Serial.println("R: Read current motor speed");
  Serial.println("S: Stop motor");
  Serial.println("X: Run motor speed sequence from 20% to 100%");

  // Set up IR proximity sensor for RPM measurement
  pinMode(IR_SENSOR_PIN, INPUT_PULLUP);

  Serial.println("IR Sensor Test: Reading sensor state...");

  // Uncomment or add this line
  calibrateSensor();
  
  // Additional software calibration
  currentOffset = readCurrent();
  Serial.print("Current offset: ");
  Serial.println(currentOffset, 3);
}

void calibrateSensor() {
  Serial.println("Calibrating sensor (ensure no current is flowing)...");
  long sum = 0;
  for (int i = 0; i < 1000; i++) {
    sum += analogRead(HALL_CURRENT_SENSOR_PIN);
    delay(1);
  }
  float avgReading = sum / 1000.0;
  voltageOffset = (avgReading / 1023.0 * VOLTAGE_REFERENCE) - (VOLTAGE_REFERENCE / 2);
  
  // Adjust for the persistent offset (average of about -1.27A from your readings)
  voltageOffset += 1.27 * SENSITIVITY;
  
  Serial.print("Voltage offset: ");
  Serial.println(voltageOffset, 3);
}

float readCurrent() {
  long sum = 0;
  for (int i = 0; i < 10; i++) {  // Average 10 readings
    sum += analogRead(HALL_CURRENT_SENSOR_PIN);
    delay(1);
  }
  float avgReading = sum / 10.0;
  float voltage = (avgReading / 1023.0) * VOLTAGE_REFERENCE;
  float current = (voltage - (VOLTAGE_REFERENCE / 2) - voltageOffset) / SENSITIVITY;
  return current;
}

void loop() {
  // Poll the sensor
  static int lastState = LOW;  // Changed from HIGH to LOW
  int currentState = digitalRead(IR_SENSOR_PIN);
  
  // Changed condition to detect rising edge instead of falling edge
  if (currentState == HIGH && lastState == LOW) {
    pulseCount++;
  }
  lastState = currentState;

  // Calculate and update RPM, thrust, current, and temperature every second
  if (millis() - lastRpmTime >= 1000) {
    // Calculate RPM
    rpm = calculateRPM();
    
    // Read thrust from load cell
    float thrust = scale.get_units(10);  // Average of 5 readings
    
    // Read current from Hall effect sensor and apply offset
    float current = readCurrent() - currentOffset;
    if (abs(current) < 0.1) {  // Adjust this threshold as needed
        current = 0;
    }
    
    // Read temperatures from MLXC90214 sensor
    float ambientTemp = mlx.readAmbientTempC();
    float objectTemp = mlx.readObjectTempC();
    
    float throttle = calculateThrottle(esc.readMicroseconds());

    // Print RPM, thrust, current, and temperatures
    Serial.print("Throttle: ");
    Serial.print(throttle);
    Serial.print(",Thrust:");
    Serial.print(thrust, 1);  // Remove the "g" unit here
    Serial.print(",RPM:");
    Serial.print(rpm);
    // Serial.print(",PulseCount:");
    // Serial.print(pulseCount);
    Serial.print(",Current:");
    Serial.print(current, 2);
    Serial.print(",AmbientTemp:");
    Serial.print(ambientTemp, 1);
    Serial.print(",ObjectTemp:");
    Serial.print(objectTemp, 1);
    Serial.println();  // Add a newline at the end

    // Reset pulse count and update last RPM time
    pulseCount = 0;
    lastRpmTime = millis();
  }

  // Handle serial commands
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }

  // Gradual speed adjustment (including stopping)
  if (currentSpeed != targetSpeed && millis() - lastRampTime >= RAMP_DELAY) {
    if (currentSpeed > targetSpeed) {
      currentSpeed = max(currentSpeed - SPEED_INCREMENT, targetSpeed);
    } else {
      currentSpeed = min(currentSpeed + SPEED_INCREMENT, targetSpeed);
    }
    setMotorSpeed(currentSpeed);
    lastRampTime = millis();
    
    // Print a message when the motor has fully stopped
    if (currentSpeed == 0 && targetSpeed == 0) {
      Serial.println("Motor stopped");
    }
  }
}

float calculateThrottle(int pwmValue) {
  float throttle = map(pwmValue, PWM_MIN, PWM_MAX, 0, 100);
  return throttle;
}

unsigned int calculateRPM() {
  unsigned long currentTime = millis();
  unsigned long elapsedTime = currentTime - lastRpmTime;
  
  // Calculate RPM based on pulse count and elapsed time
  // This assumes one pulse per revolution - adjust if needed
  unsigned int calculatedRPM = (pulseCount * 60000UL) / elapsedTime;
  
  return calculatedRPM;
}

void processCommand(String command) {
  command.trim();
  if (command.length() > 0) {
    char cmd = command.charAt(0);
    if (cmd >= '0' && cmd <= '9') {
      int index = cmd - '0';
      if (index < NUM_SPEED_OPTIONS) {
        targetSpeed = SPEED_OPTIONS[index];
        Serial.print("Target motor speed set to ");
        Serial.print(targetSpeed);
        Serial.println("%");
      }
    } else if (cmd == 'R' || cmd == 'r') {
      Serial.print("Current motor speed: ");
      Serial.print(currentSpeed);
      Serial.println("%");
    } else if (cmd == 'S' || cmd == 's') {
      targetSpeed = 0;
      Serial.println("Stopping motor...");
    } else if (cmd == 'X' || cmd == 'x') {
      Serial.println("Starting motor speed sequence from 20% to 100%...");
      runSpeedSequence();
    } else {
      Serial.println("Invalid command");
    }
  }
}

void runSpeedSequence() {
  int speedSteps[] = {20, 25, 30, 35, 40, 45, 50, 55, 60};
  int numSteps = sizeof(speedSteps) / sizeof(speedSteps[0]);
  
  for (int i = 0; i < numSteps; i++) {
    targetSpeed = speedSteps[i];
    Serial.print("Setting motor speed to ");
    Serial.print(targetSpeed);
    Serial.println("%");
    
    // Wait for motor to reach the target speed
    while (currentSpeed != targetSpeed) {
      // Do nothing, let the ramping logic handle the gradual change
      delay(100);
    }
    
    // Wait for 1 minute (60,000 ms) at this speed
    delay(60000);
  }

  // Stop motor after sequence is complete
  targetSpeed = 0;
  Serial.println("Motor speed sequence complete. Motor stopped.");
}

void setMotorSpeed(int speed) {
  int pwmValue = map(speed, 0, 100, PWM_MIN, PWM_MAX);
  esc.writeMicroseconds(pwmValue);
}
