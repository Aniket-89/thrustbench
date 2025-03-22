import sys
import serial
import time
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                           QHBoxLayout, QLabel, QLineEdit, QPushButton, 
                           QComboBox, QGroupBox, QGridLayout, QMessageBox)
from PyQt5.QtCore import Qt, QTimer

class StatorWinderDashboard(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Stator Winding Machine Control")
        self.setGeometry(100, 100, 800, 600)
        
        # Initialize serial connection
        try:
            self.serial = serial.Serial('COM3', 115200, timeout=1)
            time.sleep(2)  # Wait for Arduino to reset
        except:
            self.serial = None
            QMessageBox.warning(self, "Connection Error", 
                              "Could not connect to Arduino. Check connection and port.")
        
        self.initUI()
        
    def initUI(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # Parameters Group
        params_group = QGroupBox("Machine Parameters")
        params_layout = QGridLayout()
        
        # Motor 1 (Winding) Parameters
        self.wind_speed = self.addParameterField(params_layout, 0, "Winding Speed (steps/s):", "1000")
        self.wind_steps = self.addParameterField(params_layout, 1, "Winding Steps/Rev:", "200")
        self.gear_ratio = self.addParameterField(params_layout, 2, "Gear Ratio:", "2.5")
        
        # Motor 2 (Feed) Parameters
        self.feed_speed = self.addParameterField(params_layout, 3, "Feed Speed (steps/s):", "500")
        self.feed_steps = self.addParameterField(params_layout, 4, "Feed Steps/Rev:", "200")
        self.slot_length = self.addParameterField(params_layout, 5, "Slot Length (mm):", "50")
        
        # Motor 3 (Rotation) Parameters
        self.rot_speed = self.addParameterField(params_layout, 6, "Rotation Speed (steps/s):", "200")
        self.rot_steps = self.addParameterField(params_layout, 7, "Rotation Steps/Rev:", "200")
        
        # General Parameters
        self.coils_per_slot = self.addParameterField(params_layout, 8, "Coils per Slot:", "100")
        
        # Winding Direction
        direction_layout = QHBoxLayout()
        direction_label = QLabel("Winding Direction:")
        self.wind_direction = QComboBox()
        self.wind_direction.addItems(["Clockwise", "Counter-Clockwise"])
        direction_layout.addWidget(direction_label)
        direction_layout.addWidget(self.wind_direction)
        params_layout.addLayout(direction_layout, 9, 0, 1, 2)
        
        params_group.setLayout(params_layout)
        main_layout.addWidget(params_group)
        
        # Control Buttons
        buttons_layout = QHBoxLayout()
        
        self.update_btn = QPushButton("Update Parameters")
        self.update_btn.clicked.connect(self.updateParameters)
        
        self.home_btn = QPushButton("Home All")
        self.home_btn.clicked.connect(self.homeAll)
        
        self.start_btn = QPushButton("Start Winding")
        self.start_btn.clicked.connect(self.startWinding)
        
        self.stop_btn = QPushButton("Emergency Stop")
        self.stop_btn.setStyleSheet("background-color: red; color: white;")
        self.stop_btn.clicked.connect(self.emergencyStop)
        
        buttons_layout.addWidget(self.update_btn)
        buttons_layout.addWidget(self.home_btn)
        buttons_layout.addWidget(self.start_btn)
        buttons_layout.addWidget(self.stop_btn)
        
        main_layout.addLayout(buttons_layout)
        
        # Status Bar
        self.statusBar().showMessage('Ready')
        
    def addParameterField(self, layout, row, label_text, default_value):
        label = QLabel(label_text)
        field = QLineEdit(default_value)
        layout.addWidget(label, row, 0)
        layout.addWidget(field, row, 1)
        return field
        
    def updateParameters(self):
        if not self.serial:
            QMessageBox.warning(self, "Error", "No connection to Arduino")
            return
            
        try:
            # Format: P,windSpeed,feedSpeed,rotSpeed,windSteps,feedSteps,rotSteps,
            #          gearRatio,windDir,coilsPerSlot,slotLength\n
            params = f"P,{self.wind_speed.text()},{self.feed_speed.text()},"
            params += f"{self.rot_speed.text()},{self.wind_steps.text()},"
            params += f"{self.feed_steps.text()},{self.rot_steps.text()},"
            params += f"{self.gear_ratio.text()},"
            params += f"{1 if self.wind_direction.currentText() == 'Clockwise' else 0},"
            params += f"{self.coils_per_slot.text()},{self.slot_length.text()}\n"
            
            self.serial.write(params.encode())
            self.statusBar().showMessage('Parameters updated successfully')
            
        except Exception as e:
            QMessageBox.warning(self, "Error", f"Failed to update parameters: {str(e)}")
    
    def homeAll(self):
        if self.serial:
            self.serial.write(b'H\n')
            self.statusBar().showMessage('Homing sequence initiated')
            
    def startWinding(self):
        if self.serial:
            self.serial.write(b'S\n')
            self.statusBar().showMessage('Winding sequence started')
            
    def emergencyStop(self):
        if self.serial:
            self.serial.write(b'E\n')
            self.statusBar().showMessage('EMERGENCY STOP ACTIVATED')
            
    def closeEvent(self, event):
        if self.serial:
            self.serial.close()
        event.accept()

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = StatorWinderDashboard()
    window.show()
    sys.exit(app.exec_())