import sys
import serial
import serial.tools.list_ports
from PyQt5.QtWidgets import (QApplication, QDialog, QLineEdit, QMessageBox,
                             QMainWindow, QVBoxLayout, QHBoxLayout,
                             QWidget, QPushButton, QLabel, QComboBox)
from PyQt5.QtGui import QPixmap, QFontDatabase, QFont
from PyQt5.QtCore import Qt, QTimer
import pyqtgraph as pg
import time
import os
import requests


class LoginDialog(QDialog):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Login")

        # Create the widgets
        self.email_input = QLineEdit()
        self.email_input.setPlaceholderText("Email")
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.Password)
        self.login_button = QPushButton("Login")
        self.login_button.clicked.connect(self.login)

        # Create the layout
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Email:"))
        layout.addWidget(self.email_input)
        layout.addWidget(QLabel("Password:"))
        layout.addWidget(self.password_input)
        layout.addWidget(self.login_button)

        self.setLayout(layout)

    def login(self):
        email = self.email_input.text()
        password = self.password_input.text()

        response = requests.post("http://127.0.0.1:8000/api/login/", data={"email": email, "password": password})

        if response.status_code == 200:
            QMessageBox.information(self, "Success", "Login successful!")
            self.accept()
        else:
            QMessageBox.warning(self, "Error", response.json().get("message"))


