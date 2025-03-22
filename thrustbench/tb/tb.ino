#include <Servo.h>
#include "HX711.h"
#include <Wire.h>
#include <Adafruit_MLX90614.h>

// Pin Configurations
const int ESC_PIN = 9;           // PWM pin for ESC control
const int LOADCELL_DOUT_PIN = 26;
const int LOADCELL_SCK_PIN = 24;
const int CURRENT_SENSOR_PIN = A0;

unsigned long lastDataSendTime = 0;
const unsigned long DATA_SEND_INTERVAL = 1000; // 1 second

// Motor Control Parameters
Servo esc;
const int PWM_MIN = 1050;
const int PWM_MAX = 1950;
int currentSpeed = 0;
int targetSpeed = 0;

// Speed Ramping Configuration
const int SPEED_INCREMENT = 5;
const unsigned long RAMP_DELAY = 75;
unsigned long lastRampTime = 0;

// Sensor Configurations
HX711 scale;
Adafruit_MLX90614 mlx = Adafruit_MLX90614();

// Current Sensor Parameters
const float VOLTAGE_REFERENCE = 5.0;
const float CURRENT_SENSITIVITY = 0.065;
float currentOffset = 0.0;

// String for Serial Command
String inputString = "";
bool stringComplete = false;

void setup() {
  Serial.begin(57600);
  
  // ESC Setup
  esc.attach(ESC_PIN, PWM_MIN, PWM_MAX);
  esc.writeMicroseconds(PWM_MIN);
  // delay(5000);  // ESC initialization delay

  // Load Cell Setup
  scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
  scale.set_scale(74);  // Calibration factor
  scale.tare();

  // Current Sensor Setup
  pinMode(CURRENT_SENSOR_PIN, INPUT);

  // Temperature Sensor Setup
  if (!mlx.begin()) {
    Serial.println("MLX sensor error. Check wiring.");
    while(1);
  }

  // Calibrate Current Sensor
  currentOffset = measureCurrentOffset();
  
  Serial.println("Thrust Stand Ready");
}

float measureCurrentOffset() {
  long sum = 0;
  for (int i = 0; i < 1000; i++) {
    sum += analogRead(CURRENT_SENSOR_PIN);
    // delay(1);
  }
  float avgReading = sum / 1000.0;
  return (avgReading / 1023.0 * VOLTAGE_REFERENCE) - (VOLTAGE_REFERENCE / 2);
}

float readCurrent() {
  long sum = 0;
  for (int i = 0; i < 10; i++) {
    sum += analogRead(CURRENT_SENSOR_PIN);
    // delay(1);
  }

  float voltage = (sum / 10.0 / 1023.0) * VOLTAGE_REFERENCE;
  float current = (voltage - (VOLTAGE_REFERENCE / 2) - currentOffset) / CURRENT_SENSITIVITY;
  
  return abs(current) < 0.1 ? 0.0 : current;
}

void loop() {
  unsigned long currentTime = millis();

  // Periodic Data Collection
  if (currentTime - lastDataSendTime >= DATA_SEND_INTERVAL) {
    float thrust = scale.get_units(20);
    float current = readCurrent() - currentOffset;
    float ambientTemp = mlx.readAmbientTempC();
    float objectTemp = mlx.readObjectTempC();
    float throttle = calculateThrottle(esc.readMicroseconds());

    // Serial Output
    Serial.print("Throttle:");
    Serial.print(throttle, 2);
    Serial.print(",Thrust:");
    Serial.print(thrust, 1);
    Serial.print(",Current:");
    Serial.print(current, 2);
    Serial.print(",AmbientTemp:");
    Serial.print(ambientTemp, 1);
    Serial.print(",ObjectTemp:");
    Serial.print(objectTemp, 1);
    Serial.println();
    lastDataSendTime = currentTime;
  }

  // Handle Serial Commands
  if (stringComplete) {
    processCommand(inputString);
    inputString = "";
    stringComplete = false;
  }

  // Speed Ramping
  if (currentSpeed != targetSpeed && millis() - lastRampTime >= RAMP_DELAY) {
    adjustMotorSpeed();
  }
}

void adjustMotorSpeed() {
  if (currentSpeed > targetSpeed) {
    currentSpeed = max(currentSpeed - SPEED_INCREMENT, targetSpeed);
  } else {
    currentSpeed = min(currentSpeed + SPEED_INCREMENT, targetSpeed);
  }
  setMotorSpeed(currentSpeed);
  lastRampTime = millis();

  if (currentSpeed == 0 && targetSpeed == 0) {
    Serial.println("Motor Stopped");
  }
}

float calculateThrottle(int pwmValue) {
  return map(pwmValue, PWM_MIN, PWM_MAX, 0, 100);
}

void setMotorSpeed(int speed) {
  speed = constrain(speed, 0, 100);
  int pwmValue = map(speed, 0, 100, PWM_MIN, PWM_MAX);
  esc.writeMicroseconds(pwmValue);
}

void processCommand(String command) {
  command.trim();
  
  if (command.endsWith("%")) {
    command.remove(command.length() - 1);
    int percentage = command.toInt();
    
    if (percentage >= 0 && percentage <= 100) {
      targetSpeed = percentage;
      Serial.print("Target speed: ");
      Serial.print(targetSpeed);
      Serial.println("%");
    } else {
      Serial.println("Invalid speed. Use 0-100%");
    }
  } else if (command.length() == 1) {
    char cmd = command.charAt(0);
    switch (cmd) {
      case 'R':
      case 'r':
        Serial.print("Current speed: ");
        Serial.print(currentSpeed);
        Serial.println("%");
        break;
      case 'S':
      case 's':
        stopMotor();
        break;
      case 'T':
      case 't':
        performTare();
        break;
      default:
        printHelp();
    }
  }
}

void stopMotor() {
  targetSpeed = 0;
  Serial.println("Stopping motor");
}

void performTare() {
  if (currentSpeed > 0) {
    Serial.println("Stop motor before taring");
    return;
  }
  
  scale.tare();
  Serial.println("Scale zeroed");
}

void printHelp() {
  Serial.println("Commands:");
  Serial.println("T: Tare scale");
  Serial.println("0-100%: Set speed");
  Serial.println("R: Read speed");
  Serial.println("S: Stop motor");
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