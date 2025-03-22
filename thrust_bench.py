import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QComboBox
from PyQt5.QtGui import QPixmap, QFontDatabase, QFont
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import time

class ThrustbenchGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        # Load Google font from the local file
        font_id = QFontDatabase.addApplicationFont("Orbitron-Regular.ttf")
        if font_id == -1:
            print("Failed to load the font!")
        else:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            print(f"Loaded font: {font_family}")

        # Set the font to be used in the app
        custom_font = QFont(font_family, 16)  # Set font size to 18



        self.setWindowTitle("DA ThrustBench console")
        self.setGeometry(100, 100, 800, 600)
        self.showMaximized()

        self.serial_port = None
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)

        # Data storage for the temperature vs. time graph
        self.time_data = []  # No fixed limit
        self.temp_data = []
        self.start_time = time.time()

        # COM port selection
        self.port_layout = QHBoxLayout()
        self.port_combo = QComboBox()
        self.refresh_ports()
        self.port_combo.setFixedWidth(120)
        self.port_layout.addWidget(QLabel("COM Port:"))
        self.port_layout.addWidget(self.port_combo)
        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.connect_button.setFixedSize(100, 30)
        self.connect_button.clicked.connect(self.connect_serial)
        self.port_layout.addWidget(self.connect_button)

        self.port_layout.setAlignment(Qt.AlignLeft)
        self.layout.addLayout(self.port_layout)

        # Measurements display
        self.h_layout = QHBoxLayout()
        self.h_layout.setSpacing(20)
        self.h_layout.setAlignment(Qt.AlignCenter)

        layout_style = "padding: 20; border: 1px solid brown; font-size: 18px; font-weight: 500;"
        label_style = "font-size: 16px; font-weight: 600; text-align: center;"
        thrust_label = QLabel("Thrust(in g)")
        thrust_label.setStyleSheet(label_style)

        self.thrust_layout = QVBoxLayout()
        self.thrust_display = QLabel("0")
        self.thrust_display.setFont(custom_font)
        self.thrust_display.setFixedSize(100, 100)
        self.thrust_display.setStyleSheet(layout_style)
        
        self.thrust_layout.addWidget(self.thrust_display)
        self.thrust_layout.addWidget(thrust_label)

        rpm_label = QLabel("RPM")
        rpm_label.setStyleSheet(label_style)
        self.rpm_layout = QVBoxLayout()
        self.rpm_display = QLabel("0")
        self.rpm_display.setFont(custom_font)

        self.rpm_display.setFixedSize(100, 100)
        self.rpm_display.setStyleSheet(layout_style)
        
        self.rpm_layout.addWidget(self.rpm_display)
        self.rpm_layout.addWidget(rpm_label)

        current_label = QLabel("Current(in A)")
        current_label.setStyleSheet(label_style)
        self.current_layout = QVBoxLayout()
        self.current_display = QLabel("0")
        self.current_display.setFont(custom_font)

        self.current_display.setFixedSize(100, 100)
        self.current_display.setStyleSheet(layout_style)
        
        self.current_layout.addWidget(self.current_display)
        self.current_layout.addWidget(current_label)

        throttle_label = QLabel("Throttle")
        throttle_label.setStyleSheet(label_style)
        self.throttle_layout = QVBoxLayout()
        self.throttle_display = QLabel("0")
        self.throttle_display.setFont(custom_font)

        self.throttle_display.setFixedSize(100, 100)
        self.throttle_display.setStyleSheet(layout_style)
        
        self.throttle_layout.addWidget(self.throttle_display)
        self.throttle_layout.addWidget(throttle_label)

        temp_label = QLabel("Temp. (in C)")
        temp_label.setStyleSheet(label_style)
        self.temp_layout = QVBoxLayout()
        self.temp_display = QLabel("0")
        self.temp_display.setFont(custom_font)

        self.temp_display.setFixedSize(100, 100)
        self.temp_display.setStyleSheet(layout_style)
        
        self.temp_layout.addWidget(self.temp_display)
        self.temp_layout.addWidget(temp_label)

        self.h_layout.addLayout(self.current_layout)
        self.h_layout.addLayout(self.rpm_layout)
        self.h_layout.addLayout(self.thrust_layout)
        self.h_layout.addLayout(self.throttle_layout)
        self.h_layout.addLayout(self.temp_layout)
        
        self.layout.addLayout(self.h_layout)
        
        # Real-time Plot Layout
        self.plot_layout = QHBoxLayout()

        # Create a plot widget for temperature vs. time
        self.temp_plot = pg.PlotWidget(title="Temperature vs Time")
        self.temp_plot.setLabel('left', 'Temperature (°C)')
        self.temp_plot.setLabel('bottom', 'Time (s)')
        self.temp_plot.addLegend()
        self.temp_plot.setYRange(0, 100)
        self.temp_plot.setMouseEnabled(x=False, y=False)
        self.temp_curve = self.temp_plot.plot(pen='r', name="Object Temp")

        # Create a plot widget for current vs. time
        self.current_plot = pg.PlotWidget(title="Current vs Time")
        self.current_plot.setLabel('left', 'Current (A)')
        self.current_plot.setLabel('bottom', 'Time (s)')
        self.current_plot.addLegend()

        # Disable zooming
        self.current_plot.setMouseEnabled(x=False, y=False)

        self.current_curve = self.current_plot.plot(pen='b', name="Current")

        self.plot_layout.addWidget(self.temp_plot)
        self.plot_layout.addWidget(self.current_plot)
        self.layout.addLayout(self.plot_layout)

        # Motor speed control
        self.speed_label = QLabel("Motor Speed: 0%")
        self.speed_label.setFixedSize(200, 40)
        self.speed_label.setStyleSheet("background-color: #ff77ff; font-size: 18px; font-weight: 500; height: 40; border-radius: 5px; border: 1px solid gray;")
        self.layout.addWidget(self.speed_label)

        speed_button_layout = QHBoxLayout()
        for i in range(10):
            speed = (i + 1) * 10
            button = QPushButton(f"{speed}%")
            button.setStyleSheet("background-color: #f5c700; color: white; width: 80; height: 30; font-size: 18px; font-weight: 500; border-radius: 5px;")
            button.clicked.connect(lambda _, s=i: self.set_motor_speed(s))
            speed_button_layout.addWidget(button)
        self.layout.addLayout(speed_button_layout)

        self.bottom_layout = QHBoxLayout()
        self.stop_button = QPushButton("STOP")
        self.stop_button.setFixedSize(80, 80)
        self.stop_button.setStyleSheet("background-color: red; color: white; font-size: 20px; font-weight: bold; border-radius: 40px;")
        self.stop_button.clicked.connect(self.stop_motor)

        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignRight)
        self.logo_pixmap = QPixmap("p-logo.jpg")  # Update with the path to your logo
        self.logo_label.setPixmap(self.logo_pixmap.scaled(300, 200, Qt.KeepAspectRatio))
        self.bottom_layout.addWidget(self.stop_button)
        self.bottom_layout.addWidget(self.logo_label)

        self.layout.addLayout(self.bottom_layout)

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
            if data.startswith("Throttle"):
                parts = data.split(",")
                if len(parts) >= 7:
                    throttle = float(parts[0].split("Throttle")[1].strip())
                    rpm = int(parts[1].split(":")[1].strip())
                    pulse_count = int(parts[2].split(":")[1].strip())
                    thrust = float(parts[3].split(":")[1].strip())
                    current = float(parts[4].split(":")[1].strip())
                    ambient_temp = float(parts[5].split(":")[1].strip())
                    object_temp = float(parts[6].split(":")[1].strip())
                    
                    self.throttle_display.setText(str(throttle))
                    self.rpm_display.setText(str(rpm))
                    self.thrust_display.setText(str(thrust))
                    self.current_display.setText(str(current))
                    self.temp_display.setText(str(object_temp))

                    # Calculate elapsed time
                    current_time = time.time() - self.start_time
                    self.time_data.append(current_time)

                    # Append data for both temperature and current
                    self.temp_data.append(object_temp)
                    self.current_data.append(current)

                    # Update the temperature vs time graph
                    self.temp_curve.setData(self.time_data, self.temp_data)

                    # Update the current vs time graph
                    self.current_curve.setData(self.time_data, self.current_data)

                    # Dynamically adjust X-axis to scroll with time
                    if len(self.time_data) > 1:
                        self.temp_plot.setXRange(self.time_data[-1] - 10, self.time_data[-1], padding=0)
                        self.current_plot.setXRange(self.time_data[-1] - 10, self.time_data[-1], padding=0)

        except Exception as e:
            print(f"Error parsing data: {e}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    gui = ThrustbenchGUI()
    gui.show()
    sys.exit(app.exec_())
