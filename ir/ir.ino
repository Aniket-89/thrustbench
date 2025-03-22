// Pin configuration
const int sensorPin = 9;  // Digital pin connected to the "out" pin of the sensor
int sensorState = 0;       // Variable to store the sensor state (HIGH or LOW)
int lastState = HIGH;       // Variable to store the last state of the sensor
unsigned long debounceDelay = 100;  // Debounce time in milliseconds
unsigned long lastDebounceTime = 0;

void setup() {
  // Initialize the serial communication
  Serial.begin(9600);
  
  // Configure the sensor pin as an input
  pinMode(sensorPin, INPUT);
}

void loop() {
  // Read the sensor's state (HIGH or LOW)
  int reading = digitalRead(sensorPin);

  // If the sensor reading has changed (due to noise or an object)
  if (reading != lastState) {
    lastDebounceTime = millis();  // Reset the debounce timer
  }

  // Check if enough time has passed to take a stable reading
  if ((millis() - lastDebounceTime) > debounceDelay) {
    // If the sensor state has stabilized
    if (reading != sensorState) {
      sensorState = reading;

      // Print the sensor state
      if (sensorState == LOW) {
        Serial.println("Object detected!");
      } else {
        Serial.println("No object detected.");
      }
    }
  }

  // Update the last sensor reading
  lastState = reading;

  // Small delay to avoid too frequent readings
  delay(100);
}