class ThrustbenchGUI(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("DA ThrustBench console")
        self.setGeometry(0, 0, 1920, 1080)
 
        font_path = os.path.join(
            os.path.dirname(__file__), 'Orbitron-Regular.ttf'
            )
        logo_path = os.path.join(
            os.path.dirname(__file__), 'logo.png'
                )

        font_id = QFontDatabase.addApplicationFont(font_path)
        if font_id == -1:
            print("Failed to load the font!")
        else:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            print(f"Loaded font: {font_family}")

        # Set the font to be used in the app
        custom_font = QFont(font_family, 16)  # Set font size to 18

        self.serial_port = None
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QHBoxLayout(self.central_widget)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        self.layout.setStretch(0, 3)
        self.layout.setStretch(1, 7)

        # Data storage for the temperature vs. time graph
        self.time_data = []  # No fixed limit
        self.temp_data = []
        self.current_data = []
        self.thrust_data = []
        self.throttle_data = []
        self.start_time = time.time()

        # variables
        left_panel_bg = "#ffd000"
        left_bottom_bg = "#ffd000"
        main_bg = "#eddea4"

        self.left_panel_widget = QWidget()
        self.left_panel_widget.setMaximumWidth(500)

        # Left panel layout
        self.left_panel_layout = QVBoxLayout()
        self.left_panel_layout.setContentsMargins(0, 10, 0, 0)
        self.left_panel_layout.setAlignment(Qt.AlignCenter)

        # Set the layout to the widget
        self.left_panel_widget.setLayout(self.left_panel_layout)
        self.left_panel_widget.setStyleSheet(f"background-color: {left_panel_bg};")

        # COM port selection
        self.port_layout = QHBoxLayout()
        self.port_layout.setSpacing(0)
        self.port_layout.setContentsMargins(10, 0, 10, 0)
        self.port_combo = QComboBox()
        self.refresh_ports()
        self.port_combo.setFixedSize(150, 30)
        self.port_combo.setStyleSheet("background-color: #fbb02d;")
        self.connect_button = QPushButton("Connect")
        self.connect_button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 18px;")
        self.connect_button.setFixedSize(80, 30)
        self.connect_button.clicked.connect(self.connect_serial)


        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignLeft)
        self.logo_pixmap = QPixmap(logo_path)  # Update with the path to your logo
        self.logo_label.setPixmap(self.logo_pixmap.scaled(180, 80, Qt.KeepAspectRatio))
        self.port_layout.addWidget(self.logo_label)
        self.port_layout.addWidget(self.port_combo)
        self.port_layout.addWidget(self.connect_button)

        # self.port_layout.setAlignment(Qt.AlignLeft)
        self.left_panel_layout.addLayout(self.port_layout)

        # Measurements display
        self.h_layout = QVBoxLayout()
        self.h_layout.setSpacing(20)
        self.h_layout.setAlignment(Qt.AlignCenter)

        layout_style = "padding: 20; border: 1px solid white; font-size: 22px; font-weight: 500; background-color: black; color: #39FF14;"
        label_style = "font-size: 18px; font-weight: 600; text-align: center; color: black;"

        thrust_label = QLabel("Thrust (in g)")
        thrust_label.setStyleSheet(label_style)
        thrust_label.setFont(custom_font)

        self.thrust_layout = QHBoxLayout()
        self.thrust_display = QLabel("0")
        self.thrust_display.setFont(custom_font)
        self.thrust_display.setFixedSize(200, 100)
        self.thrust_display.setStyleSheet(layout_style)
        
        self.thrust_layout.addWidget(self.thrust_display)
        self.thrust_layout.addWidget(thrust_label)

        # Add a QLabel for displaying the timer
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setFont(custom_font)
        self.timer_label.setFixedSize(200, 100)
        self.timer_label.setStyleSheet(layout_style)
        self.h_layout.addWidget(self.timer_label)

        # Add attributes for the timer
        self.start_time = None
        self.elapsed_time = 0  # To track frozen time when the motor stops
        self.is_motor_running = False  # Flag to track motor state

        # Timer to update the motor data
        self.data_timer = QTimer(self)
        self.data_timer.timeout.connect(self.update_data)
        self.data_timer.start(100)  # Update motor data every 100ms

        # Timer to update the timer label
        self.display_timer = QTimer(self)
        self.display_timer.timeout.connect(self.update_timer_display)
        self.display_timer.start(1000)  # Update the display every second

        current_label = QLabel("Current (in A)")
        current_label.setStyleSheet(label_style)
        current_label.setFont(custom_font)

        self.current_layout = QHBoxLayout()
        self.current_display = QLabel("0")
        self.current_display.setFont(custom_font)

        self.current_display.setFixedSize(200, 100)
        self.current_display.setStyleSheet(layout_style)
        
        self.current_layout.addWidget(self.current_display)
        self.current_layout.addWidget(current_label)

        throttle_label = QLabel("Throttle")
        throttle_label.setFont(custom_font)
        throttle_label.setStyleSheet(label_style)
        self.throttle_layout = QHBoxLayout()
        self.throttle_display = QLabel("0")
        self.throttle_display.setFont(custom_font)
        
        self.throttle_display.setFixedSize(200, 100)
        self.throttle_display.setStyleSheet(layout_style)
        
        self.throttle_layout.addWidget(self.throttle_display)
        self.throttle_layout.addWidget(throttle_label)

        temp_label = QLabel("Temp. (in C)")
        temp_label.setStyleSheet(label_style)
        temp_label.setFont(custom_font)

        self.temp_layout = QHBoxLayout()
        self.temp_display = QLabel("0")
        self.temp_display.setFont(custom_font)

        self.temp_display.setFixedSize(200, 100)
        self.temp_display.setStyleSheet(layout_style)
        
        self.temp_layout.addWidget(self.temp_display)
        self.temp_layout.addWidget(temp_label)

        self.h_layout.addLayout(self.current_layout)
        # self.h_layout.addLayout(self.rpm_layout)
        self.h_layout.addLayout(self.thrust_layout)
        self.h_layout.addLayout(self.throttle_layout)
        self.h_layout.addLayout(self.temp_layout)

        self.bottom_layout_widget = QWidget()
        self.bottom_layout = QHBoxLayout()

        self.bottom_layout_widget.setLayout(self.bottom_layout)
        self.bottom_layout_widget.setStyleSheet(f"background-color: {left_bottom_bg};")
        self.bottom_layout.setAlignment(Qt.AlignLeft)

        self.speed_input_layout = QVBoxLayout()
        self.speed_input_layout.setAlignment(Qt.AlignLeft)
        
        # Create a QLineEdit for user input
        self.speed_input = QLineEdit()
        self.speed_input.setFixedSize(120, 60)  # Set size as needed
        self.speed_input.setFont(custom_font)
        self.speed_input.setStyleSheet("background-color: #7cb518; color: white; font-size: 18px; font-weight: 500;")
        self.speed_input.setPlaceholderText("Enter %")
        self.speed_input_layout.addWidget(self.speed_input)
        # Connect the returnPressed signal to handle Enter key
        self.speed_input.returnPressed.connect(self.handle_input_speed)
        
        # Motor speed control
        self.speed_display_widget = QWidget()
        
        self.speed_layout = QVBoxLayout()
        self.speed_layout.setSpacing(10)
        motor_label = QLabel("Motor Control")
        motor_label.setFont(custom_font)
        motor_label.setAlignment(Qt.AlignTop)
        motor_label.setStyleSheet("font-size: 20px; color: black; font-weight: 500;")
        self.speed_display = QLabel("0%")

        self.speed_display.setFont(custom_font)
        self.speed_display.setFixedSize(200, 100)
        self.speed_display.setStyleSheet("color: #39FF14; font-size: 18px; font-weight: 500; border: 1px solid white; background-color: black;")
        
        self.stop_button = QPushButton("STOP")
        self.stop_button.setFixedSize(200, 100)
        self.stop_button.setFont(custom_font)
        self.stop_button.setStyleSheet("background-color: red; color: white; font-size: 24px; font-weight: 600;")
        self.stop_button.clicked.connect(self.stop_motor)

        self.speed_layout.addWidget(motor_label)
        self.speed_layout.addWidget(self.speed_display)
        self.speed_layout.addStretch()
        self.speed_layout.addWidget(self.stop_button)

        self.speed_display_widget.setLayout(self.speed_layout)

        self.bottom_layout.addWidget(self.speed_display_widget)

        self.bottom_layout.addLayout(self.speed_input_layout)

        # self.left_panel_layout.addWidget(self.logo_label)
        self.left_panel_layout.addStretch()

        self.left_panel_layout.addLayout(self.h_layout)
        self.left_panel_layout.addStretch()
        
        self.left_panel_layout.addWidget(self.bottom_layout_widget)

        # self.left_panel_layout.addWidget(self.speed_display_widget)
        self.layout.addWidget(self.left_panel_widget)

        # main widget
        self.main_widget = QWidget()
        self.main_widget.setStyleSheet(f"background-color: {main_bg};")
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)

        self.main_widget.setLayout(self.main_layout)
        
        # Real-time Plot Layout
        self.plot_layout = QVBoxLayout()
        self.plot_layout.setContentsMargins(10, 5, 0, 5)

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

        # Plot for thrust vs. throttle
        self.thrust_plot = pg.PlotWidget(title="Thrust vs Throttle")
        self.thrust_plot.setLabel('left', 'Thrust (g)')
        self.thrust_plot.setLabel('bottom', 'Throttle (%)')
        self.thrust_plot.addLegend()
        self.thrust_curve = self.thrust_plot.plot(pen='g', name="Thrust vs Throttle")

        # Enable dynamic Y-axis range for thrust_plot
        self.thrust_plot.enableAutoRange(axis=pg.ViewBox.YAxis, enable=True)

        self.plot_layout.addWidget(self.temp_plot)
        self.plot_layout.addWidget(self.current_plot)
        self.plot_layout.addWidget(self.thrust_plot)
        self.main_layout.addLayout(self.plot_layout)

        self.layout.addWidget(self.main_widget)

        self.showMaximized()

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_data)
        self.timer.start(100)  # Update every 100ms

    def refresh_ports(self):
        self.port_combo.clear()
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.port_combo.addItems(ports)

    def handle_input_speed(self):
        try:
            # Get the input value
            speed = int(self.speed_input.text())
            if 10 <= speed <= 100:
                self.set_motor_speed(speed)
                self.speed_input.clear()  # Clear the input after processing
                # Start the timer when the motor starts
                if not self.is_motor_running:
                    self.start_time = time.time()
                    self.is_motor_running = True
                    self.elapsed_time = 0  # Reset elapsed time
            else:
                print("Please enter a value between 10 and 100.")
        except ValueError:
            print("Invalid input. Please enter a number.")


    def connect_serial(self):
        if self.serial_port:
            self.serial_port.close()
            self.serial_port = None
            self.connect_button.setText("Connect")
            self.connect_button.setStyleSheet("background-color: green;")
            self.port_combo.setEnabled(True)
        else:
            try:
                port = self.port_combo.currentText()
                self.serial_port = serial.Serial(port, 57600, timeout=1)
                self.connect_button.setText("Disconnect")
                self.connect_button.setStyleSheet("background-color: red;")
                self.port_combo.setEnabled(False)
                print(f"Connected to {port}")
            except serial.SerialException as e:
                print(f"Error connecting to {port}: {e}")

    def set_motor_speed(self, value):
        if self.serial_port:
            command = f"{value}%\n"
            self.serial_port.write(command.encode())
            self.speed_display.setText(f"{(value)}%")



    def stop_motor(self):
        if self.serial_port:
            command = "S\n"
            self.serial_port.write(command.encode())
            self.speed_display.setText("0%")
            # Freeze the timer when the motor stops
            if self.is_motor_running:
                self.elapsed_time += time.time() - self.start_time
                self.is_motor_running = False

    def update_data(self):
        if self.serial_port and self.serial_port.in_waiting:
            try:
                line = self.serial_port.readline().decode('utf-8', errors='replace').strip()
                # print("line is read")
                self.parse_data(line)
                # print("parsing done")


            except Exception as e:
                print(f"Error reading data: {e}")
    
    def update_timer_display(self):
        # Only update the timer if the motor has been started
        if self.is_motor_running and self.start_time is not None:
            current_time = time.time()
            elapsed = current_time - self.start_time + self.elapsed_time
        else:
            # When the motor is stopped or hasn't started, use the saved elapsed time
            elapsed = self.elapsed_time

        # Convert the elapsed time to hours, minutes, seconds
        hours, rem = divmod(elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        self.timer_label.setText(f"{int(hours):02}:{int(minutes):02}:{int(seconds):02}")


    def parse_data(self, data):
        try:
            if data.startswith("Throttle:"):  # Note the colon here
                parts = data.split(",")
                if len(parts) >= 6:
                    # Parse each part using exact Arduino format
                    throttle = float(parts[0].split("Throttle:")[1].strip())
                    thrust = float(parts[1].split("Thrust:")[1].strip())
                    rpm = int(parts[2].split("RPM:")[1].strip())
                    current = float(parts[3].split("Current:")[1].strip())
                    ambient_temp = float(parts[4].split("AmbientTemp:")[1].strip())
                    object_temp = float(parts[5].split("ObjectTemp:")[1].strip())
                    
                    # Update displays with matching precision to Arduino output
                    self.throttle_display.setText(f"{throttle:.1f}")  # 1 decimal place
                    self.thrust_display.setText(f"{thrust:.1f}")      # 1 decimal place
                    self.current_display.setText(f"{current:.2f}")    # 2 decimal places
                    self.temp_display.setText(f"{object_temp:.1f}")   # 1 decimal place

                    # Calculate elapsed time
                    current_time = time.time() - self.start_time
                    self.time_data.append(current_time)

                    # Append data for plots (already converted to float above)
                    self.temp_data.append(object_temp)
                    self.current_data.append(current)
                    self.throttle_data.append(throttle)
                    self.thrust_data.append(thrust)

                    # Update plots
                    self.temp_curve.setData(self.time_data, self.temp_data)
                    self.current_curve.setData(self.time_data, self.current_data)
                    self.thrust_curve.setData(self.throttle_data, self.thrust_data)

                    # Dynamically adjust X-axis to scroll with time
                    if len(self.time_data) > 1:
                        self.temp_plot.setXRange(self.time_data[-1] - 10, self.time_data[-1], padding=0)
                        self.current_plot.setXRange(self.time_data[-1] - 10, self.time_data[-1], padding=0)

        except Exception as e:
            print(f"Error parsing data: {e}")
            # Optionally print the raw data for debugging
            # print(f"Raw data: {data}")

def main():
    app = QApplication(sys.argv)

    # login_dialog = LoginDialog()
    # if login_dialog.exec_() == QDialog.Accepted:
    gui = ThrustbenchGUI()
    gui.show()
    sys.exit(app.exec_())

    # else:
    #     sys.exit()


if __name__ == "__main__":
    main()
