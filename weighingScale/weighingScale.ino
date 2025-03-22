#include "HX711.h"

// Pin configuration for the load cell
#define LOADCELL_DOUT_PIN  4
#define LOADCELL_SCK_PIN   5

HX711 scale;

void setup() {
    Serial.begin(9600);
    scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
    
    // Tare the scale
    scale.tare();
    Serial.println("Taring complete. Place a known weight on the scale.");
    delay(2000); // Wait for 2 seconds before reading
}

void loop() {
    // Get raw reading
    long rawReading = scale.get_units(10); // Average of 10 readings
    Serial.print("Raw reading: ");
    Serial.println(rawReading);
    
    // Convert to weight in grams (use your calibration factor)
    float calibrationFactor = 112.03; // Replace with your actual calibration factor
    float weight = rawReading / calibrationFactor;

    Serial.print("Weight: ");
    Serial.print(weight, 2); // Show weight with 2 decimal places
    Serial.println(" g");
    
    delay(1000); // Read every second
}
