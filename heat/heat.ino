#include <Wire.h>
#include <Adafruit_MLX90614.h>

// Create an instance of the MLX90614 sensor
Adafruit_MLX90614 mlx = Adafruit_MLX90614();

void setup() {
  Serial.begin(57600);
  
  // Initialize communication with the sensor
  if (!mlx.begin()) {
    Serial.println("Error connecting to MLX90614 sensor. Check wiring.");
    while (1);  // Stay here if the sensor isn't found
  }

  Serial.println("MLX90614 sensor initialized successfully!");
}

void loop() {
  // Read ambient (room) temperature
  float ambientTemp = mlx.readAmbientTempC();
  
  // Read object (target) temperature
  float objectTemp = mlx.readObjectTempC();

  // Debug: Print the temperatures to the serial monitor
  Serial.print("Ambient temperature: ");
  Serial.print(ambientTemp);
  Serial.println(" °C");

  Serial.print("Object temperature: ");
  Serial.print(objectTemp);
  Serial.println(" °C");
  
  // Wait for 1 second before taking the next reading
  delay(1000);
}
