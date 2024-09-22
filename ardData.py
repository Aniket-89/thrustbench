import serial
import serial.tools.list_ports
import time

def find_arduino_port():
    ports = list(serial.tools.list_ports.comports())
    print("Available ports:")
    for p in ports:
        print(f"- {p.device}: {p.description}")
    
    for p in ports:
        if 'Arduino' in p.description or 'CH340' in p.description:
            return p.device
    return None

def monitor_serial_data(port, baud_rate=9600, timeout=1):
    try:
        with serial.Serial(port, baud_rate, timeout=timeout) as ser:
            print(f"Connected to {port}")
            print("Monitoring serial data (press Ctrl+C to stop):")
            while True:
                if ser.in_waiting:
                    raw_data = ser.readline()
                    try:
                        decoded_data = raw_data.decode('utf-8').strip()
                        print(f"Received: {decoded_data}")
                    except UnicodeDecodeError:
                        print(f"Received (raw): {raw_data}")
                time.sleep(0.1)
    except serial.SerialException as e:
        print(f"Error: {e}")
        print("Make sure the Arduino is connected and no other program is using the port.")

if __name__ == "__main__":
    port = find_arduino_port()
    if port:
        monitor_serial_data(port)
    else:
        print("Arduino not found. Please check the connection and try again.")
        ports = list(serial.tools.list_ports.comports())
        if ports:
            print("\nAvailable ports:")
            for p in ports:
                print(f"- {p.device}: {p.description}")
            port = input("Enter the port name manually (e.g., COM3): ")
            monitor_serial_data(port)
        else:
            print("No COM ports found. Make sure your Arduino is connected.")