import sys
import serial
import time
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QSlider
from PyQt5.QtCore import Qt, QTimer

class ThrustbenchGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thrustbench Control")
        self.setGeometry(100, 100, 600, 400)

        self.serial_port = serial.Serial('COM6', 57600, timeout=1)  # Adjust COM port as needed
        time.sleep(2)  # Wait for Arduino to initialize

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Measurements display
        self.thrust_label = QLabel("Thrust: 0 g")
        self.rpm_label = QLabel("RPM: 0")
        self.voltage_label = QLabel("Voltage: 0 V")
        self.current_label = QLabel("Current: 0 A")
        self.power_label = QLabel("Power: 0 W")

        self.layout.addWidget(self.thrust_label)
        self.layout.addWidget(self.rpm_label)
        self.layout.addWidget(self.voltage_label)
        self.layout.addWidget(self.current_label)
        self.layout.addWidget(self.power_label)

        # Motor speed control
        self.speed_label = QLabel("Motor Speed: 0%")
        self.layout.addWidget(self.speed_label)

        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setMinimum(0)
        self.speed_slider.setMaximum(9)
        self.speed_slider.valueChanged.connect(self.set_motor_speed)
        self.layout.addWidget(self.speed_slider)

        # Speed buttons
        speed_button_layout = QHBoxLayout()
        for i in range(10):
            speed = (i + 1) * 10
            button = QPushButton(f"{speed}%")
            button.clicked.connect(lambda _, s=i: self.set_motor_speed(s))
            speed_button_layout.addWidget(button)
        self.layout.addLayout(speed_button_layout)

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(100)  # Update every 100ms

    def set_motor_speed(self, value):
        command = f"S{value}\n"
        self.serial_port.write(command.encode())
        self.speed_label.setText(f"Motor Speed: {(value+1)*10}%")

    def update_data(self):
        if self.serial_port.in_waiting:
            line = self.serial_port.readline().decode('utf-8').strip()
            self.parse_data(line)

    def parse_data(self, data):
        if data.startswith("Thrust:"):
            thrust = float(data.split(":")[1].strip().rstrip("g"))
            self.thrust_label.setText(f"Thrust: {thrust:.2f} g")
        elif data.startswith("RPM:"):
            rpm = int(data.split(":")[1].strip())
            self.rpm_label.setText(f"RPM: {rpm}")
        elif data.startswith("Voltage:"):
            voltage = float(data.split(":")[1].strip().rstrip("V"))
            self.voltage_label.setText(f"Voltage: {voltage:.2f} V")
        elif data.startswith("Current:"):
            current = float(data.split(":")[1].strip().rstrip("A"))
            self.current_label.setText(f"Current: {current:.2f} A")
        elif data.startswith("Power:"):
            power = float(data.split(":")[1].strip().rstrip("W"))
            self.power_label.setText(f"Power: {power:.2f} W")

    def closeEvent(self, event):
        self.serial_port.close()
        event.accept()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ThrustbenchGUI()
    window.show()
    sys.exit(app.exec_())