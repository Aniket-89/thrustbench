const int SENSOR_PIN = A0;  // Analog pin A0 for current sensor input

const int SAMPLES = 100;  // Number of samples for calibration
const float REFERENCE_CURRENT = 0.1;  // Known reference current in Amperes

float offset = 0;
float gain = 1;

void setup() {
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect
  }
  
  pinMode(SENSOR_PIN, INPUT);
  
  Serial.println("Current Sensor Calibration");
  Serial.println("Please ensure a known reference current is flowing.");
  Serial.println("Press any key to start calibration...");
  while (!Serial.available()) {}
  Serial.read();  // Clear the input buffer
  
  calibrateSensor();
  
  Serial.println("Calibration complete.");
  Serial.print("Offset: ");
  Serial.println(offset, 6);
  Serial.print("Gain: ");
  Serial.println(gain, 6);
}

void loop() {
  float current = readCurrent();
  Serial.print("Calibrated Current: ");
  Serial.print(current, 3);
  Serial.println(" A");
  delay(1000);
}

void calibrateSensor() {
  long sum = 0;
  
  // Collect samples
  for (int i = 0; i < SAMPLES; i++) {
    sum += readRawCurrent();
    delay(10);
  }
  
  // Calculate average
  float avgRaw = (float)sum / SAMPLES;
  
  // Calculate offset and gain
  offset = avgRaw;
  gain = REFERENCE_CURRENT / (avgRaw - offset);
  
  Serial.println("Calibration values calculated.");
}

int readRawCurrent() {
  return analogRead(SENSOR_PIN);
}

float readCurrent() {
  int rawReading = readRawCurrent();
  float current = (rawReading - offset) * gain;
  return current;
}
