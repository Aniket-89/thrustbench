#include "HX711.h"

// Pin configuration for the load cell
#define LOADCELL_DOUT_PIN  4
#define LOADCELL_SCK_PIN   5

HX711 scale;

void setup() {
    Serial.begin(9600);
    scale.begin(LOADCELL_DOUT_PIN, LOADCELL_SCK_PIN);
    scale.tare(); // Tare the scale
}

void loop() {
    long rawReading = scale.get_units(10); // Average of 10 readings
    float calibrationFactor = 112.03; // Replace with your actual calibration factor
    float weight = rawReading / calibrationFactor;

    Serial.println(weight, 2); // Send weight to serial with 2 decimal places
    delay(1000); // Read every second
}
