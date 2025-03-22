// Pin definitions for stepper motors
#define WIND_STEP_PIN 2
#define WIND_DIR_PIN 3
#define WIND_EN_PIN 4

#define FEED_STEP_PIN 5
#define FEED_DIR_PIN 6
#define FEED_EN_PIN 7

#define ROT_STEP_PIN 8
#define ROT_DIR_PIN 9
#define ROT_EN_PIN 10

// Parameters struct to store user inputs
struct WindingParams {
  float windSpeed;      // Steps/second for winding motor
  float feedSpeed;      // Steps/second for feed motor
  float rotSpeed;       // Steps/second for rotation motor
  long windSteps;       // Steps per revolution for winding motor
  long feedSteps;       // Steps per revolution for feed motor
  long rotSteps;        // Steps per revolution for rotation motor
  float gearRatio;      // Gear ratio for winding motor
  bool windDirection;   // true = CW, false = CCW
  int coilsPerSlot;    // Number of coils per slot
  float slotLength;     // Length of stator slot in mm
};

WindingParams params;
const int TOTAL_SLOTS = 12;
// Winding sequence for 12 slots (0-based index)
const int windingSequence[] = {0,1,6,7,2,3,8,9,4,5,10,11};
int currentSlot = 0;

// Function declarations
void setupMotors();
void homeAll();
void windSlot(int slotNum);
void moveFeed(bool forward);
void rotateStator(int slots);
void setMotorSpeed(int motor, float speed);
void executeStep(int stepPin, bool dir);

void setup() {
  Serial.begin(115200);
  setupMotors();
  
  // Default parameters (will be overwritten by GUI)
  params.windSpeed = 1000;
  params.feedSpeed = 500;
  params.rotSpeed = 200;
  params.windSteps = 200;
  params.feedSteps = 200;
  params.rotSteps = 200;
  params.gearRatio = 2.5;
  params.windDirection = true;
  params.coilsPerSlot = 100;
  params.slotLength = 50.0;
  
  homeAll();
}

void loop() {
  if (Serial.available()) {
    // Process commands from GUI
    char cmd = Serial.read();
    switch(cmd) {
      case 'S': // Start winding sequence
        executeWindingSequence();
        break;
      case 'H': // Home all axes
        homeAll();
        break;
      case 'P': // Update parameters
        updateParams();
        break;
      case 'M': // Motor movement command
        handleMotorCommand();
        break;
      case 'E': // Emergency stop
      // Add more commands as needed
    }
  }
}

void setupMotors() {
  // Configure motor pins
  pinMode(WIND_STEP_PIN, OUTPUT);
  pinMode(WIND_DIR_PIN, OUTPUT);
  pinMode(WIND_EN_PIN, OUTPUT);
  
  pinMode(FEED_STEP_PIN, OUTPUT);
  pinMode(FEED_DIR_PIN, OUTPUT);
  pinMode(FEED_EN_PIN, OUTPUT);
  
  pinMode(ROT_STEP_PIN, OUTPUT);
  pinMode(ROT_DIR_PIN, OUTPUT);
  pinMode(ROT_EN_PIN, OUTPUT);
  
  // Enable all motors
  digitalWrite(WIND_EN_PIN, LOW);
  digitalWrite(FEED_EN_PIN, LOW);
  digitalWrite(ROT_EN_PIN, LOW);
}

void homeAll() {
  // Basic homing sequence - would need limit switches in real implementation
  // Move all axes to starting position
  digitalWrite(WIND_DIR_PIN, HIGH);
  digitalWrite(FEED_DIR_PIN, HIGH);
  digitalWrite(ROT_DIR_PIN, HIGH);
  
  // Execute some steps to reach home position
  for(int i = 0; i < 100; i++) {
    digitalWrite(WIND_STEP_PIN, HIGH);
    digitalWrite(FEED_STEP_PIN, HIGH);
    digitalWrite(ROT_STEP_PIN, HIGH);
    delayMicroseconds(500);
    digitalWrite(WIND_STEP_PIN, LOW);
    digitalWrite(FEED_STEP_PIN, LOW);
    digitalWrite(ROT_STEP_PIN, LOW);
    delayMicroseconds(500);
  }
}

void executeWindingSequence() {
  for(int i = 0; i < TOTAL_SLOTS; i++) {
    int slotNum = windingSequence[i];
    windSlot(slotNum);
    
    // After every 4 slots, do 5 complete rotations
    if((i+1) % 4 == 0 && i < TOTAL_SLOTS-1) {
      rotateStator(5);
    }
  }
}

