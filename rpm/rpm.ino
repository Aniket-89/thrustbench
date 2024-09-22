const int IR_SENSOR_PIN = 48;  // Digital pin 48 for IR sensor input

volatile unsigned long lastDetectionTime = 0;
volatile unsigned long revolutions = 0;
unsigned long lastRpmCalcTime = 0;
unsigned int rpm = 0;

// Debug variables
unsigned long lastDebugTime = 0;
const unsigned long DEBUG_INTERVAL = 100; // Print debug info every 100ms

void setupIRSensor() {
  pinMode(IR_SENSOR_PIN, INPUT_PULLUP);
  attachInterrupt(digitalPinToInterrupt(IR_SENSOR_PIN), countRevolution, FALLING);
  Serial.println("IR proximity sensor initialized for RPM measurement");
}

void countRevolution() {
  unsigned long currentTime = micros();
  if (currentTime - lastDetectionTime > 1000) { // Debounce: ignore detections within 1ms
    revolutions++;
    lastDetectionTime = currentTime;
  }
}

void calculateRPM() {
  unsigned long currentTime = millis();
  if (currentTime - lastRpmCalcTime >= 1000) { // Calculate RPM every second
    noInterrupts(); // Disable interrupts to safely read volatile variables
    unsigned long revs = revolutions;
    revolutions = 0;
    interrupts(); // Re-enable interrupts

    rpm = revs * 60; // Revolutions per minute
    lastRpmCalcTime = currentTime;

    Serial.print("RPM: ");
    Serial.println(rpm);
  }
}

void printDebugInfo() {
  unsigned long currentTime = millis();
  if (currentTime - lastDebugTime >= DEBUG_INTERVAL) {
    lastDebugTime = currentTime;
    
    Serial.print("Debug - Sensor state: ");
    Serial.print(digitalRead(IR_SENSOR_PIN) == LOW ? "Detected" : "Not detected");
    Serial.print(", Revolutions: ");
    Serial.print(revolutions);
    Serial.print(", Time since last detection: ");
    Serial.print(micros() - lastDetectionTime);
    Serial.println(" us");
  }
}

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB
  }
  setupIRSensor();
  Serial.println("RPM measurement system ready. Attach sensor to motor and start rotation.");
}

void loop() {
  calculateRPM();
  printDebugInfo();
}
