#include <Arduino.h>

// Define the pin for the Hall effect current sensor
const int HALL_CURRENT_SENSOR_PIN = A0;  // Analog pin A0 for Hall current sensor input

void setup() {
  Serial.begin(57600);
  
  // Debug: Serial connection initialization
  while (!Serial) {
    ; // Wait for serial port to connect (useful for native USB boards)
  }
  
  // Debug: Initializing Hall effect sensor
  Serial.println("Initializing Hall effect current sensor...");

  // Set up Hall effect current sensor
  pinMode(HALL_CURRENT_SENSOR_PIN, INPUT);
  
  // Debug: Sensor initialized successfully
  Serial.println("Hall effect current sensor initialized.");
}

void loop() {
  // Debug: Start reading sensor value
  Serial.println("Reading sensor value...");
  
  // Read the raw sensor value
  int readA0 = analogRead(HALL_CURRENT_SENSOR_PIN);
  
  // Debug: Print the raw sensor value
  Serial.print("Raw sensor value (A0): ");
  Serial.println(readA0);
  
  // Debug: Start calculating current
  Serial.println("Calculating current...");

  // Calculate current using the provided formula
  int current = (readA0 - 505) * 78 / 512;
  
  // Debug: Print the calculated current value
  Serial.print("Calculated current: ");
  Serial.print(current);  // Current value is now an integer
  Serial.println(" A");
  
  // Debug: Delay before next reading
  Serial.println("Waiting 1 second before the next reading...");
  
  delay(1000);  // Update every second
}