// Replace the existing windSlot function with this updated version

void windSlot(int slotNum) {
    // Determine winding direction based on slot number
    // Even numbered slots (0,2,4..) wind CW, Odd numbered slots (1,3,5..) wind CCW
    bool windDir = (slotNum % 2 == 0);
    
    // If user selected CCW as base direction, invert the direction
    if (!params.windDirection) {
        windDir = !windDir;
    }
    
    // Set winding motor direction
    digitalWrite(WIND_DIR_PIN, windDir);
    
    // Calculate required steps for one slot
    long totalSteps = params.coilsPerSlot * params.windSteps * params.gearRatio;
    
    // Calculate feed movement per winding step
    float feedStepsPerWind = (params.slotLength / params.feedSteps) * params.windSteps;
    
    // Set initial feed direction (starts from center to outside)
    bool feedDir = true;
    digitalWrite(FEED_DIR_PIN, feedDir);
    
    // Move feed to starting position (center of slot)
    moveFeedToStart();
    
    Serial.print("Winding slot "); 
    Serial.print(slotNum + 1);  // Add 1 for 1-based slot numbers
    Serial.print(" Direction: ");
    Serial.println(windDir ? "CW" : "CCW");
    
    // Execute winding sequence
    for(long step = 0; step < totalSteps; step++) {
        // Execute winding step
        executeStep(WIND_STEP_PIN, windDir);
        
        // Synchronize feed movement with winding
        if(step % (long)feedStepsPerWind == 0) {
            executeStep(FEED_STEP_PIN, feedDir);
            
            // Check if we need to reverse feed direction
            if (checkFeedEndpoint()) {
                feedDir = !feedDir;
                digitalWrite(FEED_DIR_PIN, feedDir);
            }
        }
        
        delayMicroseconds(1000000/params.windSpeed);
    }
    
    // Generate clearance between winder and stator
    createClearance();
    
    // Rotate to next position if not last slot
    if(slotNum < TOTAL_SLOTS - 1) {
        rotateToNextSlot(slotNum);
    }
}

// Add these new helper functions

void moveFeedToStart() {
    // Move feed to center position
    digitalWrite(FEED_DIR_PIN, true);  // Move inward
    
    // Execute steps to reach center (half of slot length)
    long centeringSteps = (params.slotLength * params.feedSteps) / 2;
    for(long i = 0; i < centeringSteps; i++) {
        executeStep(FEED_STEP_PIN, true);
        delayMicroseconds(1000000/params.feedSpeed);
    }
}

bool checkFeedEndpoint() {
    // In a real implementation, this would check limit switches
    // For now, we'll use a calculated position
    static long currentFeedPosition = 0;
    static long maxFeedPosition = params.slotLength * params.feedSteps;
    
    currentFeedPosition++;
    if(currentFeedPosition >= maxFeedPosition) {
        currentFeedPosition = 0;
        return true;
    }
    return false;
}

void createClearance() {
    // Move feed outward to create clearance
    digitalWrite(FEED_DIR_PIN, false);
    long clearanceSteps = params.feedSteps * 2;  // Adjust clearance distance as needed
    
    for(long i = 0; i < clearanceSteps; i++) {
        executeStep(FEED_STEP_PIN, false);
        delayMicroseconds(1000000/params.feedSpeed);
    }
}

void rotateToNextSlot(int currentSlot) {
    // Calculate steps needed to reach next slot in sequence
    int currentIndex = 0;
    int nextIndex = 0;
    
    // Find current slot position in sequence
    for(int i = 0; i < TOTAL_SLOTS; i++) {
        if(windingSequence[i] == currentSlot) {
            currentIndex = i;
            nextIndex = (i + 1) % TOTAL_SLOTS;
            break;
        }
    }
    
    // Calculate shortest path to next slot
    int slotDiff = windingSequence[nextIndex] - windingSequence[currentIndex];
    if(abs(slotDiff) > TOTAL_SLOTS/2) {
        // Take shorter path around the stator
        slotDiff = (slotDiff > 0) ? slotDiff - TOTAL_SLOTS : slotDiff + TOTAL_SLOTS;
    }
    
    // Execute rotation
    bool rotDir = (slotDiff > 0);
    digitalWrite(ROT_DIR_PIN, rotDir);
    
    long stepsToMove = abs(slotDiff) * (params.rotSteps / TOTAL_SLOTS);
    for(long i = 0; i < stepsToMove; i++) {
        executeStep(ROT_STEP_PIN, rotDir);
        delayMicroseconds(1000000/params.rotSpeed);
    }
}

