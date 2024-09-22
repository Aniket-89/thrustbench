import serial
import time

arduino = serial.Serial('COM7', baudrate=9600, timeout=1)

time.sleep(2)

try:
    while True:
        if arduino.in_waiting > 0:
            data = arduino.readline().decode('utf-8').strip()
            print(data)
        time.sleep(0.1)
except KeyboardInterrupt:
    print("Program terminated by user")
finally:
    arduino.close()
