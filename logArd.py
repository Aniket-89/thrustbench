import serial
import csv
import time
from datetime import datetime

# Serial port configuration
SERIAL_PORT = 'COM3'  # Change this to match your Arduino's port
BAUD_RATE = 57600

# File configuration
OUTPUT_FILE = 'thrust_data.csv'

def main():
    try:
        # Open serial connection
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to {SERIAL_PORT}")

        # Open CSV file
        with open(OUTPUT_FILE, 'w', newline='') as csvfile:
            csvwriter = csv.writer(csvfile)
            
            # Write header
            csvwriter.writerow(['Timestamp', 'Reading Type', 'Value'])

            print(f"Saving data to {OUTPUT_FILE}")
            print("Press Ctrl+C to stop...")

            while True:
                if ser.in_waiting:
                    # Read line from serial
                    line = ser.readline().decode('utf-8').strip()
                    
                    # Parse the line
                    if line.startswith("one reading:"):
                        reading_type = "Single"
                        value = line.split("\t")[1]
                    elif line.startswith("| average:"):
                        reading_type = "Average"
                        value = line.split("\t")[1]
                    else:
                        continue  # Skip other lines

                    # Get current timestamp
                    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S.%f")

                    # Write to CSV
                    csvwriter.writerow([timestamp, reading_type, value])
                    csvfile.flush()  # Ensure data is written immediately

                    # Print to console
                    print(f"{timestamp} - {reading_type}: {value}")

    except serial.SerialException as e:
        print(f"Error opening serial port: {e}")
    except KeyboardInterrupt:
        print("\nStopping data collection...")
    finally:
        if 'ser' in locals():
            ser.close()
        print("Data collection ended.")

if __name__ == "__main__":
    main()
