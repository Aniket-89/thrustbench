import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QComboBox
from PyQt5.QtCore import Qt, QTimer

class ThrustbenchGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DA ThrustBench console")
        self.setGeometry(100, 100, 800, 600)  # Adjusted height for new labels
        self.showMaximized()

        self.serial_port = None
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # COM port selection
        self.port_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.refresh_ports()
        self.port_combo.setFixedWidth(120)  # Set a fixed width for the combo box
        self.port_layout.addWidget(QLabel("COM Port:"))
        self.port_layout.addWidget(self.port_combo)
        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.connect_button.setFixedSize(100, 30)  # Set fixed size for the button
        self.connect_button.clicked.connect(self.connect_serial)
        self.port_layout.addWidget(self.connect_button)

        # Align the layout to the start
        self.port_layout.setAlignment(Qt.AlignLeft)  # Align items to the left  
        self.layout.addLayout(self.port_layout)

        # Measurements display

        self.h_layout = QHBoxLayout()
        self.h_layout.setSpacing(20)
        self.h_layout.setAlignment(Qt.AlignCenter)

        layout_style = "padding: 20; border: 1px solid brown; font-size: 18px; font-weight: 500;"
        label_style = "font-size: 16px; font-weight: 400;"
        # Thrust Layout
        thrust_label = QLabel("Thrust(in g)")
        thrust_label.setStyleSheet(label_style)

        self.thrust_layout = QVBoxLayout()
        self.thrust_display = QLabel("0")
        self.thrust_display.setFixedSize(100, 100)
        self.thrust_display.setStyleSheet(layout_style)
        
        self.thrust_layout.addWidget(self.thrust_display)
        self.thrust_layout.addWidget(thrust_label)

        # RPM layout
        rpm_label = QLabel("RPM")
        rpm_label.setStyleSheet(label_style)
        self.rpm_layout = QVBoxLayout()
        self.rpm_display = QLabel("0")
        
        self.rpm_layout.addWidget(self.rpm_display)
        self.rpm_layout.addWidget(rpm_label)

        # Current Layout
        current_label = QLabel("Current(in A)")
        current_label.setStyleSheet(label_style)
        self.current_layout = QVBoxLayout()
        self.current_display = QLabel("0")
        
        self.current_layout.addWidget(self.current_display)
        self.current_layout.addWidget(current_label)

        # Throttle Layout
        throttle_label = QLabel("Current(in A)")
        throttle_label.setStyleSheet(label_style)
        self.throttle_layout = QVBoxLayout()
        self.throttle_display = QLabel("0")
        
        self.throttle_layout.addWidget(self.throttle_display)
        self.throttle_layout.addWidget(throttle_label)

        # Temp layout
        temp_label = QLabel("Temperature(in C)")
        temp_label.setStyleSheet(label_style)
        self.temp_layout = QVBoxLayout()
        self.temp_display = QLabel("0")
        
        self.temp_layout.addWidget(self.temp_display)
        self.temp_layout.addWidget(temp_label)

        self.h_layout.addLayout(self.current_layout)
        self.h_layout.addLayout(self.rpm_layout)
        self.h_layout.addLayout(self.thrust_layout)
        self.h_layout.addLayout(self.throttle_layout)
        self.h_layout.addLayout(self.temp_layout)
        
        self.layout.addLayout(self.h_layout)
        
        # Motor speed control
        self.speed_label = QLabel("Motor Speed: 0%")
        self.layout.addWidget(self.speed_label)

        # Speed buttons
        speed_button_layout = QHBoxLayout()
        for i in range(10):
            speed = (i + 1) * 10
            button = QPushButton(f"{speed}%")
            button.setStyleSheet("background-color: #f5c700; color: white; width: 80; height: 30;")
            button.clicked.connect(lambda _, s=i: self.set_motor_speed(s))
            speed_button_layout.addWidget(button)
        self.layout.addLayout(speed_button_layout)

        # Stop button
        self.stop_button = QPushButton("STOP")
        self.stop_button.setStyleSheet("background-color: red; color: white; font-weight: bold;")
        self.stop_button.clicked.connect(self.stop_motor)
        self.layout.addWidget(self.stop_button)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(100)  # Update every 100ms

    def refresh_ports(self):
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.addItems(ports)

    def connect_serial(self):
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None
            self.connect_button.setText("Connect")
            self.port_combo.setEnabled(True)
        else:
            try:
                port = self.port_combo.currentText()
                self.serial_port = serial.Serial(port, 57600, timeout=1)
                self.connect_button.setText("Disconnect")
                self.port_combo.setEnabled(False)
                print(f"Connected to {port}")
            except serial.SerialException as e:
                print(f"Error connecting to {port}: {e}")

    def set_motor_speed(self, value):
        if self.serial_port:
            command = f"{value}\n"
            self.serial_port.write(command.encode())
            self.speed_label.setText(f"Motor Speed: {(value+1)*10}%")

    def stop_motor(self):
        if self.serial_port:
            command = "S\n"
            self.serial_port.write(command.encode())
            self.speed_label.setText("Motor Speed: 0%")

    def update_data(self):
        if self.serial_port and self.serial_port.in_waiting:
            try:
                line = self.serial_port.readline().decode('utf-8', errors='replace').strip()
                self.parse_data(line)
            except Exception as e:
                print(f"Error reading serial data: {e}")

    def parse_data(self, data):
        try:
            # Check if the data starts with "Throttle", which indicates it's sensor data
            if data.startswith("Throttle"):
                # Split the data by commas
                parts = data.split(",")

                # Ensure the correct number of parts is available before parsing
                if len(parts) >= 7:
                    # Parse individual values from the data
                    throttle = float(parts[0].split("Throttle")[1].strip())
                    rpm = int(parts[1].split(":")[1].strip())
                    pulse_count = int(parts[2].split(":")[1].strip())
                    thrust = float(parts[3].split(":")[1].strip())
                    current = float(parts[4].split(":")[1].strip())
                    ambient_temp = float(parts[5].split(":")[1].strip())
                    object_temp = float(parts[6].split(":")[1].strip())

                    # Update the labels in the GUI with the parsed data
                    self.rpm_display.setText(f"{rpm}")
                    self.thrust_display.setText(f"{thrust:.2f}")
                    self.current_display.setText(f"{current:.2f}")
                    self.throttle_display.setText(f"{throttle}")
                    self.temp_display.setText(f"{object_temp}")
                else:
                    print(f"Incomplete data received: {data}")
            elif "Motor speed adjusted to" in data:
                # Parse motor speed adjustment message
                speed_str = data.split("to")[-1].strip().rstrip("%")
                try:
                    speed = int(speed_str)
                    self.speed_label.setText(f"Motor Speed: {speed}%")
                except ValueError:
                    print(f"Invalid speed value: {speed_str}")
            elif data == "Motor stopped":
                self.speed_label.setText("Motor Speed: 0%")
            elif data == "Stopping motor gradually":
                self.speed_label.setText("Motor Speed: Stopping...")
            elif any(keyword in data for keyword in ["Initializing", "IR Sensor Test", "Calibrating", "Voltage offset", "Current offset"]):
                # Handle setup messages
                print(f"Setup message: {data}")
            else:
                # Handle unhandled data messages
                print(f"Unhandled data: {data}")
        except Exception as e:
            print(f"Error parsing data '{data}': {e}")


    def closeEvent(self, event):
        if self.serial_port:
            self.stop_motor()  # Ensure motor is stopped when closing the application
            self.serial_port.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ThrustbenchGUI()
    window.show()
    sys.exit(app.exec_())
