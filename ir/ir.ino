// Define the pin for the IR proximity sensor
#define IR_SENSOR_PIN A0

void setupIRSensor() {
  pinMode(IR_SENSOR_PIN, INPUT);
  Serial.println("IR proximity sensor initialized");
}

int readIRSensor() {
  return analogRead(IR_SENSOR_PIN);
}

float convertToDistance(int sensorValue) {
  // This conversion is an approximation and may need calibration
  // for your specific sensor and environment
  float voltage = sensorValue * (5.0 / 1023.0);
  return 27.86 * pow(voltage, -1.15);
}

void printIRData() {
  int rawValue = readIRSensor();
  float distance = convertToDistance(rawValue);
  
  Serial.print("IR Sensor Raw Value: ");
  Serial.print(rawValue);
  Serial.print(", Estimated Distance: ");
  Serial.print(distance);
  Serial.println(" cm");
}

// Call this function in your main setup()
void setupIR() {
  setupIRSensor();
}

// Call this function in your main loop() to read and print IR data
void updateIR() {
  printIRData();
  delay(100); // Adjust delay as needed
}


