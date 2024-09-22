import sys
import serial
import serial.tools.list_ports
import matplotlib.pyplot as plt
from PyQt5.QtGui import QPixmap 
from PyQt5.QtCore import Qt, QTimer
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QWidget, QPushButton, QLabel, QComboBox, QSizePolicy


class ThrustbenchGUI(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Thrustbench Control")
        self.setGeometry(100, 100, 800, 600)
        self.showMaximized()
        self.size

        self.serial_port = None
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setAlignment(Qt.AlignTop)
        self.layout.setSpacing(10)

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
        self.measurements_layout = QHBoxLayout()  # Main horizontal layout
        self.measurements_layout.setSpacing(30)  # Space between items
        self.measurements_layout.setAlignment(Qt.AlignCenter)
        # Function to create a measurement box with label

        def create_measurement_display(value, label_text):
            # Vertical layout for the box and its label
            vbox = QVBoxLayout()
            
            display = QLabel(value)
            display.setFixedSize(100, 100)  # Fixed size for the display box
            display.setStyleSheet("border: 1px solid #ccc; padding: 10px; font-size: 24px; font-weight: 600; text-align: center; background-color: #f0f0f0;")
            
            label = QLabel(label_text)
            label.setAlignment(Qt.AlignCenter)  # Center alignment
            label.setStyleSheet("font-size: 18px;")
            # label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)  # Allow label to expand horizontally
            
            vbox.addWidget(display)  # Add display box
            vbox.addWidget(label)  # Add label below the box
            vbox.setAlignment(Qt.AlignRight)  # Center align the vbox in the horizontal layout
            return vbox  # Return the vertical layout

        # Adding all measurement displays to the main layout
        self.measurements_layout.addLayout(create_measurement_display("0 g", "Thrust"))
        self.measurements_layout.addLayout(create_measurement_display("0", "RPM"))
        self.measurements_layout.addLayout(create_measurement_display("0 A", "Current"))
        self.measurements_layout.addLayout(create_measurement_display("0 °C", "Ambient Temp"))
        self.measurements_layout.addLayout(create_measurement_display("0 °C", "Object Temp"))

        self.layout.addLayout(self.measurements_layout)

        # Create plots
        self.plot_layout = QHBoxLayout()
        
        # Plot for Current vs Time
        self.current_plot = PlotCanvas(self, title="Current vs Time", xlabel="Time (s)", ylabel="Current (A)")
        self.plot_layout.addWidget(self.current_plot)
        
        # Plot for Thrust vs Throttle
        self.thrust_plot = PlotCanvas(self, title="Thrust vs Throttle", xlabel="Throttle (%)", ylabel="Thrust (g)")
        self.plot_layout.addWidget(self.thrust_plot)

        self.layout.addLayout(self.plot_layout)

        # Motor controls layout
        self.motor_control_layout = QHBoxLayout()
        self.motor_control_layout.setSpacing(20)  # Space between items

        # Left side: Motor controls
        controls_layout = QVBoxLayout()

        # Motor speed label
        self.speed_label = QLabel("Motor Speed: 0%")
        self.speed_label.setStyleSheet("border: 1px solid navyblue; font-size: 18px; font-weight: 500; padding: 20px;")
        self.speed_label.setAlignment(Qt.AlignCenter)
        controls_layout.addWidget(self.speed_label)

        # Motor speed buttons
        speed_button_layout = QHBoxLayout()
        for i in range(10):
            speed = (i + 1) * 10
            button = QPushButton(f"{speed}%")
            button.setFixedSize(80, 40)  # Fixed size for buttons
            button.setStyleSheet("background-color: #4CAF50; color: white; font-size: 18px; font-weight: bold; border-radius: 5px;")
            button.clicked.connect(lambda _, s=i: self.set_motor_speed(s))
            speed_button_layout.addWidget(button)

        controls_layout.addLayout(speed_button_layout)

        # Stop button
        self.stop_button = QPushButton("STOP")
        self.stop_button.setFixedSize(80, 80)  # Circle size for the stop button
        self.stop_button.setStyleSheet("background-color: red; color: white; font-weight: bold; font-size: 20px; border-radius: 40px;")  # Circular design
        self.stop_button.clicked.connect(self.stop_motor)
        controls_layout.addWidget(self.stop_button)

        self.motor_control_layout.addLayout(controls_layout)

        # Right side: Logo
        self.logo_label = QLabel()
        self.logo_label.setAlignment(Qt.AlignCenter)
        self.logo_pixmap = QPixmap("home_logo.png")  # Update with the path to your logo
        self.logo_label.setPixmap(self.logo_pixmap.scaled(400, 600, Qt.KeepAspectRatio))  # Adjust size as needed
        self.motor_control_layout.addWidget(self.logo_label)

        self.layout.addLayout(self.motor_control_layout)

    

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
            self.speed_label.setText(f"Motor Speed: {(value + 1) * 10}%")

    def stop_motor(self):
        if self.serial_port:
            command = "S\n"
            self.serial_port.write(command.encode())
            self.speed_label.setText("Motor Speed: 0%")

    def update_data(self):
        if self.serial_port and self.serial_port.in_waiting:
            try:
                line = self.serial_port.readline().decode('utf-8', errors='replace').strip()
                print(f"Raw Data: {line}")  # Debug print to check the data
                self.parse_data(line)
            except Exception as e:
                print(f"Error reading serial data: {e}")

    def parse_data(self, data):
        try:
            if "Throttle" in data:
                parts = data.split(",")
                rpm = int(parts[1].split(":")[1].strip())
                thrust = float(parts[3].split(":")[1].strip())
                current = float(parts[4].split(":")[1].strip())
                ambient_temp = float(parts[5].split(":")[1].strip())
                object_temp = float(parts[6].split(":")[1].strip())

                # Update GUI labels directly
                self.thrust_label.setText(f"{thrust:.2f} g")
                self.rpm_label.setText(f"{rpm}")
                self.current_label.setText(f"{current:.2f} A")
                self.ambient_temp_label.setText(f"{ambient_temp:.1f} °C")
                self.object_temp_label.setText(f"{object_temp:.1f} °C")

        except Exception as e:
            print(f"Error parsing data '{data}': {e}")


    def closeEvent(self, event):
        if self.serial_port:
            self.stop_motor()
            self.serial_port.close()
        event.accept()


class PlotCanvas(FigureCanvas):
    def __init__(self, parent=None, title='', xlabel='', ylabel=''):
        fig, self.ax = plt.subplots()
        super().__init__(fig)
        self.setParent(parent)
        self.ax.set_title(title)
        self.ax.set_xlabel(xlabel)
        self.ax.set_ylabel(ylabel)
        self.ax.grid(True)

        self.xdata = []
        self.ydata = []

    def update_plot(self, x, y):
        self.xdata.append(x)
        self.ydata.append(y)

        self.ax.clear()
        self.ax.plot(self.xdata, self.ydata)
        self.ax.set_title(self.ax.get_title())
        self.ax.set_xlabel(self.ax.get_xlabel())
        self.ax.set_ylabel(self.ax.get_ylabel())
        self.ax.grid(True)
        self.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ThrustbenchGUI()

    # Make the window non-resizable and maximized
    window.setFixedSize(800, 600)  # Set a fixed size if needed (adjust as per your design)
    window.showMaximized()  # Show the window maximized

    sys.exit(app.exec_())