void moveFeed(bool forward) {
  digitalWrite(FEED_DIR_PIN, forward);
  for(int i = 0; i < params.feedSteps; i++) {
    executeStep(FEED_STEP_PIN, forward);
    delayMicroseconds(1000000/params.feedSpeed);
  }
}

// void rotateStator(int slots) {
//   long steps = slots * params.rotSteps;
//   for(long i = 0; i < steps; i++) {
//     executeStep(ROT_STEP_PIN, true);
//     delayMicroseconds(1000000/params.rotSpeed);
//   }
// }
void handleMotorCommand() {
    String data = Serial.readStringUntil('\n');
    String parts[5];  // M,motor,direction,speed,steps
    int partCount = 0;
    
    // Parse command
    int startIndex = 0;
    for(int i = 0; i < data.length() && partCount < 5; i++) {
        if(data.charAt(i) == ',') {
            parts[partCount] = data.substring(startIndex, i);
            startIndex = i + 1;
            partCount++;
        }
    }
    if(startIndex < data.length()) {
        parts[partCount] = data.substring(startIndex);
        partCount++;
    }
    
    if(partCount != 5) {
        Serial.println("Invalid motor command format");
        return;
    }
    
    // Extract parameters
    char motor = parts[1].charAt(0);
    bool direction = parts[2].toInt() == 1;
    int speed = parts[3].toInt();
    long steps = parts[4].toInt();
    
    // Set up pins based on motor
    int stepPin, dirPin;
    switch(motor) {
        case 'W':  // Winding motor
            stepPin = WIND_STEP_PIN;
            dirPin = WIND_DIR_PIN;
            break;
        case 'F':  // Feed motor
            stepPin = FEED_STEP_PIN;
            dirPin = FEED_DIR_PIN;
            break;
        case 'R':  // Rotation motor
            stepPin = ROT_STEP_PIN;
            dirPin = ROT_DIR_PIN;
            break;
        default:
            Serial.println("Invalid motor specified");
            return;
    }
    
    // Set direction
    digitalWrite(dirPin, direction);
    
    // Execute movement
    for(long i = 0; i < steps; i++) {
        digitalWrite(stepPin, HIGH);
        delayMicroseconds(10);
        digitalWrite(stepPin, LOW);
        delayMicroseconds(1000000/speed - 10);
        
        // Check for stop command
        if(Serial.available()) {
            String cmd = Serial.readStringUntil('\n');
            if(cmd.startsWith("S,") && cmd.charAt(2) == motor) {
                break;
            }
        }
    }
    
    Serial.print("Completed moving motor ");
    Serial.println(motor);
}

void executeStep(int stepPin, bool dir) {
  digitalWrite(stepPin, HIGH);
  delayMicroseconds(10);
  digitalWrite(stepPin, LOW);
  delayMicroseconds(10);
}

// Add these to the existing Arduino code

void updateParams() {
  if (Serial.available()) {
    String data = Serial.readStringUntil('\n');
    
    // Split the received string by commas
    int paramCount = 0;
    int lastCommaIndex = 0;
    float values[10];  // Array to store the parsed values
    
    // Parse the comma-separated values
    for (int i = 0; i < data.length(); i++) {
      if (data.charAt(i) == ',') {
        if (paramCount > 0) {  // Skip the first 'P' character
          String valueStr = data.substring(lastCommaIndex + 1, i);
          values[paramCount - 1] = valueStr.toFloat();
        }
        lastCommaIndex = i;
        paramCount++;
      }
    }
    
    // Update parameters if we received the correct number
    if (paramCount == 11) {  // 10 parameters plus the initial 'P'
      params.windSpeed = values[0];
      params.feedSpeed = values[1];
      params.rotSpeed = values[2];
      params.windSteps = (long)values[3];
      params.feedSteps = (long)values[4];
      params.rotSteps = (long)values[5];
      params.gearRatio = values[6];
      params.windDirection = (bool)values[7];
      params.coilsPerSlot = (int)values[8];
      params.slotLength = values[9];
      
      // Send confirmation
      Serial.println("Parameters updated successfully");
    } else {
      Serial.println("Error: Invalid parameter count");
    }
  }
}

// Add this to the existing loop() function case statement
case 'E': // Emergency Stop
  // Disable all motors
  digitalWrite(WIND_EN_PIN, HIGH);
  digitalWrite(FEED_EN_PIN, HIGH);
  digitalWrite(ROT_EN_PIN, HIGH);
  break;