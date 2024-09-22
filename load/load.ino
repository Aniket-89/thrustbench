#include "HX711.h"

// Define the pins for HX711
#define DT_PIN 26
#define SCK_PIN 24

HX711 scale;

void setup() {
  Serial.begin(9600);
  scale.begin(DT_PIN, SCK_PIN);

  Serial.println("HX711 Calibration");
  Serial.println("Initializing...");

  // Load cell calibration
  scale.set_scale(); // Adjust this value as needed for your load cell
  scale.tare();  // Reset the scale to 0

  Serial.println("Calibration complete.");
  Serial.println("Place a known weight on the scale.");
}

void loop() {
  // Read the weight from the load cell
  float weight = scale.get_units(10); // Average of 10 readings

  // Print the weight to the Serial Monitor
  Serial.print("Weight: ");
  Serial.print(weight);
  Serial.println(" grams");

  delay(1000); // Wait 1 second before the next reading
}
