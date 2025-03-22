import sys
import serial
import threading
import time
import serial.tools.list_ports
from PyQt5.QtWidgets import QApplication, QWidget, QLabel, QVBoxLayout, QPushButton, QComboBox, QMessageBox

class WeightDisplayApp(QWidget):
    def __init__(self):
        super().__init__()
        
        self.initUI()
        self.serial_thread = None
        self.serial_port = None

    def initUI(self):
        self.setWindowTitle('Weight Display')
        self.setGeometry(100, 100, 400, 300)

        self.layout = QVBoxLayout()
        self.help = QLabel("Select the com port 6 or 8")
        self.port_label = QLabel("Select COM Port:", self)
        self.layout.addWidget(self.help)
        self.layout.addWidget(self.port_label)

        # Create a combo box to select COM ports
        self.port_combobox = QComboBox(self)
        self.port_combobox.addItems(self.get_serial_ports())
        self.layout.addWidget(self.port_combobox)

        self.start_button = QPushButton("Start Reading Weight", self)
        self.start_button.clicked.connect(self.start_reading)
        self.layout.addWidget(self.start_button)

        self.weight_label = QLabel("Weight: ", self)
        self.weight_label.setStyleSheet("font-size: 24px;")
        self.layout.addWidget(self.weight_label)

        self.weight_value = QLabel("0.00 g", self)
        self.weight_value.setStyleSheet("font-size: 24px;")
        self.layout.addWidget(self.weight_value)

        self.setLayout(self.layout)

    def get_serial_ports(self):
        """ Get a list of available COM ports """
        ports = serial.tools.list_ports.comports()
        return [port.device for port in ports]

    def start_reading(self):
        if self.serial_thread is None:
            selected_port = self.port_combobox.currentText()
            if selected_port:
                self.serial_port = selected_port
                self.serial_thread = threading.Thread(target=self.read_serial, daemon=True)
                self.serial_thread.start()
            else:
                QMessageBox.warning(self, "Warning", "Please select a COM port.")

    def read_serial(self):
        """ Read weight data from the selected serial port """
        with serial.Serial(self.serial_port, 9600, timeout=1) as ser:
            while True:
                try:
                    line = ser.readline().decode('utf-8').rstrip()
                    if line:  # Check if the line is not empty
                        self.weight_value.setText(f"{line} g")  # Update weight display
                except Exception as e:
                    print(f"Error: {e}")

def main():
    app = QApplication(sys.argv)
    ex = WeightDisplayApp()
    ex.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
